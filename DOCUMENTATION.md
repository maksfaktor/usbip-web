# Orange USB/IP Web Interface - Technical Documentation

**Version:** 2.0.0  
**Last Updated:** November 25, 2025  
**Language:** English Interface Only  
**Repository:** https://github.com/maksfaktor/usbip-web

---

## Table of Contents

1. [Project Overview](#1-project-overview)
2. [System Architecture](#2-system-architecture)
3. [Installation Guide](#3-installation-guide)
4. [Project File Structure](#4-project-file-structure)
5. [Core Modules Description](#5-core-modules-description)
6. [Database Schema](#6-database-schema)
7. [API Endpoints](#7-api-endpoints)
8. [FIDO2 Virtual Device Integration](#8-fido2-virtual-device-integration)
9. [Configuration](#9-configuration)
10. [Troubleshooting](#10-troubleshooting)
11. [Security Considerations](#11-security-considerations)

---

## 1. Project Overview

### 1.1 Purpose

Orange USB/IP Web Interface is a comprehensive web-based solution for managing USB/IP devices on Linux systems. It provides:

- **Physical USB Device Management** - Share and connect USB devices over network
- **Virtual USB Device Emulation** - Create virtual HID, storage, and serial devices
- **FIDO2/U2F Security Key Emulation** - Virtual hardware security key for WebAuthn authentication
- **Real-time Monitoring** - Device status, logs, and diagnostics
- **Cross-platform Support** - Works on ARM (Orange Pi, Raspberry Pi), x86, x86_64, ARM64

### 1.2 Technology Stack

| Component | Technology |
|-----------|------------|
| Backend | Python 3.11+, Flask 3.x |
| Database | SQLite (default), PostgreSQL (optional) |
| ORM | SQLAlchemy 2.x |
| Authentication | Flask-Login |
| Frontend | Bootstrap 5.3, Bootstrap Icons |
| USB/IP | Linux kernel modules (usbip-core, usbip-host, vhci-hcd) |
| FIDO2 | virtual-fido (Go-based, auto-approval mode) |
| Process Manager | Gunicorn |
| Service Manager | Systemd |

### 1.3 Supported Platforms

- **Debian/Ubuntu** (x86_64, ARM64)
- **Raspberry Pi OS** (ARM, ARM64)
- **Orange Pi** (ARM, ARM64)
- **Other Linux distributions** with USB/IP support

---

## 2. System Architecture

### 2.1 High-Level Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                    Web Browser (Client)                      │
│                  http://server-ip:5000                       │
└─────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────┐
│                    Gunicorn WSGI Server                      │
│                    (Port 5000, systemd)                      │
└─────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────┐
│                    Flask Application                         │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────────────┐  │
│  │   app.py    │  │fido_routes  │  │  storage_routes     │  │
│  │  (main)     │  │   .py       │  │      .py            │  │
│  └─────────────┘  └─────────────┘  └─────────────────────┘  │
│                           │                                  │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────────────┐  │
│  │ usbip_utils │  │ fido_utils  │  │virtual_storage_utils│  │
│  │    .py      │  │    .py      │  │        .py          │  │
│  └─────────────┘  └─────────────┘  └─────────────────────┘  │
└─────────────────────────────────────────────────────────────┘
          │                  │                    │
          ▼                  ▼                    ▼
┌──────────────┐  ┌──────────────────┐  ┌─────────────────────┐
│   USB/IP     │  │  virtual-fido    │  │   Virtual Storage   │
│   Kernel     │  │   (Go binary)    │  │      (Files)        │
│   Modules    │  │   Auto-approval  │  │                     │
└──────────────┘  └──────────────────┘  └─────────────────────┘
```

### 2.2 Component Interaction

1. **Web Interface** → Flask routes handle HTTP requests
2. **Flask App** → Calls utility modules for device operations
3. **Utility Modules** → Execute system commands via subprocess
4. **Kernel/Binaries** → Perform actual USB/IP and FIDO operations

---

## 3. Installation Guide

### 3.1 Quick Installation

**For Debian/Ubuntu/ARM64/x86_64:**
```bash
sudo bash -c "$(curl -fsSL https://raw.githubusercontent.com/maksfaktor/usbip-web/main/install_debian.sh)"
```

**For ARMv7 (Orange Pi, Raspberry Pi 32-bit):**
```bash
sudo bash -c "$(curl -fsSL https://raw.githubusercontent.com/maksfaktor/usbip-web/main/install_arm.sh)"
```

### 3.2 Installation Steps (What the script does)

| Step | Description |
|------|-------------|
| 1/11 | Check operating system and architecture |
| 2/11 | Update package list |
| 3/11 | Install required packages (git, python3, usbutils, etc.) |
| 4/11 | Check and configure USB/IP kernel modules |
| 5/11 | Start usbipd daemon |
| 6/11 | Clone repository to `~/orange-usbip` |
| 7/11 | Set up Python virtual environment |
| 8/11 | Install Python dependencies |
| 9/11 | Configure FIDO2 virtual device |
| 10/11 | Create and start systemd service |
| 11/11 | Configure sudo permissions |

### 3.3 Post-Installation

- **Web Interface:** `http://<server-ip>:5000`
- **Default Credentials:** `admin` / `admin`
- **Service Name:** `orange-usbip`
- **Logs:** `sudo journalctl -u orange-usbip`

### 3.4 Uninstallation

```bash
cd ~/orange-usbip && chmod +x uninstall.sh && sudo ./uninstall.sh
```

---

## 4. Project File Structure

### 4.1 Root Directory

```
orange-usbip/
├── app.py                    # Main Flask application
├── main.py                   # Application entry point
├── models.py                 # SQLAlchemy database models
├── fido_routes.py            # FIDO2 device Flask blueprint
├── fido_utils.py             # FIDO2 utility functions
├── storage_routes.py         # Virtual storage Flask blueprint
├── usbip_utils.py            # USB/IP utility functions
├── virtual_storage_utils.py  # Virtual storage utilities
├── doctor.sh                 # System diagnostics script
├── install_debian.sh         # Debian/Ubuntu installation script
├── install_arm.sh            # ARM installation script
├── uninstall.sh              # Uninstallation script
├── requirements-deploy.txt   # Python dependencies
├── .env                      # Environment configuration (created on install)
├── usbip_web.db              # SQLite database (created on first run)
├── templates/                # HTML templates
├── static/                   # CSS, JS, images
└── virtual-fido/             # FIDO2 binary and source
```

### 4.2 Core Application Files

| File | Description |
|------|-------------|
| `app.py` | Main Flask application with routes for USB device management, authentication, logging, diagnostics |
| `main.py` | Simple entry point that imports and runs the Flask app |
| `models.py` | SQLAlchemy models: User, LogEntry, DeviceAlias, VirtualUsbDevice, FidoDevice, FidoCredential, FidoLog |
| `fido_routes.py` | Flask Blueprint for FIDO2 device management (/fido/*) |
| `fido_utils.py` | Functions: start_fido_device(), stop_fido_device(), get_fido_status(), manage credentials |
| `storage_routes.py` | Flask Blueprint for virtual USB storage management |
| `usbip_utils.py` | Functions: get_local_usb_devices(), bind_device(), unbind_device(), attach/detach remote devices |
| `virtual_storage_utils.py` | Virtual USB storage device management |

### 4.3 Templates Directory

```
templates/
├── base.html                 # Base template with navigation
├── login.html                # Login page
├── index.html                # Main dashboard
├── home2.html                # Alternative home layout
├── logs.html                 # Operation logs viewer
├── terminal.html             # Web terminal interface
├── fido_device.html          # FIDO2 device control panel
├── fido_help.html            # FIDO2 help documentation
└── fido_logs.html            # FIDO2 operation logs
```

### 4.4 Static Files

```
static/
├── css/
│   └── style.css             # Custom styles
├── js/
│   └── app.js                # JavaScript functions
└── img/
    ├── orange_favicon.svg    # Favicon
    └── orange-icon.jpg       # Logo
```

### 4.5 Scripts

| Script | Purpose |
|--------|---------|
| `install_debian.sh` | Full installation for Debian/Ubuntu systems |
| `install_arm.sh` | Full installation for ARM devices |
| `uninstall.sh` | Complete removal with backup creation |
| `doctor.sh` | System diagnostics (kernel modules, services, devices) |

### 4.6 FIDO2 Related Files

```
virtual-fido/
└── cmd/demo/
    ├── virtual-fido-demo     # Compiled Go binary (auto-approval mode)
    ├── demo.go               # Main demo source
    └── server.go             # Server with auto-approval (modified)

~/fido_data/                  # FIDO data directory (user home)
├── virtual-fido              # FIDO binary copy
├── vault.json                # Encrypted credentials storage
└── backups/                  # Vault backups
```

---

## 5. Core Modules Description

### 5.1 app.py - Main Application

**Key Components:**
- Flask app initialization with session management
- Database configuration (SQLite/PostgreSQL)
- Flask-Login setup for authentication
- Route handlers for all pages and API endpoints

**Main Routes:**

| Route | Method | Description |
|-------|--------|-------------|
| `/login` | GET, POST | User authentication |
| `/logout` | GET | User logout |
| `/` | GET | Main dashboard |
| `/home2` | GET | Alternative dashboard |
| `/logs` | GET | Operation logs |
| `/terminal` | GET | Web terminal |
| `/run_doctor` | POST | Run diagnostics |
| `/api/devices` | GET | Get USB devices list |
| `/api/publish/<busid>` | POST | Publish USB device |
| `/api/unpublish/<busid>` | POST | Unpublish USB device |

### 5.2 fido_utils.py - FIDO2 Utilities

**Environment Variables:**
- `FIDO_BINARY_PATH` - Path to virtual-fido binary
- `FIDO_DATA_DIR` - Directory for FIDO data
- `FIDO_VAULT_PATH` - Path to vault.json
- `FIDO_PASSPHRASE` - Vault passphrase

**Key Functions:**

| Function | Description |
|----------|-------------|
| `check_fido_binary()` | Verify FIDO binary exists |
| `start_fido_device()` | Start virtual FIDO device |
| `stop_fido_device()` | Stop virtual FIDO device |
| `get_fido_status()` | Check if device is running |
| `get_fido_credentials()` | List registered credentials |
| `delete_fido_credential()` | Remove a credential |
| `backup_fido_vault()` | Create vault backup |

### 5.3 usbip_utils.py - USB/IP Utilities

**Key Functions:**

| Function | Description |
|----------|-------------|
| `get_local_usb_devices()` | List local USB devices |
| `get_published_devices()` | Get published (bound) devices |
| `get_attached_devices()` | Get remotely attached devices |
| `bind_device(busid)` | Publish device for remote access |
| `unbind_device(busid)` | Unpublish device |
| `attach_remote_device()` | Connect to remote USB device |
| `detach_remote_device()` | Disconnect remote device |
| `run_command()` | Execute system commands with sudo |

---

## 6. Database Schema

### 6.1 Users Table

```sql
CREATE TABLE users (
    id INTEGER PRIMARY KEY,
    username VARCHAR(64) UNIQUE NOT NULL,
    password_hash VARCHAR(256) NOT NULL,
    is_admin BOOLEAN DEFAULT FALSE,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP
);
```

### 6.2 Logs Table

```sql
CREATE TABLE logs (
    id INTEGER PRIMARY KEY,
    timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
    level VARCHAR(20) NOT NULL,
    message TEXT NOT NULL,
    source VARCHAR(50)
);
```

### 6.3 Device Aliases Table

```sql
CREATE TABLE device_aliases (
    id INTEGER PRIMARY KEY,
    busid VARCHAR(20) UNIQUE NOT NULL,
    alias VARCHAR(100) NOT NULL
);
```

### 6.4 FIDO Device Table

```sql
CREATE TABLE fido_devices (
    id INTEGER PRIMARY KEY,
    name VARCHAR(100) DEFAULT 'Virtual FIDO2 Key',
    is_running BOOLEAN DEFAULT FALSE,
    pid INTEGER,
    started_at DATETIME,
    auto_start BOOLEAN DEFAULT FALSE,
    passphrase_hash VARCHAR(256),
    vault_path VARCHAR(500),
    last_error TEXT,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP
);
```

### 6.5 FIDO Credentials Table

```sql
CREATE TABLE fido_credentials (
    id INTEGER PRIMARY KEY,
    device_id INTEGER REFERENCES fido_devices(id),
    credential_id VARCHAR(500) NOT NULL,
    rp_id VARCHAR(255),
    rp_name VARCHAR(255),
    user_name VARCHAR(255),
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP
);
```

### 6.6 FIDO Logs Table

```sql
CREATE TABLE fido_logs (
    id INTEGER PRIMARY KEY,
    device_id INTEGER REFERENCES fido_devices(id),
    timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
    event_type VARCHAR(50) NOT NULL,
    status VARCHAR(20) NOT NULL,
    details TEXT,
    ip_address VARCHAR(45),
    user_agent TEXT
);
```

---

## 7. API Endpoints

### 7.1 Authentication

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/login` | POST | Authenticate user |
| `/logout` | GET | End session |

### 7.2 USB Device Management

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/api/devices` | GET | List all USB devices |
| `/api/publish/<busid>` | POST | Publish device |
| `/api/unpublish/<busid>` | POST | Unpublish device |
| `/api/attach` | POST | Attach remote device |
| `/api/detach/<port>` | POST | Detach remote device |

### 7.3 FIDO2 Device

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/fido/device` | GET | FIDO control panel |
| `/fido/start` | POST | Start FIDO device |
| `/fido/stop` | POST | Stop FIDO device |
| `/fido/status` | GET | Get device status |
| `/fido/credentials` | GET | List credentials |
| `/fido/credentials/<id>` | DELETE | Delete credential |
| `/fido/backup` | POST | Backup vault |
| `/fido/passphrase` | POST | Change passphrase |

### 7.4 System

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/run_doctor` | POST | Run diagnostics |
| `/logs` | GET | View operation logs |
| `/api/logs/clear` | POST | Clear logs |

---

## 8. FIDO2 Virtual Device Integration

### 8.1 Overview

The FIDO2 integration uses **virtual-fido** (https://github.com/bulwarkid/virtual-fido) to emulate a hardware security key like YubiKey. The device supports:

- FIDO2 (CTAP2) protocol
- U2F (CTAP1) protocol
- WebAuthn standard

### 8.2 Auto-Approval Mode

The virtual-fido binary has been modified to **automatically approve** all FIDO operations without requiring terminal confirmation. This enables headless/web-based deployment.

**Modified file:** `virtual-fido/cmd/demo/server.go`

```go
func (support *ClientSupport) ApproveClientAction(action fido_client.ClientAction, params fido_client.ClientActionRequestParams) bool {
    // AUTO-APPROVE MODE: All operations approved automatically
    switch action {
    case fido_client.ClientActionFIDOGetAssertion:
        fmt.Printf("[AUTO-APPROVED] Login for \"%s\"\n", params.RelyingParty)
        return true
    case fido_client.ClientActionFIDOMakeCredential:
        fmt.Printf("[AUTO-APPROVED] Account creation for \"%s\"\n", params.RelyingParty)
        return true
    // ... other cases
    }
    return false
}
```

### 8.3 Testing FIDO Device

1. Start the FIDO device from `/fido/device` page
2. Click "Test Device (Yubico Demo)" or "Test Device (WebAuthn.io)"
3. Create a temporary test account on the demo site
4. Click "Add authenticator" or "Register security key"
5. When browser prompts, click "Allow"
6. Registration completes automatically (no button press needed)

### 8.4 FIDO Data Locations

| Item | Path |
|------|------|
| Binary | `~/fido_data/virtual-fido` |
| Vault | `~/fido_data/vault.json` |
| Backups | `~/fido_data/backups/` |

---

## 9. Configuration

### 9.1 Environment Variables (.env)

```bash
# FIDO2 Configuration
FIDO_BINARY_PATH=/home/user/fido_data/virtual-fido
FIDO_DATA_DIR=/home/user/fido_data
FIDO_VAULT_PATH=/home/user/fido_data/vault.json
FIDO_PASSPHRASE=passphrase

# Session Configuration
SESSION_SECRET=<random-32-byte-hex>
```

### 9.2 Systemd Service

**File:** `/etc/systemd/system/orange-usbip.service`

```ini
[Unit]
Description=Orange USBIP Web Interface
After=network.target usbipd.service

[Service]
User=<username>
Group=<username>
WorkingDirectory=/home/<username>/orange-usbip
EnvironmentFile=/home/<username>/orange-usbip/.env
ExecStart=/home/<username>/orange-usbip/venv/bin/gunicorn --bind 0.0.0.0:5000 main:app
Restart=on-failure
Environment="PATH=/home/<username>/orange-usbip/venv/bin:/usr/local/sbin:/usr/local/bin:/usr/sbin:/usr/bin"

[Install]
WantedBy=multi-user.target
```

### 9.3 Sudoers Configuration

**File:** `/etc/sudoers.d/usbip-<username>`

```
<username> ALL=(ALL) NOPASSWD: /usr/sbin/usbip
<username> ALL=(ALL) NOPASSWD: /usr/bin/usbip
<username> ALL=(ALL) NOPASSWD: /usr/lib/linux-tools/*/usbip
<username> ALL=(ALL) NOPASSWD: /home/<username>/orange-usbip/doctor.sh
```

---

## 10. Troubleshooting

### 10.1 Common Issues

| Issue | Solution |
|-------|----------|
| Internal Server Error on login | Check database permissions: `sudo chown -R user:user ~/orange-usbip` |
| Database read-only error | Fix permissions: `chmod 664 usbip_web.db` |
| FIDO device won't start | Check binary exists: `ls -la ~/fido_data/virtual-fido` |
| USB devices not showing | Load kernel modules: `sudo modprobe usbip-core usbip-host` |
| Service won't start | Check logs: `sudo journalctl -u orange-usbip -n 50` |

### 10.2 Diagnostic Commands

```bash
# Check service status
sudo systemctl status orange-usbip

# View service logs
sudo journalctl -u orange-usbip -n 100

# Run diagnostic script
sudo ~/orange-usbip/doctor.sh

# Check kernel modules
lsmod | grep usbip

# Check usbipd daemon
ps aux | grep usbipd

# Check database permissions
ls -la ~/orange-usbip/*.db
```

### 10.3 Log Locations

| Log Type | Location |
|----------|----------|
| Application logs | `sudo journalctl -u orange-usbip` |
| USB/IP daemon logs | `sudo journalctl -u usbipd` |
| Database logs | In-app at `/logs` page |
| FIDO logs | In-app at `/fido/logs` page |

---

## 11. Security Considerations

### 11.1 Authentication

- Default credentials: `admin`/`admin` - **CHANGE IMMEDIATELY**
- Passwords are hashed using Werkzeug's PBKDF2 with SHA-256
- Session management via Flask-Login with secure cookies

### 11.2 FIDO2 Security

- **Auto-approval mode** is for development/testing only
- Vault is encrypted with passphrase
- Change default passphrase in production
- Regular backups recommended

### 11.3 Network Security

- Bind to `0.0.0.0:5000` - accessible from network
- Use firewall to restrict access if needed
- Consider using HTTPS reverse proxy (nginx) for production

### 11.4 Recommendations

1. Change default admin password immediately
2. Use strong FIDO passphrase
3. Regular vault backups
4. Restrict network access with firewall
5. Monitor logs for suspicious activity

---

## Related Documentation

- **[README.md](README.md)** - Quick start guide
- **[FIDO2_INTEGRATION.md](FIDO2_INTEGRATION.md)** - FIDO2 integration plan
- **[FIDO2_PROGRESS.md](FIDO2_PROGRESS.md)** - Development progress and task status

---

*Documentation generated: November 25, 2025*
