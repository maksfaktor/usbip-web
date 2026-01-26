"""
================================================================================
Avahi (mDNS) Service Discovery Utilities
================================================================================

File: avahi_utils.py
Project: Orange USB/IP Web Interface
Purpose: Discover other Orange USB/IP instances on the local network using Avahi

Features:
    - Discover _orangeusbip._tcp services via mDNS
    - Multiple discovery methods (avahi-browse CLI, zeroconf library)
    - Self-detection to mark local instance
    - Configurable scan timeout (default: 5 seconds)

Service Type:
    _orangeusbip._tcp.local

TXT Records:
    - version: Software version
    - usbip_port: USB/IP daemon port (3240)
    - fido_port: Virtual FIDO port (3241)
    - hostname: System hostname

Usage:
    from avahi_utils import discover_services, is_avahi_available
    
    if is_avahi_available():
        services = discover_services(timeout=5)
        for svc in services:
            print(f"{svc['name']} at {svc['ip']}:{svc['web_port']}")

Dependencies:
    - avahi-utils package (avahi-browse command)
    - Optional: zeroconf Python library for fallback
================================================================================
"""

import subprocess
import socket
import logging
import time
import re
import os
from typing import List, Dict, Optional

logger = logging.getLogger(__name__)

SERVICE_TYPE = "_orangeusbip._tcp"
DEFAULT_TIMEOUT = 5
DEFAULT_WEB_PORT = 5000
DEFAULT_USBIP_PORT = 3240
DEFAULT_FIDO_PORT = 3241


def get_local_ips() -> List[str]:
    """Get list of local IP addresses for self-detection."""
    local_ips = ['127.0.0.1', 'localhost']
    try:
        hostname = socket.gethostname()
        local_ips.append(hostname)
        local_ips.append(hostname + '.local')
        
        for info in socket.getaddrinfo(hostname, None, socket.AF_INET):
            ip = info[4][0]
            if ip not in local_ips:
                local_ips.append(ip)
    except Exception as e:
        logger.debug(f"Error getting local IPs: {e}")
    
    try:
        import netifaces
        for iface in netifaces.interfaces():
            addrs = netifaces.ifaddresses(iface)
            if netifaces.AF_INET in addrs:
                for addr in addrs[netifaces.AF_INET]:
                    ip = addr.get('addr')
                    if ip and ip not in local_ips:
                        local_ips.append(ip)
    except ImportError:
        pass
    except Exception as e:
        logger.debug(f"Error with netifaces: {e}")
    
    try:
        result = subprocess.run(
            ['hostname', '-I'],
            capture_output=True,
            text=True,
            timeout=2
        )
        if result.returncode == 0:
            for ip in result.stdout.strip().split():
                if ip and ip not in local_ips:
                    local_ips.append(ip)
    except Exception as e:
        logger.debug(f"Error getting IPs via hostname -I: {e}")
    
    return local_ips


def is_avahi_available() -> bool:
    """Check if Avahi daemon is running and avahi-browse is available."""
    try:
        result = subprocess.run(
            ['which', 'avahi-browse'],
            capture_output=True,
            timeout=2
        )
        if result.returncode != 0:
            logger.debug("avahi-browse not found")
            return False
        
        result = subprocess.run(
            ['systemctl', 'is-active', 'avahi-daemon'],
            capture_output=True,
            text=True,
            timeout=5
        )
        if result.returncode == 0 and 'active' in result.stdout:
            return True
        
        result = subprocess.run(
            ['pgrep', '-x', 'avahi-daemon'],
            capture_output=True,
            timeout=2
        )
        return result.returncode == 0
        
    except Exception as e:
        logger.debug(f"Error checking Avahi availability: {e}")
        return False


def parse_txt_record(txt_str: str) -> Dict[str, str]:
    """Parse TXT record string into dictionary."""
    txt_records = {}
    if not txt_str:
        return txt_records
    
    txt_str = txt_str.strip('"\'')
    
    for item in txt_str.split():
        item = item.strip('"\'')
        if '=' in item:
            key, value = item.split('=', 1)
            txt_records[key] = value
    
    return txt_records


def discover_via_avahi_browse(timeout: int = DEFAULT_TIMEOUT) -> List[Dict]:
    """Discover services using avahi-browse command."""
    services = []
    local_ips = get_local_ips()
    
    try:
        result = subprocess.run(
            [
                'avahi-browse',
                '-r',
                '-t',
                '-p',
                SERVICE_TYPE
            ],
            capture_output=True,
            text=True,
            timeout=timeout + 2
        )
        
        if result.returncode != 0 and not result.stdout:
            logger.debug(f"avahi-browse returned no results: {result.stderr}")
            return services
        
        current_service = {}
        
        for line in result.stdout.strip().split('\n'):
            if not line or line.startswith('+'):
                continue
            
            if line.startswith('='):
                parts = line.split(';')
                if len(parts) >= 10:
                    interface = parts[1]
                    protocol = parts[2]
                    name = parts[3]
                    svc_type = parts[4]
                    domain = parts[5]
                    hostname = parts[6]
                    ip = parts[7]
                    port = parts[8]
                    txt = ';'.join(parts[9:]) if len(parts) > 9 else ''
                    
                    txt_records = parse_txt_record(txt)
                    
                    is_self = ip in local_ips or hostname.rstrip('.') in local_ips
                    
                    service = {
                        'name': name,
                        'hostname': hostname.rstrip('.'),
                        'ip': ip,
                        'web_port': int(port) if port.isdigit() else DEFAULT_WEB_PORT,
                        'usbip_port': int(txt_records.get('usbip_port', DEFAULT_USBIP_PORT)),
                        'fido_port': int(txt_records.get('fido_port', DEFAULT_FIDO_PORT)),
                        'version': txt_records.get('version', 'unknown'),
                        'is_self': is_self
                    }
                    
                    existing = next((s for s in services if s['ip'] == ip), None)
                    if not existing:
                        services.append(service)
                        logger.debug(f"Discovered service: {name} at {ip}:{port}")
        
    except subprocess.TimeoutExpired:
        logger.warning(f"avahi-browse timed out after {timeout} seconds")
    except FileNotFoundError:
        logger.warning("avahi-browse command not found")
    except Exception as e:
        logger.error(f"Error running avahi-browse: {e}")
    
    return services


def discover_via_zeroconf(timeout: int = DEFAULT_TIMEOUT) -> List[Dict]:
    """Discover services using zeroconf Python library (fallback method)."""
    services = []
    local_ips = get_local_ips()
    
    try:
        from zeroconf import ServiceBrowser, Zeroconf, ServiceStateChange
        
        discovered = []
        
        def on_service_state_change(zeroconf, service_type, name, state_change):
            if state_change == ServiceStateChange.Added:
                info = zeroconf.get_service_info(service_type, name)
                if info:
                    discovered.append(info)
        
        zc = Zeroconf()
        browser = ServiceBrowser(zc, f"{SERVICE_TYPE}.local.", handlers=[on_service_state_change])
        
        time.sleep(timeout)
        
        for info in discovered:
            if info.addresses:
                ip = socket.inet_ntoa(info.addresses[0])
                hostname = info.server.rstrip('.')
                
                txt_records = {}
                if info.properties:
                    for key, value in info.properties.items():
                        if isinstance(key, bytes):
                            key = key.decode('utf-8')
                        if isinstance(value, bytes):
                            value = value.decode('utf-8')
                        txt_records[key] = value
                
                is_self = ip in local_ips or hostname in local_ips
                
                service = {
                    'name': info.name.replace(f'.{SERVICE_TYPE}.local.', ''),
                    'hostname': hostname,
                    'ip': ip,
                    'web_port': info.port,
                    'usbip_port': int(txt_records.get('usbip_port', DEFAULT_USBIP_PORT)),
                    'fido_port': int(txt_records.get('fido_port', DEFAULT_FIDO_PORT)),
                    'version': txt_records.get('version', 'unknown'),
                    'is_self': is_self
                }
                services.append(service)
        
        browser.cancel()
        zc.close()
        
    except ImportError:
        logger.debug("zeroconf library not available")
    except Exception as e:
        logger.error(f"Error with zeroconf discovery: {e}")
    
    return services


def discover_services(timeout: int = None) -> Dict:
    """
    Discover Orange USB/IP services on the local network.
    
    Args:
        timeout: Scan timeout in seconds (default: 5)
    
    Returns:
        Dict with:
            - success: bool
            - services: List of discovered services
            - scan_time: Time taken to scan
            - method: Discovery method used
            - error: Error message if failed
    """
    if timeout is None:
        timeout = int(os.environ.get('AVAHI_SCAN_TIMEOUT', DEFAULT_TIMEOUT))
    
    start_time = time.time()
    services = []
    method = None
    error = None
    
    if is_avahi_available():
        method = 'avahi-browse'
        services = discover_via_avahi_browse(timeout)
        logger.info(f"Avahi discovery found {len(services)} services")
    else:
        method = 'zeroconf'
        services = discover_via_zeroconf(timeout)
        if not services:
            method = 'unavailable'
            error = "Avahi daemon not running. Install avahi-daemon package and start the service."
            logger.warning("Neither avahi-browse nor zeroconf available")
    
    scan_time = round(time.time() - start_time, 2)
    
    services.sort(key=lambda x: (x.get('is_self', False), x.get('name', '')))
    
    return {
        'success': error is None,
        'services': services,
        'scan_time': scan_time,
        'method': method,
        'error': error
    }


def get_local_service_info() -> Dict:
    """Get information about local Orange USB/IP service."""
    try:
        hostname = socket.gethostname()
        local_ips = get_local_ips()
        primary_ip = next((ip for ip in local_ips if ip not in ['127.0.0.1', 'localhost']), '127.0.0.1')
        
        return {
            'name': f'OrangeUSB on {hostname}',
            'hostname': hostname,
            'ip': primary_ip,
            'web_port': DEFAULT_WEB_PORT,
            'usbip_port': DEFAULT_USBIP_PORT,
            'fido_port': DEFAULT_FIDO_PORT,
            'version': '1.0',
            'is_self': True
        }
    except Exception as e:
        logger.error(f"Error getting local service info: {e}")
        return None


if __name__ == '__main__':
    logging.basicConfig(level=logging.DEBUG)
    
    print("Checking Avahi availability...")
    print(f"Avahi available: {is_avahi_available()}")
    
    print("\nLocal service info:")
    local_info = get_local_service_info()
    if local_info:
        for key, value in local_info.items():
            print(f"  {key}: {value}")
    
    print("\nDiscovering services...")
    result = discover_services(timeout=5)
    
    print(f"\nScan completed in {result['scan_time']}s using {result['method']}")
    
    if result['success']:
        print(f"Found {len(result['services'])} services:")
        for svc in result['services']:
            marker = " (THIS DEVICE)" if svc.get('is_self') else ""
            print(f"  - {svc['name']}{marker}")
            print(f"    IP: {svc['ip']}, Web: {svc['web_port']}, USB/IP: {svc['usbip_port']}, FIDO: {svc['fido_port']}")
    else:
        print(f"Error: {result.get('error')}")
