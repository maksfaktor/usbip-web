# Orange USB/IP Web Interface

## Project Overview
A comprehensive USB/IP device management web interface designed for robust device configuration, monitoring, and advanced system diagnostics across Linux architectures.

## User Preferences
- Language: Russian/English multilingual support
- UI Style: Bootstrap dark theme with clean, professional design
- Icon Style: Orange fruit-based branding to match "Orange Pi" hardware

## Project Architecture

### Core Components
- **Flask Application** (`app.py`): Main web interface with authentication
- **Database Models** (`models.py`): SQLAlchemy models for users, devices, logs
- **USB/IP Utilities** (`usbip_utils.py`): Core device management functions
- **Virtual Storage** (`virtual_storage_utils.py`): Virtual USB device file management
- **Translation System** (`translations.py`): Multilingual interface support

### Key Features
- Enhanced USB device binding and publication capabilities
- Advanced real-time monitoring for local and remote USB devices
- Intelligent error detection and recovery mechanisms
- Cross-platform device compatibility with detailed diagnostic tools
- Internationalized user interface supporting multiple languages
- Streamlined installation and uninstallation processes
- Improved session and error handling for API requests

## Recent Changes

### July 8, 2025
- **New Application Icon**: Created custom orange fruit SVG icon (`static/orange-icon.svg`) to match Orange Pi branding
- **Updated Templates**: Modified `base.html` and `login.html` to use new orange icon
- **Enhanced Home2 Page**: Added `/home2` route with simplified USB device management interface
- **Improved Logging**: Added detailed debug logging for device publication tracking

### Previous Updates
- Enhanced get_published_devices() function with multiple detection methods
- Fixed JavaScript syntax errors in API responses
- Created simplified alternative interface (home2.html)
- Added comprehensive diagnostic capabilities with doctor.sh integration
- Implemented automated installation scripts for ARM and x86 architectures

## File Structure
```
├── app.py                 # Main Flask application
├── models.py              # Database models
├── usbip_utils.py         # USB/IP device management
├── virtual_storage_utils.py # Virtual device file handling
├── translations.py        # Multilingual support
├── templates/             # HTML templates
│   ├── base.html         # Base template with navigation
│   ├── login.html        # Login interface
│   ├── home2.html        # Simplified device management
│   └── ...
├── static/               # Static assets
│   ├── orange-icon.svg   # Application icon
│   └── ...
└── ...
```

## Development Notes
- Uses Flask-Login for authentication
- PostgreSQL database for persistent storage
- Bootstrap CSS framework for responsive design
- SVG icons for scalable graphics
- Comprehensive logging system for troubleshooting

## Installation Scripts
- `install_debian.sh`: Debian/Ubuntu installation
- `install_arm.sh`: ARM-specific installation
- `uninstall.sh`: Complete removal with backup
- `doctor.sh`: System diagnostic tool