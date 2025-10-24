# 🍊 Orange USB/IP Web Interface

<div align="center">

**Modern web-based management interface for USB/IP devices**

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Platform](https://img.shields.io/badge/platform-Linux-blue.svg)](https://www.linux.org/)
[![Python](https://img.shields.io/badge/python-3.8+-blue.svg)](https://www.python.org/)
[![Flask](https://img.shields.io/badge/flask-2.0+-green.svg)](https://flask.palletsprojects.com/)

</div>

---

## 📋 Project Overview

A comprehensive USB/IP device management web interface designed for robust device configuration, monitoring, and advanced system diagnostics across Linux architectures. Built with Flask and modern web technologies, it provides an intuitive interface for sharing USB devices across your network infrastructure.

## ✨ Key Features

- **🔌 USB Device Management**
  - Publish local USB devices to network via USB/IP protocol
  - Attach remote USB devices
  - Real-time monitoring for local and remote USB devices
  - One-click bind/unbind operations
  - Intelligent error detection and recovery mechanisms

- **🖥️ Modern Web Interface**
  - Responsive Bootstrap 5 design
  - Dark theme optimized for Orange Pi
  - Real-time updates without page refresh
  - Mobile-friendly responsive layout
  - Beautiful, functional, production-ready design

- **🔐 Security**
  - User authentication system (Flask-Login)
  - Session management
  - Password hashing (Werkzeug)
  - HTTPS support via reverse proxy (ProxyFix)
  - Permission isolation through systemd

- **🛠️ Advanced Tools**
  - Built-in diagnostic system (`doctor.sh`)
  - Web-based terminal with command execution
  - Virtual USB device support
  - Virtual device file management
  - Comprehensive logging system

- **📊 Monitoring & Diagnostics**
  - Device connection history
  - System health checks
  - Error tracking and reporting
  - Cross-platform device compatibility
  - Detailed diagnostic tools

## 🏗️ Architecture

### Core Components

- **Flask Application** (`app.py`)  
  Main web interface with authentication, routing, and business logic

- **Database Models** (`models.py`)  
  SQLAlchemy models for users, devices, logs, and terminal commands

- **USB/IP Utilities** (`usbip_utils.py`)  
  Core device management functions - publishing, attaching, monitoring

- **Virtual Storage** (`virtual_storage_utils.py`)  
  Virtual USB device file management

### Technology Stack

- **Backend**: Flask, Flask-Login, Flask-SQLAlchemy, Werkzeug
- **Frontend**: Bootstrap 5, JavaScript (vanilla JS, no frameworks)
- **Database**: PostgreSQL / SQLite (supports both)
- **Icons**: Font Awesome, Feather Icons, custom SVG icons
- **USB/IP**: Linux kernel USB/IP drivers (usbip-host, vhci-hcd)
- **Server**: Gunicorn WSGI server

### Database Structure

- **User**: System users (id, username, email, password_hash)
- **Device**: USB devices (busid, vendor, product, status)
- **DeviceLog**: Device operation logs (device_id, action, timestamp)
- **TerminalCommand**: Web terminal commands (name, command, description)

## 🚀 Quick Start

### Installation on Debian/Ubuntu (x86_64 and ARM)

```bash
curl -fsSL https://raw.githubusercontent.com/maksfaktor/usbip-web/main/install_debian.sh -o install_debian.sh
chmod +x install_debian.sh
sudo ./install_debian.sh
```

**Installation script features:**
- Automatic system requirement validation
- Dependency management
- Intelligent cleanup of previous installations
- Professional-grade service configuration with security hardening
- Robust error handling with timeout protection
- Visual progress tracking
- Complete help system (`--help` option)

### Installation on ARM (Orange Pi, Raspberry Pi)

```bash
curl -fsSL https://raw.githubusercontent.com/maksfaktor/usbip-web/main/install_arm.sh -o install_arm.sh
chmod +x install_arm.sh
sudo ./install_arm.sh
```

## 🎯 Usage

### Access the Web Interface

After installation, open your browser and navigate to:
```
http://your-server-ip:5000
```

Default credentials:
- **Username**: admin
- **Password**: admin123

> ⚠️ **Security Notice**: Change the default password immediately after first login!

### Publishing a USB Device

1. Navigate to **Local USB Devices**
2. Locate your device in the list
3. Click the green **"Publish Device"** button
4. Device is now available on the network

### Unbinding a Device

1. Find the published device (marked with green "Published" status)
2. Click the yellow **"Cancel"** button
3. Device will be unbound from USB/IP

### Attaching a Remote Device

1. Go to **Remote USB Devices**
2. Enter the remote server IP address
3. Click **"Show Devices"**
4. Select device and click **"Attach Device"**

## 🔧 Diagnostics & Troubleshooting

### Run the Diagnostic Script

To check system status:

```bash
sudo ./doctor.sh
```

**The script checks:**
- USB/IP kernel modules status (usbip-host, vhci-hcd)
- Service status (usbipd, orange-usbip)
- Connected USB devices
- Published devices
- System and service logs
- Network configuration

## 🗑️ Uninstallation

### Interactive Removal

```bash
curl -fsSL https://raw.githubusercontent.com/maksfaktor/usbip-web/main/check_and_remove.sh -o check_and_remove.sh
chmod +x check_and_remove.sh
sudo ./check_and_remove.sh
```

**Removal script features:**
- Detects and removes orange-usbip and usbipd services
- Checks application directories with size reporting
- Terminates running processes
- Detailed status reporting
- Final system verification

### Complete Removal

```bash
sudo ./uninstall.sh
```

## 📁 File Structure

```
orange-usbip/
├── app.py                      # Main Flask application
├── main.py                     # Entry point (imports app)
├── models.py                   # Database models (SQLAlchemy)
├── usbip_utils.py             # USB/IP management utilities
├── virtual_storage_utils.py   # Virtual device management
├── translations.py            # Translation system (i18n)
├── storage_routes.py          # Virtual device routes
├── templates/                 # Jinja2 HTML templates
│   ├── base.html             # Base template with navigation
│   ├── login.html            # Login page
│   ├── index.html            # Main page (Dashboard)
│   ├── local_devices.html    # Local USB devices
│   ├── remote_devices.html   # Remote USB devices
│   ├── terminal.html         # Web terminal
│   └── ...                   # Other pages
├── static/                    # Static files
│   ├── orange-icon.svg       # Application icon (orange fruit)
│   └── ...                   # CSS, JS, images
├── virtual_storage/          # Virtual device file storage
├── scripts/                  # Installation and utility scripts
│   ├── install_debian.sh    # Debian/Ubuntu installation
│   ├── install_arm.sh       # ARM platform installation
│   ├── uninstall.sh        # Complete removal
│   ├── doctor.sh           # System diagnostics
│   └── check_and_remove.sh # Interactive removal
├── requirements-deploy.txt   # Python dependencies
├── pyproject.toml           # Project configuration
└── usbip_web.db            # SQLite database (when using SQLite)
```

## 💻 Development

### Install Development Dependencies

```bash
pip install -r requirements-deploy.txt
```

### Required Python Packages

- `flask` - Web framework
- `flask-login` - Authentication management
- `flask-sqlalchemy` - ORM for database
- `flask-wtf` - Forms and CSRF protection
- `werkzeug` - Utilities (password hashing)
- `gunicorn` - WSGI server for production
- `sqlalchemy` - SQL toolkit
- `requests` - HTTP library
- `trafilatura` - Text parsing and processing
- `email-validator` - Email validation
- `netifaces` - Network interface operations

### Run in Development Mode

```bash
export DATABASE_URL="sqlite:///usbip_web.db"
export SESSION_SECRET="your-secret-key-here"
python main.py
```

Or with PostgreSQL:
```bash
export DATABASE_URL="postgresql://user:password@localhost/usbip_web"
export SESSION_SECRET="your-secret-key-here"
python main.py
```

### Run in Production Mode

```bash
gunicorn --bind 0.0.0.0:5000 --reuse-port --reload main:app
```

## 🔒 Security

- **Authentication**: Flask-Login for session management
- **Passwords**: Hashed using Werkzeug (default method)
- **HTTPS**: Support via ProxyFix for reverse proxy
- **Isolation**: Systemd service with limited permissions
- **CSRF Protection**: Flask-WTF for form protection
- **Session Secret**: Configurable secret key via environment variables

> ⚠️ **Important**: Never store secret keys in code! Use environment variables.

## 🔧 System Requirements

- **OS**: Linux with USB/IP kernel modules
- **Python**: 3.8 or higher
- **Database**: PostgreSQL or SQLite
- **Memory**: 512MB RAM minimum
- **Storage**: 100MB free space
- **Network**: Open port 5000 (or configurable)

## 🐛 Known Issues and Solutions

**Issue**: Device not showing in list  
**Solution**: Run `sudo ./doctor.sh` for diagnostics. May need to reload USB/IP modules.

**Issue**: Device won't publish  
**Solution**: Ensure device is not used by other programs. Close all programs using the device.

**Issue**: Error "already bound to usbip-host"  
**Solution**: Device is already published. Use "Cancel" button to unbind before republishing.

**Issue**: Service doesn't start after installation  
**Solution**: Check logs: `sudo journalctl -u orange-usbip -n 50`

## 🤝 Contributing

Contributions are welcome! Please follow these guidelines:

1. Fork the repository
2. Create your feature branch (`git checkout -b feature/AmazingFeature`)
3. Commit your changes (`git commit -m 'Add some AmazingFeature'`)
4. Push to the branch (`git push origin feature/AmazingFeature`)
5. Open a Pull Request

**Development guidelines:**
- Follow PEP 8 for Python code
- Add comments for complex logic
- Update documentation when changing functionality
- Test before submitting Pull Request

## 📝 License

This project is licensed under the MIT License - see the LICENSE file for details.

## 🙏 Acknowledgments

- Built for Orange Pi and other ARM platforms
- Inspired by the Linux USB/IP project
- Thanks to the community for contributions and feedback
- Special thanks to contributors and testers

## 📞 Support

- **GitHub Repository**: https://github.com/maksfaktor/usbip-web
- **Report Issues**: https://github.com/maksfaktor/usbip-web/issues
- **Documentation**: In development
- **Wiki**: https://github.com/maksfaktor/usbip-web/wiki

---

<div align="center">

**Made with ❤️ for Orange Pi and Linux community**

[⬆ Back to Top](#-orange-usbip-web-interface)

</div>
