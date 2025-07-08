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
- **Installation Script Recovery**: Restored working `install_debian.sh` from backup after debugging issues
  - Identified critical bugs in enhanced version that caused premature script termination
  - Successfully restored stable version from `install_debian_old.sh`
  - Both files now contain identical, working installation script
  - Maintained backup system for future enhancements
- **Interactive Removal Script**: Created `check_and_remove.sh` for service and application cleanup
  - Comprehensive English-language interactive script for checking and removing Orange USB/IP
  - Detects and removes orange-usbip and usbipd services with user confirmation
  - Checks for application directories in multiple locations with size reporting
  - Terminates running processes with user approval
  - Provides detailed status reporting and final system verification
  - **Final Command**: Confirmed only working command: `curl -fsSL https://raw.githubusercontent.com/maksfaktor/usbip-web/main/check_and_remove.sh -o check_and_remove.sh && chmod +x check_and_remove.sh && sudo ./check_and_remove.sh`
  - **Installation Script Hanging Fix**: Removed automatic usbipd service start during installation
    - Fixed issue where installation would hang indefinitely on `systemctl start usbipd`
    - Installation now only checks service status without attempting to start it
    - Service is enabled during installation and can be started manually after completion
    - Provides clear instructions for manual service management if needed
  - **Doctor.sh Simplification**: Removed interactive network connection test section
    - Deleted Section 9 "Network Connection Test" from doctor.sh diagnostic script
    - Eliminated user prompt for remote server IP address testing
    - Streamlined diagnostic flow to focus on local system checks only
  - **Database Configuration Fix**: Fixed PostgreSQL/SQLite compatibility in main.py and app.py
    - Resolved circular import issues between main.py and app.py
    - Added automatic database type detection based on DATABASE_URL environment variable
    - Fixed admin user creation logic to work with both PostgreSQL and SQLite
    - Corrected 500 error after login on production installations
- **Terminal Page Implementation**: Created comprehensive web terminal with command execution
  - Added `TerminalCommand` model for storing custom command buttons
  - Implemented terminal interface with keyboard support and command history
  - Added command button management (create, edit, delete)
  - Integrated multilingual support for terminal functionality
- **Translation System Fixes**: Fixed all `translate()` function calls to use `t()` 
  - Corrected function usage in `terminal.html`, `home2.html`, and navigation
  - Added complete Russian and English translations for terminal features
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
- `install_debian.sh`: Enhanced Debian/Ubuntu installation with comprehensive features:
  - Automatic system requirement validation and dependency management
  - Intelligent cleanup of previous installations before reinstallation
  - Professional-grade service configuration with security hardening
  - Robust error handling with timeout protection and diagnostic feedback
  - Visual progress tracking and detailed status reporting
  - Complete help system with --help option support
- `install_debian_old.sh`: Backup of previous installation script version for rollback purposes
- `install_arm.sh`: ARM-specific installation
- `uninstall.sh`: Complete removal with backup
- `doctor.sh`: System diagnostic tool for troubleshooting