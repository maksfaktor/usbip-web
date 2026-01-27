# Avahi (mDNS) Service Discovery - Implementation Status

## Current Status: PARTIALLY IMPLEMENTED

**Last Updated**: January 27, 2026

---

## Implementation Summary

This document tracks the implementation status of Avahi-based automatic network discovery for the Orange USB/IP Web Interface. The feature allows the `/remote` page to automatically find other Orange USB/IP instances on the local network.

---

## What is Avahi?

Avahi is a system daemon that implements mDNS/DNS-SD (multicast DNS / DNS-based Service Discovery) - the same technology used by Apple's Bonjour. It allows devices to:
- Announce services they provide
- Discover services offered by other devices
- Work without a central DNS server (zero-configuration networking)

---

## Implementation Status by Component

### ✅ COMPLETED Components

| Component | File | Status | Notes |
|-----------|------|--------|-------|
| Python Discovery Module | `avahi_utils.py` | ✅ Complete | Uses `avahi-browse` CLI parsing |
| API Endpoint - Discovery | `/api/discover-services` | ✅ Complete | Returns discovered services |
| API Endpoint - Status | `/api/avahi-status` | ✅ Complete | Returns Avahi daemon status |
| Remote Page UI | `templates/remote.html` | ✅ Complete | Network Discovery section added |
| Auto-scan toggle | Remote page | ✅ Complete | Enabled by default, toggle to disable |
| Manual scan button | Remote page | ✅ Complete | "Scan Network" button |
| Service cards | Remote page | ✅ Complete | Shows hostname, IP, ports |
| "This Device" badge | Remote page | ✅ Complete | Marks local instance |
| "Connect" button | Remote page | ✅ Complete | Populates IP and connects |
| "Open UI" link | Remote page | ✅ Complete | Opens remote instance web interface |
| Avahi service file template | `orangeusbip.service.avahi` | ✅ Complete | Service definition for registration |
| Install script update | `install_debian.sh` | ✅ Complete | Installs avahi-daemon, avahi-utils, registers service |
| Uninstall script update | `uninstall.sh` | ✅ Complete | Removes Avahi service configuration |
| Diagnostic tool update | `doctor.sh` | ✅ Complete | Avahi status checks added |

### ⚠️ NEEDS TESTING Components

| Component | Status | Testing Required |
|-----------|--------|------------------|
| Multi-instance discovery | ⚠️ Not tested | Need 2+ Orange USB/IP instances on same network |
| Cross-subnet discovery | ⚠️ Not tested | Requires mDNS reflector for VLANs |
| Service registration on boot | ⚠️ Not tested | Verify Avahi picks up service after system restart |
| Firewall compatibility | ⚠️ Not tested | May need port 5353/UDP open for mDNS |
| Orange Pi hardware | ⚠️ Not tested | Test on actual Orange Pi device |

### ❌ KNOWN LIMITATIONS

| Limitation | Description | Workaround |
|------------|-------------|------------|
| Replit environment | Avahi daemon not available | Use manual IP entry |
| Windows compatibility | Avahi not native on Windows | Use Bonjour for Windows or manual entry |
| Docker containers | Requires host network mode | Configure Docker with `--network=host` |

---

## Virtual Device Integration Status

### ✅ COMPLETED Features

| Feature | Status | Notes |
|---------|--------|-------|
| USB Mass Storage Device (Go) | ✅ Complete | Full SCSI command emulation, BBB protocol |
| Device Registry API | ✅ Complete | HTTP API on port 3242 |
| Flask endpoints | ✅ Complete | `/publish_virtual_device`, `/unpublish_virtual_device` |
| Database migration | ✅ Complete | `is_published`, `usbip_busid` columns |
| Virtual Devices page | ✅ Complete | Publish/Unpublish buttons, status display |
| Remote page integration | ✅ Complete | Virtual devices shown with "Virtual" badge |
| Local device detection | ✅ Complete | Detects local machine by hostname/IP |
| Graceful error handling | ✅ Complete | Works without USB/IP tools |

### ⚠️ NEEDS TESTING Features

| Feature | Status | Testing Required |
|---------|--------|------------------|
| USB/IP protocol (virtual-fido) | ⚠️ Not tested | Test `usbip list -r localhost -p 3241` on Linux |
| Virtual device attach | ⚠️ Not tested | Test `usbip attach -r <ip> -b <busid>` |
| FIDO2 device functionality | ⚠️ Not tested | Test WebAuthn authentication with virtual FIDO2 key |
| Mass Storage read/write | ⚠️ Not tested | Mount attached virtual storage and test I/O |
| Multi-device registration | ⚠️ Not tested | Register multiple virtual devices simultaneously |

### ❌ NOT IMPLEMENTED Features

| Feature | Status | Description |
|---------|--------|-------------|
| virtual-fido Go service | ❌ Not running | Go service needs compilation and startup |
| Device API server (port 3242) | ❌ Not running | Part of virtual-fido Go service |
| Real USB/IP daemon | ❌ Not available | Requires Linux kernel modules |

---

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

## Port Configuration

| Port | Service | Protocol | Description |
|------|---------|----------|-------------|
| 5000 | Flask Web UI | HTTP | Main web interface |
| 3240 | USB/IP daemon (usbipd) | USB/IP | Real USB devices |
| 3241 | virtual-fido | USB/IP | Virtual USB devices |
| 3242 | Device API | HTTP/JSON | Virtual device management |
| 5353 | Avahi (mDNS) | UDP | Service discovery |

---

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

---

## Testing Checklist

### Basic Functionality Testing (Single Instance)

- [ ] Install on Debian/Ubuntu with `install_debian.sh`
- [ ] Verify Avahi daemon is running: `systemctl status avahi-daemon`
- [ ] Verify service registered: `avahi-browse -a | grep orangeusbip`
- [ ] Open Remote page and click "Scan Network"
- [ ] Verify local instance appears with "This Device" badge

### Multi-Instance Testing (2+ Instances Required)

- [ ] Install Orange USB/IP on two devices on same network
- [ ] Open Remote page on Instance A
- [ ] Verify Instance B appears in discovered services
- [ ] Click "Connect" button on Instance B
- [ ] Verify devices from Instance B are listed

### Virtual Device Testing (Linux with kernel modules)

- [ ] Create virtual storage device in web UI
- [ ] Click "Publish" on virtual device
- [ ] Run: `usbip list -r localhost -p 3241`
- [ ] Verify virtual device appears in list
- [ ] Run: `usbip attach -r localhost -b <busid> -p 3241`
- [ ] Verify device appears in `lsusb` output
- [ ] Mount and test read/write operations

### Error Handling Testing

- [ ] Test Remote page without Avahi installed (should show warning)
- [ ] Test Remote page with Avahi but no other instances (should show "No services found")
- [ ] Test Virtual Devices page without USB/IP tools (should work with database)

---

## Files Modified/Created

| File | Action | Description |
|------|--------|-------------|
| `avahi_utils.py` | Created | Python module for Avahi discovery |
| `app.py` | Modified | Added `/api/discover-services`, `/api/avahi-status` endpoints |
| `templates/remote.html` | Modified | Added Network Discovery UI section |
| `install_debian.sh` | Modified | Added Avahi installation and service registration |
| `uninstall.sh` | Modified | Added Avahi service cleanup |
| `doctor.sh` | Modified | Added Avahi diagnostic checks |
| `orangeusbip.service.avahi` | Created | Avahi service definition template |

---

## Environment Variables

| Variable | Default | Description |
|----------|---------|-------------|
| `AVAHI_SCAN_TIMEOUT` | 5 | Network scan timeout in seconds |

---

## Known Issues

1. **Replit Environment**: USB/IP tools and Avahi daemon are not available in the Replit development environment. All USB/IP and Avahi functionality requires deployment on a real Linux system.

2. **virtual-fido Service**: The Go-based virtual-fido service is not automatically started. It needs to be compiled and run manually or configured as a systemd service.

3. **Database**: Currently using SQLite in Replit. Production deployment should use PostgreSQL for better performance.

---

## Next Steps for Full Deployment

1. **Compile virtual-fido**: Build the Go service for target architecture (ARM for Orange Pi)
2. **Create systemd service**: Add virtual-fido as a systemd service
3. **Test on real hardware**: Deploy to Orange Pi and test all features
4. **Multi-instance testing**: Set up 2+ instances and verify discovery works
5. **Documentation**: Update user-facing documentation with setup instructions

---

*Document last updated: January 27, 2026*
