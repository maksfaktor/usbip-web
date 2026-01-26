# Avahi (mDNS) Service Discovery Implementation Plan

## Overview

This document outlines the implementation plan for adding Avahi-based automatic network discovery to the Orange USB/IP Web Interface. The feature will allow the `/remote` page to automatically find other Orange USB/IP instances on the local network.

## What is Avahi?

Avahi is a system daemon that implements mDNS/DNS-SD (multicast DNS / DNS-based Service Discovery) - the same technology used by Apple's Bonjour. It allows devices to:
- Announce services they provide
- Discover services offered by other devices
- Work without a central DNS server (zero-configuration networking)

## Architecture

```
┌─────────────────────────────────────────────────────────────────────┐
│                    Orange USB/IP Instance A                          │
│  ┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐  │
│  │   Flask App     │    │  Avahi Daemon   │    │   USB/IP        │  │
│  │   Port 5000     │◄──►│  (mDNS)         │    │   Port 3240     │  │
│  └─────────────────┘    └────────┬────────┘    └─────────────────┘  │
│                                  │ Publishes:                        │
│                                  │ _orangeusbip._tcp.local           │
└──────────────────────────────────┼──────────────────────────────────┘
                                   │
                    ═══════════════╪═══════════════  Local Network
                                   │
┌──────────────────────────────────┼──────────────────────────────────┐
│                    Orange USB/IP Instance B                          │
│  ┌─────────────────┐    ┌────────┴────────┐    ┌─────────────────┐  │
│  │   Flask App     │    │  Avahi Daemon   │    │   USB/IP        │  │
│  │   Port 5000     │◄──►│  (mDNS)         │    │   Port 3240     │  │
│  └─────────────────┘    └─────────────────┘    └─────────────────┘  │
│                                  │ Publishes:                        │
│                                  │ _orangeusbip._tcp.local           │
└─────────────────────────────────────────────────────────────────────┘
```

## Service Definition

### Service Type
```
_orangeusbip._tcp.local
```

### Service Name Format
```
OrangeUSB on <hostname>
```

### TXT Record Data
```
version=1.0
port=5000
usbip_port=3240
fido_port=3241
hostname=<system_hostname>
```

## Implementation Components

### 1. Server-Side Components

#### 1.1 Avahi Service File
**File**: `/etc/avahi/services/orangeusbip.service`

This XML file registers the Orange USB/IP service with Avahi daemon:
```xml
<?xml version="1.0" standalone='no'?>
<!DOCTYPE service-group SYSTEM "avahi-service.dtd">
<service-group>
  <name replace-wildcards="yes">OrangeUSB on %h</name>
  <service>
    <type>_orangeusbip._tcp</type>
    <port>5000</port>
    <txt-record>version=1.0</txt-record>
    <txt-record>usbip_port=3240</txt-record>
    <txt-record>fido_port=3241</txt-record>
  </service>
</service-group>
```

#### 1.2 Python Discovery Module
**File**: `avahi_utils.py`

New Python module for Avahi interaction:

```python
Functions:
- discover_services() -> List[Dict]
  Discovers all _orangeusbip._tcp services on the network
  Returns: [{hostname, ip, port, txt_records}, ...]

- is_avahi_available() -> bool
  Checks if Avahi daemon is running and available

- get_service_info() -> Dict
  Returns information about local service registration
```

**Discovery Methods** (in order of preference):
1. **dbus-python** - Direct D-Bus communication with Avahi (most reliable)
2. **avahi-browse CLI** - Command-line tool parsing (fallback)
3. **zeroconf Python library** - Pure Python implementation (cross-platform fallback)

#### 1.3 Flask API Endpoint
**File**: `app.py`

New endpoint for AJAX discovery requests:

```
GET /api/discover-services

Response:
{
  "success": true,
  "services": [
    {
      "name": "OrangeUSB on orangepi-1",
      "hostname": "orangepi-1.local",
      "ip": "192.168.1.100",
      "web_port": 5000,
      "usbip_port": 3240,
      "fido_port": 3241,
      "version": "1.0",
      "is_self": false
    }
  ],
  "scan_time": 3.5,
  "method": "dbus"
}
```

### 2. Frontend Components

#### 2.1 Discovery UI Section
**File**: `templates/remote.html`

Add new card section for discovered services:

```
┌─────────────────────────────────────────────────────────────────┐
│  Network Discovery                                    [🔍 Scan] │
├─────────────────────────────────────────────────────────────────┤
│  ○ Auto-scan on page load                                       │
│                                                                 │
│  ┌─────────────────────────────────────────────────────────────┐│
│  │ 🟢 OrangeUSB on orangepi-1                                  ││
│  │    IP: 192.168.1.100 | Web: 5000 | USB/IP: 3240             ││
│  │    [Connect] [Open Web UI]                                  ││
│  └─────────────────────────────────────────────────────────────┘│
│  ┌─────────────────────────────────────────────────────────────┐│
│  │ 🟢 OrangeUSB on orangepi-2                                  ││
│  │    IP: 192.168.1.101 | Web: 5000 | USB/IP: 3240             ││
│  │    [Connect] [Open Web UI]                                  ││
│  └─────────────────────────────────────────────────────────────┘│
│                                                                 │
│  Last scan: 2 seconds ago | Found: 2 services                  │
└─────────────────────────────────────────────────────────────────┘
```

#### 2.2 JavaScript Functions
```javascript
- scanNetwork() - Triggers network discovery via API
- displayDiscoveredServices(services) - Renders service cards
- connectToService(ip) - Fills IP field and triggers connection
- toggleAutoScan() - Enables/disables auto-scan on page load
```

### 3. Installation Script Updates

#### 3.1 install_debian.sh Updates
Add Avahi setup to installation:

```bash
# Install Avahi daemon and tools
apt-get install -y avahi-daemon avahi-utils

# Enable and start Avahi service
systemctl enable avahi-daemon
systemctl start avahi-daemon

# Copy service definition file
cp orangeusbip.service /etc/avahi/services/

# Restart Avahi to pick up new service
systemctl restart avahi-daemon
```

#### 3.2 uninstall.sh Updates
Add Avahi cleanup:

```bash
# Remove Avahi service file
rm -f /etc/avahi/services/orangeusbip.service

# Restart Avahi (don't disable - other services may use it)
systemctl restart avahi-daemon
```

### 4. Dependencies

#### 4.1 System Packages
```
avahi-daemon      - mDNS/DNS-SD daemon
avahi-utils       - Command-line tools (avahi-browse)
libavahi-client3  - Client library
```

#### 4.2 Python Packages (optional, for enhanced functionality)
```
zeroconf>=0.80.0  - Pure Python mDNS implementation (fallback)
```

## Implementation Phases

### Phase 1: Core Discovery (Backend)
1. Create `avahi_utils.py` with discovery functions
2. Implement `avahi-browse` CLI parsing (works without extra Python deps)
3. Add `/api/discover-services` endpoint to `app.py`
4. Create Avahi service definition file template

### Phase 2: Frontend Integration
1. Update `templates/remote.html` with discovery UI
2. Add JavaScript for scan button and auto-scan
3. Implement service card rendering
4. Add "Connect" functionality to populate IP field

### Phase 3: Installation Integration
1. Update `install_debian.sh` to install and configure Avahi
2. Update `uninstall.sh` to clean up Avahi service
3. Add Avahi checks to `doctor.sh` diagnostic tool

### Phase 4: Testing & Polish
1. Test discovery between multiple instances
2. Handle edge cases (no services found, timeout, etc.)
3. Add loading indicators and error messages
4. Ensure UI matches existing dark theme

## Technical Considerations

### Discovery Timeout
- Default scan timeout: 3 seconds
- Configurable via environment variable: `AVAHI_SCAN_TIMEOUT`
- Progressive UI feedback during scan

### Self-Exclusion
- Detected services are compared against local IPs
- Local instance marked with `is_self: true` or filtered out

### Network Segmentation
- mDNS works within local broadcast domain only
- VLANs/subnets require mDNS reflector or alternative discovery

### Fallback Behavior
- If Avahi unavailable, show warning message
- Manual IP entry always available
- Graceful degradation on systems without Avahi

### Security Considerations
- Service discovery is passive (listening only)
- No authentication data transmitted via mDNS
- TXT records contain only version and port info
- Actual USB/IP connections still require proper authentication

## File Changes Summary

| File | Action | Description |
|------|--------|-------------|
| `avahi_utils.py` | Create | New module for Avahi discovery |
| `app.py` | Modify | Add /api/discover-services endpoint |
| `templates/remote.html` | Modify | Add discovery UI section |
| `static/js/app.js` | Modify | Add discovery JavaScript functions |
| `install_debian.sh` | Modify | Add Avahi installation |
| `uninstall.sh` | Modify | Add Avahi cleanup |
| `doctor.sh` | Modify | Add Avahi diagnostic checks |
| `orangeusbip.service` | Create | Avahi service definition (template) |

## User Interface Flow

### Automatic Discovery (on page load)
1. Page loads → Check if auto-scan enabled (localStorage)
2. If enabled → Show "Scanning network..." indicator
3. Call `/api/discover-services` API
4. Display found services in cards
5. User can click "Connect" to use any discovered server

### Manual Discovery (button click)
1. User clicks "Scan Network" button
2. Button shows spinner, "Scanning..."
3. Call `/api/discover-services` API
4. Display results or "No services found" message
5. Results persist until next scan or page reload

## Success Criteria

1. ✅ Orange USB/IP instances automatically register with Avahi on startup
2. ✅ `/remote` page can discover other instances on the network
3. ✅ Both auto-scan and manual scan options available
4. ✅ Discovered services show hostname, IP, and ports
5. ✅ "Connect" button pre-fills IP and triggers connection
6. ✅ Works on Debian/Ubuntu systems with Avahi installed
7. ✅ Graceful fallback when Avahi is unavailable
8. ✅ UI matches existing dark theme design

## Questions for Discussion

1. **Auto-scan default**: Should auto-scan be enabled by default, or require user opt-in?
   - Recommendation: Disabled by default (user enables via toggle)

2. **Scan timeout**: Is 3 seconds appropriate, or should it be longer/shorter?
   - Recommendation: 3 seconds default, configurable

3. **Service filtering**: Should we show the local instance in results (marked as "This device")?
   - Recommendation: Show but mark as "This device", don't allow self-connection

4. **Cache duration**: Should we cache discovery results, and for how long?
   - Recommendation: No cache, always fresh scan (mDNS is fast)

5. **Port display**: Show all ports (Web, USB/IP, FIDO) or just essential ones?
   - Recommendation: Show all in expandable details

---

*This plan is ready for review. After approval, implementation will proceed in the phases described above.*
