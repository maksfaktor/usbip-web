# Orange USB/IP Web Interface

## Project Overview
A comprehensive USB/IP device management web interface designed for robust device configuration, monitoring, and advanced system diagnostics across Linux architectures.

## User Preferences
- Language: English-only interface (Russian translations removed October 2025)
- UI Style: Bootstrap dark theme with clean, professional design
- Icon Style: Orange fruit-based branding to match "Orange Pi" hardware

## Project Architecture

### Core Components
- **Flask Application** (`app.py`): Main web interface with authentication
- **Database Models** (`models.py`): SQLAlchemy models for users, devices, logs
- **USB/IP Utilities** (`usbip_utils.py`): Core device management functions
- **Virtual Storage** (`virtual_storage_utils.py`): Virtual USB device file management

### Key Features
- Enhanced USB device binding and publication capabilities
- Advanced real-time monitoring for local and remote USB devices
- Intelligent error detection and recovery mechanisms
- Cross-platform device compatibility with detailed diagnostic tools
- English-only interface for simplified maintenance and consistency
- Streamlined installation and uninstallation processes
- Improved session and error handling for API requests

## Recent Changes

### November 24, 2025
- **FIDO2 Virtual Device Integration - Logs Viewer**: Completed Task 13 (72.2% progress)
  - **Task 13 - Logs Viewer**: Comprehensive operation history display with filtering and pagination
    - Backend API routes: GET `/fido/logs` (with filters), POST `/fido/logs/clear`, GET `/fido/logs/stats`
    - Logs table with columns: Timestamp, Event Type, Status, RP ID/Details, IP Address
    - Advanced filters: Event Type (device_start, device_stop, credential_delete, vault_backup, etc.), Status (success/failed/pending)
    - Pagination: 50 logs per page with Prev/Next navigation
    - Clear Old Logs: Interactive cleanup with customizable retention period (default 30 days)
    - Color-coded status badges: success (green), failed (red), pending (yellow)
    - JavaScript functions: toggleLogFilters(), loadLogs(), displayLogs(), updatePagination(), changePage(), clearOldLogs()
    - Auto-load logs on page load with real-time filtering
    - All operations logged to FidoLog table with user tracking and IP addresses

### October 25, 2025
- **FIDO2 Virtual Device Integration - Passphrase Management**: Completed Tasks 8-11 (61.1% progress)
  - **Task 8 - Help System**: Created comprehensive English-language help and progress tracking
    - Created `FIDO2_PROGRESS.md` (420+ lines) - detailed execution history file
    - Added progress link to main `FIDO2_INTEGRATION.md` documentation
    - Implemented collapsible help section on `fido_device.html`
    - Created separate help page `fido_help.html` (498 lines) with 8 sections
    - All help content in English (First Start, Registration, Authentication, Credentials, Backup, Troubleshooting, FAQ)
    - Added `/fido/help` route in `fido_routes.py`
    - Fixed KeyError bug: `status_info['running']` → `status_info['is_running']`
  - **Task 9 - Credentials Listing**: Implemented credentials table display
    - Table with RP ID (Domain), User, Created, Actions columns
    - Backend: `list_fido_credentials()` parses CLI JSON output
    - Frontend: Bootstrap table with hover effects and badge count
    - Fallback message when no credentials exist
  - **Task 10 - Delete Credentials** (TEST CHECKPOINT #2 PASSED):
    - Delete button with JavaScript confirm dialog
    - Backend route `/fido/credentials/<id>/delete` (DELETE method)
    - Automatic database cleanup after vault deletion
    - Flash messages for user feedback
    - All operations logged to FidoLog table
  - **Task 11 - Passphrase Management**:
    - Backend: `get_fido_passphrase()` and `set_fido_passphrase()` functions with environment variable storage
    - API routes: `GET /fido/passphrase/get` (status), `POST /fido/passphrase/change` (update)
    - Updated all FIDO wrapper functions to use dynamic passphrase from FIDO_PASSPHRASE env var
    - UI: Passphrase Management card with masked display, show/hide toggle, change form
    - JavaScript: Auto-load status, visibility toggle, validation (min 8 chars, confirmation match)
    - Security: Passphrase stored in .env (not database), API never returns actual value, all operations logged
    - Warning alerts about backup and device restart requirements
    - Default passphrase: "passphrase" with insecurity warning indicator
- **Complete Russian Translation Removal**: Removed all Russian language support for English-only interface
  - Deleted `translations.py` file (653 lines) containing Russian/English translation dictionaries
  - Replaced 307 `t()` function calls across 11 HTML templates with direct English text
  - Removed language selector UI components from `base.html`, `login.html`, and `admin.html`
  - Removed translation functions from `app.py`: `get_current_language()`, `inject_translation()`, `/set_language` route
  - Updated device type labels in virtual devices page with English descriptions
  - Simplified logout message handling (removed conditional Russian/English logic)
  - Created automation script (`remove_translations.py`) for bulk t() replacements
  - Synchronized all changes between Replit and GitHub repository
  - **Rationale**: English-only interface simplifies maintenance, reduces complexity, and aligns with professional deployment standards

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