# Orange USB/IP Web Interface - Technical Documentation

**Version:** 2.0  
**Last Updated:** January 26, 2026  
**Language:** English

---

## Table of Contents

1. [Project Overview](#1-project-overview)
2. [System Architecture](#2-system-architecture)
3. [Network Ports & Protocols](#3-network-ports--protocols)
4. [Database Schema](#4-database-schema)
5. [Flask Web Application](#5-flask-web-application)
6. [Virtual FIDO Component](#6-virtual-fido-component)
7. [USB/IP Protocol Implementation](#7-usbip-protocol-implementation)
8. [Security & Encryption](#8-security--encryption)
9. [Installation & Deployment](#9-installation--deployment)
10. [API Reference](#10-api-reference)
11. [Troubleshooting](#11-troubleshooting)

---

## 1. Project Overview

### 1.1 Purpose

The Orange USB/IP Web Interface is a comprehensive web-based solution for managing USB devices over IP networks on Linux systems. It enables:

- **Remote USB Access**: Share physical USB devices over the network
- **Virtual USB Devices**: Create software-emulated USB devices (FIDO2, storage)
- **Centralized Management**: Web interface for all USB/IP operations
- **Security Key Emulation**: Virtual FIDO2/U2F hardware security key

### 1.2 Key Features

| Feature | Description |
|---------|-------------|
| USB Device Management | Bind, publish, attach, detach USB devices |
| Virtual FIDO2 | Software security key supporting WebAuthn |
| Virtual Storage | Emulated USB mass storage devices |
| Real-time Monitoring | Live device status and connection info |
| Web Terminal | Execute commands through browser |
| Multi-user Auth | Flask-Login with role-based access |
| Diagnostic Tools | System health checks via doctor.sh |

### 1.3 Target Platforms

- **Primary**: Debian/Ubuntu Linux (x86_64, aarch64)
- **Hardware**: Orange Pi, Raspberry Pi, x86 servers
- **Browsers**: Chrome, Firefox, Safari (modern versions)

### 1.4 Project Goals

1. **Simplify USB/IP Management**: Replace complex CLI commands with intuitive web UI
2. **Enable Virtual Security Keys**: Provide FIDO2/U2F authentication without hardware tokens
3. **Cross-Platform USB Sharing**: Share USB devices across network boundaries
4. **Zero-Configuration Deployment**: Fully automated installation with sensible defaults

---

## 2. System Architecture

### 2.1 High-Level Architecture

```
┌─────────────────────────────────────────────────────────────────────┐
│                        Client Browser                                │
│                     (Chrome/Firefox/Safari)                          │
└───────────────────────────────┬─────────────────────────────────────┘
                                │ HTTP/HTTPS (Port 5000)
                                ▼
┌─────────────────────────────────────────────────────────────────────┐
│                     Flask Web Application                            │
│  ┌─────────────┐  ┌──────────────┐  ┌───────────────┐               │
│  │   app.py    │  │ fido_routes  │  │ storage_routes│               │
│  │  (Routes)   │  │  (Blueprint) │  │  (Blueprint)  │               │
│  └──────┬──────┘  └──────┬───────┘  └───────┬───────┘               │
│         │                │                   │                       │
│  ┌──────┴────────────────┴───────────────────┴──────┐               │
│  │                    models.py                      │               │
│  │              (SQLAlchemy ORM Models)              │               │
│  └───────────────────────┬───────────────────────────┘               │
│                          │                                           │
│  ┌───────────────────────┴───────────────────────────┐               │
│  │               PostgreSQL / SQLite                  │               │
│  │                   (Database)                       │               │
│  └────────────────────────────────────────────────────┘               │
└───────────────────────────────┬─────────────────────────────────────┘
                                │
           ┌────────────────────┼────────────────────┐
           │                    │                    │
           ▼                    ▼                    ▼
┌──────────────────┐ ┌──────────────────┐ ┌──────────────────┐
│   usbip_utils.py │ │  fido_utils.py   │ │virtual_storage   │
│                  │ │                  │ │   _utils.py      │
│  USB/IP Device   │ │  Virtual FIDO    │ │  Virtual USB     │
│   Management     │ │   Management     │ │    Storage       │
└────────┬─────────┘ └────────┬─────────┘ └──────────────────┘
         │                    │
         ▼                    ▼
┌──────────────────┐ ┌──────────────────────────────────────┐
│    usbipd        │ │         virtual-fido (Go)            │
│   Port 3240      │ │            Port 3241                 │
│  (Real USB)      │ │        (Virtual FIDO2)               │
└──────────────────┘ └──────────────────────────────────────┘
         │                    │
         └────────────────────┴───────────────────┐
                                                  ▼
                              ┌──────────────────────────────┐
                              │     Linux Kernel Modules     │
                              │  usbip-core, usbip-host,     │
                              │        vhci-hcd              │
                              └──────────────────────────────┘
```

### 2.2 Component Overview

#### 2.2.1 Frontend Layer
- **Templates**: Jinja2 HTML templates with Bootstrap 5
- **Styling**: Dark theme with orange accents (Orange Pi branding)
- **JavaScript**: Vanilla JS for AJAX, no heavy frameworks

#### 2.2.2 Application Layer
- **Flask Application** (`app.py`): Main routing and request handling
- **Blueprints**: Modular route organization (fido_routes, storage_routes)
- **Models** (`models.py`): SQLAlchemy ORM for database operations

#### 2.2.3 Business Logic Layer
- **usbip_utils.py**: USB/IP command abstraction
- **fido_utils.py**: Virtual FIDO device management
- **virtual_storage_utils.py**: Virtual USB storage management

#### 2.2.4 Infrastructure Layer
- **usbipd**: Real USB device sharing daemon (port 3240)
- **virtual-fido**: Virtual FIDO2 USB/IP server (port 3241)
- **Kernel Modules**: vhci-hcd, usbip-host, usbip-core

### 2.3 Data Flow

#### Device Publishing Flow
```
User clicks "Publish" → Flask route /publish
    → usbip_utils.bind_device(busid)
        → sudo usbip bind -b <busid>
            → usbip-host kernel module
                → Device available on port 3240
```

#### Virtual FIDO Attachment Flow
```
User clicks "Start FIDO" → Flask route /fido/start
    → fido_utils.start_fido_device()
        → subprocess: virtual-fido start --port 3241
            → USB/IP server listens on port 3241
                → User clicks "Attach to Localhost"
                    → sudo modprobe vhci-hcd
                    → sudo usbip --tcp-port 3241 attach -r 127.0.0.1 -b 2-2
                        → Device appears in lsusb as "0000:0000 Virtual FIDO"
```

---

## 3. Network Ports & Protocols

### 3.1 Port Configuration

| Port | Service | Protocol | Purpose |
|------|---------|----------|---------|
| 5000 | Flask/Gunicorn | HTTP | Web interface |
| 3240 | usbipd | USB/IP | Real USB device sharing |
| 3241 | virtual-fido | USB/IP | Virtual FIDO2 device |

### 3.2 USB/IP Protocol Overview

USB/IP is a Linux kernel-level protocol for sharing USB devices over TCP/IP networks.

#### Protocol Version
```
Version: 0x0111 (1.1.1)
```

#### Control Commands (Connection Setup)
| Command | Code | Direction | Description |
|---------|------|-----------|-------------|
| OP_REQ_DEVLIST | 0x8005 | Client → Server | Request device list |
| OP_REP_DEVLIST | 0x0005 | Server → Client | Reply with device list |
| OP_REQ_IMPORT | 0x8003 | Client → Server | Request device attachment |
| OP_REP_IMPORT | 0x0003 | Server → Client | Confirm attachment |

#### URB Commands (Data Transfer)
| Command | Code | Description |
|---------|------|-------------|
| USBIP_CMD_SUBMIT | 0x00000001 | Submit USB Request Block |
| USBIP_RET_SUBMIT | 0x00000003 | Return completed URB |
| USBIP_CMD_UNLINK | 0x00000002 | Cancel pending URB |
| USBIP_RET_UNLINK | 0x00000004 | Confirm URB cancellation |

### 3.3 Simultaneous Operation

The system is designed for simultaneous operation of real and virtual USB devices:

```
┌─────────────────────────────────────────────────┐
│                 Linux Host                       │
│                                                 │
│  ┌─────────────────┐  ┌─────────────────┐      │
│  │    usbipd       │  │  virtual-fido   │      │
│  │   Port 3240     │  │   Port 3241     │      │
│  │  (Real USB)     │  │ (Virtual FIDO)  │      │
│  └────────┬────────┘  └────────┬────────┘      │
│           │                    │                │
│           ▼                    ▼                │
│  ┌─────────────────────────────────────────┐   │
│  │          vhci-hcd (Virtual HCI)          │   │
│  │   Manages both real and virtual devices  │   │
│  └─────────────────────────────────────────┘   │
│                     │                           │
│           ┌─────────┴─────────┐                │
│           ▼                   ▼                │
│  ┌─────────────┐     ┌─────────────────┐      │
│  │ Real USB    │     │  Virtual FIDO   │      │
│  │ Device      │     │  0000:0000      │      │
│  └─────────────┘     └─────────────────┘      │
└─────────────────────────────────────────────────┘
```

---

## 4. Database Schema

### 4.1 Entity Relationship Diagram

```
┌────────────────┐       ┌────────────────────┐
│     User       │       │   TerminalCommand  │
├────────────────┤       ├────────────────────┤
│ id (PK)        │───────│ id (PK)            │
│ username       │       │ user_id (FK)       │
│ password_hash  │       │ name               │
│ is_admin       │       │ command            │
│ created_at     │       │ description        │
│ updated_at     │       └────────────────────┘
└────────────────┘

┌────────────────────┐       ┌────────────────────┐
│  VirtualUsbDevice  │       │   VirtualUsbFile   │
├────────────────────┤       ├────────────────────┤
│ id (PK)            │───────│ id (PK)            │
│ name               │       │ device_id (FK)     │
│ device_type        │       │ filename           │
│ vendor_id          │       │ file_path          │
│ product_id         │       │ file_size          │
│ is_active          │       │ file_type          │
│ storage_size       │       └────────────────────┘
│ storage_path       │
└────────────────────┘       ┌────────────────────┐
         │                   │   VirtualUsbPort   │
         └───────────────────├────────────────────┤
                             │ id (PK)            │
                             │ device_id (FK)     │
                             │ name               │
                             │ port_number        │
                             │ is_connected       │
                             └────────────────────┘

┌────────────────────┐       ┌────────────────────┐
│    FidoDevice      │       │   FidoCredential   │
├────────────────────┤       ├────────────────────┤
│ id (PK)            │       │ id (PK)            │
│ is_running         │       │ credential_id      │
│ pid                │       │ rp_id              │
│ started_at         │       │ user_id            │
│ stopped_at         │       │ username           │
│ auto_start         │       │ display_name       │
│ vault_path         │       │ created_at         │
│ passphrase_hash    │       │ last_used          │
│ last_error         │       │ use_count          │
└────────────────────┘       └────────────────────┘

┌────────────────────┐       ┌────────────────────┐
│    DeviceAlias     │       │      LogEntry      │
├────────────────────┤       ├────────────────────┤
│ id (PK)            │       │ id (PK)            │
│ busid              │       │ timestamp          │
│ device_info        │       │ level              │
│ alias              │       │ message            │
└────────────────────┘       │ source             │
                             └────────────────────┘
```

### 4.2 Table Descriptions

#### 4.2.1 User Table
Stores user authentication and authorization data.

| Column | Type | Constraints | Description |
|--------|------|-------------|-------------|
| id | INTEGER | PRIMARY KEY | Auto-increment ID |
| username | VARCHAR(64) | UNIQUE, NOT NULL | Login username |
| password_hash | VARCHAR(256) | NOT NULL | Bcrypt/scrypt hash |
| is_admin | BOOLEAN | DEFAULT FALSE | Admin privileges |
| created_at | DATETIME | DEFAULT NOW | Creation time |
| updated_at | DATETIME | AUTO UPDATE | Last modification |

#### 4.2.2 FidoDevice Table
Tracks virtual FIDO device state and configuration.

| Column | Type | Description |
|--------|------|-------------|
| id | INTEGER | Primary key |
| is_running | BOOLEAN | Current running state |
| pid | INTEGER | Process ID when running |
| started_at | DATETIME | Last start time |
| stopped_at | DATETIME | Last stop time |
| auto_start | BOOLEAN | Start on boot flag |
| vault_path | VARCHAR(512) | Path to vault.json |
| passphrase_hash | VARCHAR(256) | Hashed passphrase |
| last_error | TEXT | Last error message |

#### 4.2.3 FidoCredential Table
Metadata for FIDO2 credentials (keys stored in vault).

| Column | Type | Description |
|--------|------|-------------|
| id | INTEGER | Primary key |
| credential_id | VARCHAR(256) | Base64 credential ID |
| rp_id | VARCHAR(256) | Relying party domain |
| user_id | VARCHAR(256) | User identifier |
| username | VARCHAR(256) | Username/email |
| display_name | VARCHAR(256) | Friendly name |
| created_at | DATETIME | Registration time |
| last_used | DATETIME | Last authentication |
| use_count | INTEGER | Authentication count |

---

## 5. Flask Web Application

### 5.1 Application Structure

```
orange-usbip/
├── main.py              # Application entry point
├── app.py               # Flask app initialization & routes
├── models.py            # SQLAlchemy database models
├── usbip_utils.py       # USB/IP command utilities
├── fido_utils.py        # Virtual FIDO management
├── fido_routes.py       # FIDO API routes (Blueprint)
├── virtual_storage_utils.py  # Virtual storage utilities
├── storage_routes.py    # Storage API routes (Blueprint)
├── templates/           # Jinja2 HTML templates
│   ├── base.html        # Base template
│   ├── index.html       # Dashboard
│   ├── login.html       # Login page
│   ├── fido.html        # FIDO management
│   └── ...
├── static/              # Static assets (CSS, JS, images)
└── fido_data/           # FIDO data directory
    ├── vault.json       # Encrypted credential vault
    └── virtual-fido     # Compiled binary
```

### 5.2 Flask Configuration

```python
# Application initialization
app = Flask(__name__)
app.secret_key = os.environ.get("SESSION_SECRET")
app.wsgi_app = ProxyFix(app.wsgi_app, x_proto=1, x_host=1)

# Database configuration
app.config["SQLALCHEMY_DATABASE_URI"] = os.environ.get("DATABASE_URL")
app.config["SQLALCHEMY_ENGINE_OPTIONS"] = {
    "pool_recycle": 300,
    "pool_pre_ping": True,
}

# Login manager
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = "login"
```

### 5.3 Blueprint Registration

```python
from storage_routes import storage_bp
from fido_routes import fido_bp

app.register_blueprint(storage_bp)  # /storage/* routes
app.register_blueprint(fido_bp)     # /fido/* routes
```

### 5.4 Authentication Flow

```
┌──────────┐     ┌──────────────┐     ┌──────────────┐
│  Client  │────▶│  /login POST │────▶│  Check User  │
└──────────┘     └──────────────┘     └──────┬───────┘
                                             │
                      ┌──────────────────────┼──────────────────────┐
                      ▼                      ▼                      ▼
              ┌──────────────┐       ┌──────────────┐       ┌──────────────┐
              │ User Found   │       │ Password OK  │       │ login_user() │
              │    No?       │       │    No?       │       │   Success    │
              └──────┬───────┘       └──────┬───────┘       └──────┬───────┘
                     │                      │                      │
                     ▼                      ▼                      ▼
              Flash Error           Flash Error            Redirect to /
```

### 5.5 Request Flow

1. **Incoming Request** → Gunicorn worker
2. **WSGI Layer** → ProxyFix middleware (handles reverse proxy headers)
3. **Flask Routing** → Match URL to route function
4. **Authentication** → @login_required decorator checks session
5. **Route Handler** → Execute business logic
6. **Database** → SQLAlchemy ORM operations
7. **Response** → Jinja2 template or JSON response

---

## 6. Virtual FIDO Component

### 6.1 Overview

The Virtual FIDO component is a Go application that emulates a FIDO2/U2F hardware security key. It implements:

- **FIDO2 (CTAP2)**: Modern WebAuthn protocol
- **U2F (CTAP1)**: Legacy Universal 2nd Factor
- **USB/IP Server**: Exposes device over network

### 6.2 Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                    virtual-fido Application                      │
│                                                                 │
│  ┌─────────────────────────────────────────────────────────┐   │
│  │                   fido_client                            │   │
│  │  ┌──────────────────┐  ┌──────────────────────────────┐ │   │
│  │  │  identity_vault  │  │   User Approval Callbacks    │ │   │
│  │  │  (Credentials)   │  │  (auto-approve in headless)  │ │   │
│  │  └────────┬─────────┘  └──────────────────────────────┘ │   │
│  └───────────┼──────────────────────────────────────────────┘   │
│              │                                                   │
│  ┌───────────┴───────────────────────────────────────────────┐ │
│  │                        CTAP Layer                          │ │
│  │  ┌─────────────────────┐  ┌─────────────────────────────┐ │ │
│  │  │     ctap/ctap.go    │  │       u2f/u2f.go            │ │ │
│  │  │  (CTAP2 Protocol)   │  │   (U2F/CTAP1 Protocol)      │ │ │
│  │  └──────────┬──────────┘  └──────────────┬──────────────┘ │ │
│  └─────────────┼─────────────────────────────┼───────────────┘ │
│                └──────────────┬──────────────┘                  │
│                               │                                  │
│  ┌────────────────────────────┴─────────────────────────────┐  │
│  │                    CTAP HID Layer                         │  │
│  │                 ctap_hid/ctap_hid.go                      │  │
│  │           (USB HID Transport Protocol)                    │  │
│  └────────────────────────────┬─────────────────────────────┘  │
│                               │                                  │
│  ┌────────────────────────────┴─────────────────────────────┐  │
│  │                     USB Layer                             │  │
│  │                    usb/usb.go                             │  │
│  │          (USB Descriptors & Endpoints)                    │  │
│  └────────────────────────────┬─────────────────────────────┘  │
│                               │                                  │
│  ┌────────────────────────────┴─────────────────────────────┐  │
│  │                   USB/IP Layer                            │  │
│  │              usbip/usbip_server.go                        │  │
│  │         (USB/IP Protocol Implementation)                  │  │
│  └────────────────────────────┬─────────────────────────────┘  │
│                               │                                  │
└───────────────────────────────┼──────────────────────────────────┘
                                │
                          Port 3241
                                │
                                ▼
                    ┌───────────────────────┐
                    │   vhci-hcd Module     │
                    │  (Virtual USB Host)   │
                    └───────────────────────┘
```

### 6.3 CTAP2 Commands

| Command | Code | Description |
|---------|------|-------------|
| authenticatorMakeCredential | 0x01 | Create new credential |
| authenticatorGetAssertion | 0x02 | Authenticate with credential |
| authenticatorGetInfo | 0x04 | Get authenticator info |
| authenticatorClientPIN | 0x06 | PIN management |
| authenticatorReset | 0x07 | Factory reset |
| authenticatorGetNextAssertion | 0x08 | Get next assertion |
| authenticatorCredentialManagement | 0x0A | Manage credentials |

### 6.4 U2F Commands

| Command | Code | Description |
|---------|------|-------------|
| U2F_REGISTER | 0x01 | Register new key |
| U2F_AUTHENTICATE | 0x02 | Authenticate |
| U2F_VERSION | 0x03 | Get U2F version |

### 6.5 CTAP HID Commands

| Command | Code | Description |
|---------|------|-------------|
| CTAPHID_MSG | 0x03 | Send U2F message |
| CTAPHID_CBOR | 0x10 | Send CTAP2 CBOR command |
| CTAPHID_INIT | 0x06 | Initialize channel |
| CTAPHID_PING | 0x01 | Echo test |
| CTAPHID_CANCEL | 0x11 | Cancel operation |
| CTAPHID_KEEPALIVE | 0x3B | Keep connection alive |
| CTAPHID_WINK | 0x08 | Visual indicator |
| CTAPHID_ERROR | 0x3F | Error response |

### 6.6 Credential Storage (Vault)

#### Vault Structure
```json
{
  "salt": "<base64-encoded-32-bytes>",
  "encryption_key": "<encrypted-DEK>",
  "key_nonce": "<12-byte-nonce>",
  "encrypted_data": "<AES-GCM-encrypted-credentials>",
  "data_nonce": "<12-byte-nonce>"
}
```

#### Decrypted Data Structure
```json
{
  "encryption_key": "<device-encryption-key>",
  "attestation_certificate": "<X.509-DER>",
  "attestation_private_key": "<ECDSA-P256>",
  "authentication_counter": 0,
  "pin_enabled": false,
  "pin_hash": null,
  "sources": [
    {
      "type": "public-key",
      "id": "<credential-id>",
      "private_key": "<ECDSA-P256>",
      "relying_party": {"id": "example.com", "name": "Example"},
      "user": {"id": "<user-id>", "name": "user@example.com"},
      "signature_counter": 5
    }
  ]
}
```

### 6.7 CLI Commands

```bash
# Start virtual FIDO device
virtual-fido start -f vault.json -p "passphrase" --port 3241

# List stored credentials
virtual-fido list -f vault.json -p "passphrase"

# Delete credential by ID prefix
virtual-fido delete -f vault.json -p "passphrase" --id "a1b2c3"

# Verbose mode
virtual-fido start -f vault.json -p "passphrase" -v
```

---

## 7. USB/IP Protocol Implementation

### 7.1 Connection Sequence

```
┌──────────┐                                    ┌──────────┐
│  Client  │                                    │  Server  │
│ (usbip)  │                                    │ (usbipd) │
└────┬─────┘                                    └────┬─────┘
     │                                               │
     │  OP_REQ_DEVLIST (0x8005)                     │
     │ ──────────────────────────────────────────▶ │
     │                                               │
     │  OP_REP_DEVLIST (0x0005)                     │
     │  [Device count, Device descriptors]          │
     │ ◀────────────────────────────────────────── │
     │                                               │
     │  OP_REQ_IMPORT (0x8003)                      │
     │  [Bus ID: "2-2"]                             │
     │ ──────────────────────────────────────────▶ │
     │                                               │
     │  OP_REP_IMPORT (0x0003)                      │
     │  [Device descriptor]                         │
     │ ◀────────────────────────────────────────── │
     │                                               │
     │  === Connection Established ===              │
     │                                               │
     │  USBIP_CMD_SUBMIT (URB)                      │
     │ ──────────────────────────────────────────▶ │
     │                                               │
     │  USBIP_RET_SUBMIT (URB Response)             │
     │ ◀────────────────────────────────────────── │
     │                                               │
```

### 7.2 Device Descriptor Structure

```c
struct usbip_usb_device {
    char path[256];           // Device path
    char busid[32];           // Bus ID (e.g., "2-2")
    uint32_t busnum;          // Bus number
    uint32_t devnum;          // Device number
    uint32_t speed;           // USB speed
    uint16_t idVendor;        // Vendor ID
    uint16_t idProduct;       // Product ID
    uint16_t bcdDevice;       // Device version
    uint8_t bDeviceClass;     // Device class
    uint8_t bDeviceSubClass;  // Device subclass
    uint8_t bDeviceProtocol;  // Device protocol
    uint8_t bConfigurationValue;
    uint8_t bNumConfigurations;
    uint8_t bNumInterfaces;
};
```

### 7.3 URB (USB Request Block) Structure

```c
struct usbip_header {
    uint32_t command;         // USBIP_CMD_* or USBIP_RET_*
    uint32_t seqnum;          // Sequence number
    uint32_t devid;           // Device ID
    uint32_t direction;       // 0=OUT, 1=IN
    uint32_t ep;              // Endpoint number
};

struct usbip_header_cmd_submit {
    uint32_t transfer_flags;
    int32_t transfer_buffer_length;
    int32_t start_frame;      // ISO only
    int32_t number_of_packets;// ISO only
    int32_t interval;
    uint8_t setup[8];         // Control setup packet
};
```

### 7.4 Kernel Modules

| Module | Purpose |
|--------|---------|
| usbip-core | Core USB/IP functionality |
| usbip-host | Export local USB devices |
| vhci-hcd | Virtual Host Controller Interface |

#### Loading Modules
```bash
sudo modprobe usbip-core
sudo modprobe usbip-host   # For exporting devices
sudo modprobe vhci-hcd     # For attaching remote devices
```

---

## 8. Security & Encryption

### 8.1 Authentication Security

#### Password Storage
- **Algorithm**: Werkzeug's `generate_password_hash()` (scrypt by default)
- **Salt**: Random per-password, stored with hash
- **Never**: Store plaintext passwords

#### Session Security
- **Secret Key**: `SESSION_SECRET` environment variable
- **Cookies**: HTTP-only, secure flag when HTTPS
- **CSRF**: Flask's built-in session protection

### 8.2 FIDO Vault Encryption

#### Key Derivation
```
Passphrase
    │
    ▼
┌─────────────────────────────┐
│  scrypt(N=32768, r=8, p=1)  │
│  Salt: 32 random bytes      │
└──────────────┬──────────────┘
               │
               ▼
         Master Key (32 bytes)
               │
               ▼
┌─────────────────────────────┐
│     AES-256-GCM Encrypt     │
│  Nonce: 12 random bytes     │
└──────────────┬──────────────┘
               │
               ▼
    Data Encryption Key (DEK)
               │
               ▼
┌─────────────────────────────┐
│     AES-256-GCM Encrypt     │
│  Nonce: 12 random bytes     │
└──────────────┬──────────────┘
               │
               ▼
      Encrypted Credentials
```

#### Encryption Parameters
| Parameter | Value |
|-----------|-------|
| Algorithm | AES-256-GCM |
| Key Size | 256 bits |
| Nonce Size | 96 bits (12 bytes) |
| Tag Size | 128 bits (16 bytes) |
| KDF | scrypt |
| scrypt N | 32768 |
| scrypt r | 8 |
| scrypt p | 1 |

### 8.3 FIDO2 Cryptography

#### Supported Algorithms
| COSE ID | Algorithm | Usage |
|---------|-----------|-------|
| -7 (ES256) | ECDSA P-256 + SHA-256 | Default for credentials |
| -8 (EdDSA) | Ed25519 | Alternative signatures |
| -36 (ES512) | ECDSA P-521 + SHA-512 | High security |
| -37 (PS256) | RSA-PSS + SHA-256 | RSA attestation |
| -25 | ECDH-HKDF-256 | PIN protocol key agreement |

#### Attestation
- **Type**: Self-attestation
- **Certificate**: Self-signed X.509
- **Key Type**: ECDSA P-256
- **Validity**: 20 years

### 8.4 Sudoers Configuration

The installation script configures passwordless sudo for specific commands:

```
# /etc/sudoers.d/orange-usbip
username ALL=(ALL) NOPASSWD: /usr/sbin/usbip
username ALL=(ALL) NOPASSWD: /usr/sbin/usbipd
username ALL=(ALL) NOPASSWD: /sbin/modprobe
username ALL=(ALL) NOPASSWD: /path/to/doctor.sh
```

---

## 9. Installation & Deployment

### 9.1 System Requirements

| Requirement | Minimum | Recommended |
|-------------|---------|-------------|
| OS | Debian 10 / Ubuntu 20.04 | Debian 12 / Ubuntu 22.04 |
| CPU | ARMv7 / x86 | ARM64 / x86_64 |
| RAM | 256 MB | 512 MB |
| Storage | 500 MB | 1 GB |
| Network | Ethernet | Ethernet + WiFi |

### 9.2 Installation Steps

```bash
# 1. Download installer
wget https://github.com/orange-usbip/orange-usbip/raw/main/install_debian.sh

# 2. Make executable
chmod +x install_debian.sh

# 3. Run installer (as root)
sudo ./install_debian.sh

# 4. Access web interface
# Open http://localhost:5000 or http://<IP>:5000
# Default credentials: admin / admin
```

### 9.3 Installation Process Details

1. **System Check**
   - Verify Debian/Ubuntu OS
   - Check CPU architecture
   - Verify root privileges

2. **Dependencies**
   - python3, python3-pip, python3-venv
   - linux-tools-common, linux-tools-generic
   - Build tools (for Go compilation)

3. **Kernel Modules**
   - Load usbip-core, usbip-host, vhci-hcd
   - Configure to load on boot via /etc/modules

4. **Application Setup**
   - Clone/update from GitHub
   - Create Python virtual environment
   - Install Python packages
   - Initialize database

5. **FIDO Binary**
   - Download pre-built or compile from source
   - Install to fido_data/virtual-fido

6. **Systemd Services**
   - orange-usbip.service (web interface)
   - usbipd.service (USB/IP daemon)

7. **Sudoers Configuration**
   - Passwordless sudo for usbip commands

### 9.4 Directory Structure (Installed)

```
~/orange-usbip/
├── main.py
├── app.py
├── models.py
├── usbip_utils.py
├── fido_utils.py
├── fido_routes.py
├── virtual_storage_utils.py
├── storage_routes.py
├── templates/
├── static/
├── fido_data/
│   ├── virtual-fido
│   └── vault.json
├── venv/
├── usbip_web.db
└── install_debian.sh
```

### 9.5 Systemd Service Configuration

#### orange-usbip.service
```ini
[Unit]
Description=Orange USB/IP Web Interface
After=network.target

[Service]
Type=simple
User=<username>
WorkingDirectory=/home/<username>/orange-usbip
ExecStart=/home/<username>/orange-usbip/venv/bin/gunicorn \
    --bind 0.0.0.0:5000 \
    --reuse-port \
    --reload \
    main:app
Restart=always

[Install]
WantedBy=multi-user.target
```

### 9.6 Environment Variables

| Variable | Description | Default |
|----------|-------------|---------|
| SESSION_SECRET | Flask session encryption key | (random) |
| DATABASE_URL | PostgreSQL connection string | sqlite:///usbip_web.db |
| FIDO_PASSPHRASE | Vault encryption passphrase | passphrase |
| FIDO_VAULT_PATH | Path to vault.json | ./fido_data/vault.json |
| FIDO_BINARY_PATH | Path to virtual-fido binary | ./fido_data/virtual-fido |
| FIDO_DATA_DIR | FIDO data directory | ./fido_data |

---

## 10. API Reference

### 10.1 Authentication Endpoints

#### POST /login
Authenticate user and create session.

**Request:**
```
Content-Type: application/x-www-form-urlencoded

username=admin&password=admin
```

**Response:**
- Success: Redirect to /
- Failure: Redirect to /login with error flash

#### GET /logout
End user session.

**Response:**
- Redirect to /login

### 10.2 Device Management Endpoints

#### GET /api/local_devices
Get list of local USB devices.

**Response:**
```json
{
  "success": true,
  "devices": [
    {
      "busid": "1-2",
      "device_name": "USB Mouse",
      "idVendor": "046d",
      "idProduct": "c077",
      "is_published": false
    }
  ]
}
```

#### POST /publish
Publish (bind) a device for sharing.

**Request:**
```
Content-Type: application/x-www-form-urlencoded

busid=1-2
```

**Response:**
- Redirect to index with status flash

#### POST /unpublish
Unpublish (unbind) a shared device.

**Request:**
```
Content-Type: application/x-www-form-urlencoded

busid=1-2
```

#### GET /api/attached_devices
Get list of attached remote devices.

**Response:**
```json
{
  "success": true,
  "devices": [
    {
      "port": "00",
      "busid": "2-2",
      "remote_host": "127.0.0.1",
      "device_name": "Virtual FIDO"
    }
  ]
}
```

#### POST /attach
Attach a remote USB device.

**Request:**
```
Content-Type: application/x-www-form-urlencoded

host=192.168.1.100&busid=1-2&port=3240
```

#### POST /detach
Detach an attached device.

**Request:**
```
Content-Type: application/x-www-form-urlencoded

port=00
```

### 10.3 FIDO Endpoints

#### GET /fido
FIDO management page.

#### GET /api/fido/status
Get FIDO device status.

**Response:**
```json
{
  "success": true,
  "status": {
    "is_running": true,
    "pid": 12345,
    "started_at": "2026-01-26T10:30:00",
    "is_attached": true,
    "vault_exists": true,
    "credentials_count": 3
  }
}
```

#### POST /api/fido/start
Start virtual FIDO device.

**Response:**
```json
{
  "success": true,
  "message": "FIDO device started",
  "pid": 12345
}
```

#### POST /api/fido/stop
Stop virtual FIDO device.

#### POST /api/fido/attach
Attach FIDO device to localhost.

#### POST /api/fido/detach
Detach FIDO device.

#### GET /api/fido/credentials
List FIDO credentials.

**Response:**
```json
{
  "success": true,
  "credentials": [
    {
      "id": "a1b2c3...",
      "rp_id": "github.com",
      "username": "user@example.com",
      "created_at": "2026-01-20T15:00:00"
    }
  ]
}
```

#### DELETE /api/fido/credentials/<id>
Delete a FIDO credential.

### 10.4 Storage Endpoints

#### GET /api/storage/devices
List virtual storage devices.

#### POST /api/storage/devices
Create virtual storage device.

#### DELETE /api/storage/devices/<id>
Delete virtual storage device.

#### GET /api/storage/devices/<id>/files
List files in virtual storage.

#### POST /api/storage/devices/<id>/upload
Upload file to virtual storage.

#### GET /api/storage/devices/<id>/download/<filename>
Download file from virtual storage.

### 10.5 Terminal Endpoints

#### POST /api/terminal/execute
Execute terminal command.

**Request:**
```json
{
  "command": "ls -la"
}
```

**Response:**
```json
{
  "success": true,
  "output": "total 64\ndrwxr-xr-x ..."
}
```

### 10.6 Diagnostic Endpoints

#### POST /api/run_doctor
Run diagnostic script.

**Response:**
```json
{
  "success": true,
  "output": "=== Orange USBIP Diagnostics ===\n..."
}
```

---

## 11. Troubleshooting

### 11.1 Common Issues

#### Device not appearing after publish
1. Check usbipd is running: `systemctl status usbipd`
2. Verify kernel modules: `lsmod | grep usbip`
3. Check binding status: `usbip list -l`

#### Virtual FIDO not working
1. Verify vhci-hcd is loaded: `lsmod | grep vhci`
2. Check if process is running: `ps aux | grep virtual-fido`
3. Verify port 3241: `ss -tlnp | grep 3241`
4. Check vault file exists and is readable

#### Web interface not accessible
1. Check service status: `systemctl status orange-usbip`
2. Verify port 5000: `ss -tlnp | grep 5000`
3. Check firewall: `ufw status`

### 11.2 Diagnostic Commands

```bash
# Run comprehensive diagnostics
sudo ./doctor.sh

# Check USB/IP status
usbip list -l              # Local devices
usbip list -r <host>       # Remote devices
usbip port                 # Attached devices

# Check kernel modules
lsmod | grep -E "usbip|vhci"

# Check services
systemctl status orange-usbip
systemctl status usbipd

# Check logs
journalctl -u orange-usbip -f
journalctl -u usbipd -f

# Check FIDO process
ps aux | grep virtual-fido
lsusb | grep -i fido
```

### 11.3 Log Locations

| Log | Location |
|-----|----------|
| Application | Database (logs table) |
| Systemd | `journalctl -u orange-usbip` |
| USB/IP | `journalctl -u usbipd` |
| Kernel | `dmesg | grep -i usb` |

### 11.4 Reset Procedures

#### Reset Admin Password
```bash
cd ~/orange-usbip
source venv/bin/activate
python3 -c "
from app import app, db
from models import User
with app.app_context():
    user = User.query.filter_by(username='admin').first()
    user.set_password('newpassword')
    db.session.commit()
"
```

#### Reset FIDO Vault
```bash
rm ~/orange-usbip/fido_data/vault.json
# New vault will be created on next start
```

#### Reset Database
```bash
rm ~/orange-usbip/usbip_web.db
# Restart service to recreate
systemctl restart orange-usbip
```

---

## Appendix A: File Reference

| File | Purpose |
|------|---------|
| main.py | Application entry point |
| app.py | Flask app, routes, initialization |
| models.py | SQLAlchemy database models |
| usbip_utils.py | USB/IP command utilities |
| fido_utils.py | Virtual FIDO management |
| fido_routes.py | FIDO API routes |
| virtual_storage_utils.py | Storage utilities |
| storage_routes.py | Storage API routes |
| install_debian.sh | Installation script |
| uninstall.sh | Uninstallation script |
| doctor.sh | Diagnostic tool |
| virtual-fido/*.go | Go FIDO implementation |

## Appendix B: Glossary

| Term | Definition |
|------|------------|
| CTAP | Client to Authenticator Protocol |
| CTAP2 | Modern FIDO2 protocol |
| U2F | Universal 2nd Factor (legacy) |
| FIDO2 | Fast Identity Online v2 |
| WebAuthn | Web Authentication API |
| USB/IP | USB over IP protocol |
| vhci-hcd | Virtual Host Controller Interface |
| URB | USB Request Block |
| HID | Human Interface Device |
| COSE | CBOR Object Signing and Encryption |
| CBOR | Concise Binary Object Representation |

---

*Document generated: January 26, 2026*  
*Orange USB/IP Web Interface v2.0*
