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

### July 9, 2025
- **Added Permanent Cancel Button**: Replaced temporary Cancel button with permanent solution to prevent disappearing buttons
  - Replaced "Set Name" button with permanent "Cancel" button that's always visible
  - Cancel button is disabled (gray) for unpublished devices, active (yellow) for published devices
  - Fixed auto-refresh issue where Cancel buttons would disappear after API updates
  - Added handleCancelDevice() function for consistent unpublish functionality
  - Updated both main page (/) and home2 page (/home2) with permanent Cancel buttons
  - Added Home2 navigation link to menu for easier access during testing
- **Removed Home2 Page**: Cleaned up codebase by removing temporary testing page
  - Deleted home2() function from app.py
  - Removed Home2 navigation link from base.html
  - Deleted templates/home2.html file
  - Created backup on GitHub before removal
  - Consolidated functionality into main page only
- **Stable Version Backup**: Created comprehensive backup of working version
  - All critical files synchronized to GitHub repository
  - Permanent Cancel buttons working correctly
  - Auto-refresh issue resolved
  - Clean codebase without temporary testing pages
  - Full multilingual support maintained
- **Fixed Cancel Button Visibility on Main Page**: Resolved critical issue where unpublish functionality was missing from index.html
  - Added "Cancel" button to main page (index.html) for published devices instead of disabled "Published" button
  - Added handleUnbindDevice() JavaScript function to handle device unpublication on main page
  - Now both main page (/) and simplified page (/home2) support device unpublication
  - Published devices show yellow "Cancel" button that allows removing device from publication
  - Automatic device list refresh after unpublication with proper UI feedback
- **Fixed Device Publication Status Detection**: Resolved critical bug where device status wasn't updating after publication
  - Replaced complex `get_published_devices()` function with simpler, more reliable approach
  - Method 1: Check `/sys/bus/usb/drivers/usbip-host/` directory for device links
  - Method 2: Parse `doctor.sh` output for device status information
  - Method 3: Test bind attempt to detect if device is already bound
  - Removed non-existent `usbip list -b` command usage
  - Fixed "already bound to usbip-host" error handling as success case
- **Enhanced JavaScript UI Updates**: Fixed device status refresh after publication
  - Added real-time device status updates without page reload
  - Implemented `/api/devices/local` endpoint for AJAX device list refresh
  - Added proper button state management for publish/unpublish actions
  - Fixed notification system with proper success/error handling
  - Added automatic device list refresh with visual feedback
- **Improved Error Handling**: Fixed all Russian text in logging to English
  - Updated all `bind_device()` function logs to English
  - Fixed parsing function logs to use English
  - Standardized error messages and debug output language
  - Enhanced server-side logging for better troubleshooting
- **Added Device Unpublish Functionality**: Implemented "Cancel" button to remove devices from publication
  - Added `unbind_device()` function to usbip_utils.py with comprehensive error handling
  - Created `/unbind_device` route in app.py with proper JSON response handling
  - Updated home2.html template with conditional publish/unpublish buttons
  - Added `handleUnbindDevice()` JavaScript function with real-time UI updates
  - Enhanced `updateDeviceStatus()` function to handle both published and unpublished states
  - Added multilingual support for "unpublish" button in translations.py
  - Published devices now show yellow "Cancel" button instead of disabled green "Published" button
- **UI Bug Fixes**: Fixed critical JavaScript and API endpoint issues
  - Corrected API endpoint URL from `/api/local_devices` to `/api/devices/local` in index.html
  - Fixed conditional display logic for publish/unpublish buttons in home2.html
  - Added proper error handling for device list refresh operations
  - Fixed orange-icon.jpg path resolution for favicon and branding
  - Enhanced notification system with Russian language error messages
- **Critical JavaScript Fixes**: Fixed JavaScript functions preventing Cancel buttons from appearing
  - Fixed `handleBindDevice()` and `handleUnbindDevice()` functions to properly handle form events
  - Corrected button element selection to use form.querySelector() instead of event.target
  - Fixed badge status update logic to use proper DOM traversal methods
  - Resolved busid='error' issue by improving event handling and form data extraction
  - Cancel buttons now properly appear for published devices after page refresh

### July 8-9, 2025
- **Device Publication Fix**: Fixed JavaScript syntax errors preventing device publication
  - Replaced ES6 template literals with compatible string concatenation
  - Added proper AJAX handling for device publication with visual feedback
  - Fixed SyntaxError in notification system and fetch requests
  - Publication button now shows loading spinner and success/error notifications
  - Added comprehensive debugging and console logging for troubleshooting
  - Enhanced server-side request logging with detailed headers and form data
  - **CRITICAL FIX**: Fixed busid mismatch - now uses `usbip list -l` instead of `lsusb`
  - Device busid from `lsusb` (1-5) didn't match `usbip` requirements (1-8)
  - Updated get_local_usb_devices() to prioritize usbip list -l for correct busid
- **Device Name & Status Display Fix**: Fixed device name parsing and publication status detection
  - Improved usbip list -l parsing to extract proper device names from multi-line format
  - Fixed "Unknown Device" issue - now shows "Chicony Electronics Co., Ltd : unknown product"
  - Enhanced get_published_devices() function with detailed logging for status detection
  - Added proper multi-line parser for device name extraction from usbip output
  - **BACKUP CREATED**: orange-usbip-backup-20250709-012300.tar.gz with all latest fixes
- **Full Device Names Integration**: Combined lsusb full names with usbip correct busid
  - Enhanced get_local_usb_devices() to merge data from both lsusb and usbip list -l
  - Now displays complete device names: "MosArt Semiconductor Corp. Wireless Keyboard/Mouse"
  - Maintains correct busid format from usbip for proper device binding
  - Shows VID:PID format consistently across interface
  - Fallback system when either lsusb or usbip commands fail
  - Updated home2.html template to display full_name field with proper formatting
  - **CONFIRMED WORKING**: User reports full device names now display correctly
- **SQLAlchemy Compatibility Fix**: Updated code to work with SQLAlchemy 1.4.50 (Ubuntu system version)
  - Changed import from `DeclarativeBase` to `declarative_base` for compatibility
  - Fixed base class creation to use `declarative_base()` instead of class inheritance
  - Resolved service startup failures caused by SQLAlchemy version conflicts
  - Created diagnostic scripts (`fix_dependencies.sh`, `fix_sqlalchemy_conflict.sh`) for installation troubleshooting
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
  - **Database Configuration Fix**: Fixed 500 error after login by correcting SQLite configuration
    - Resolved circular import issues between main.py and app.py
    - Restored proper SQLite-only configuration (removed PostgreSQL references)
    - Fixed admin user creation logic to work correctly with SQLite
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