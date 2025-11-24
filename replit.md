# Orange USB/IP Web Interface

## Overview
The Orange USB/IP Web Interface is a robust web-based solution for managing USB/IP devices on Linux systems. It provides comprehensive capabilities for configuring, monitoring, and diagnosing USB devices, aiming to simplify device management, enhance system diagnostics, and offer cross-platform compatibility. The project focuses on a professional, English-only interface with a streamlined user experience, targeting both local and remote USB device management.

## User Preferences
- Language: English-only interface
- UI Style: Bootstrap dark theme with clean, professional design
- Icon Style: Orange fruit-based branding to match "Orange Pi" hardware

## System Architecture

### UI/UX Decisions
The interface utilizes a Bootstrap dark theme for a professional and clean aesthetic, incorporating orange fruit-based SVG icons to align with the "Orange Pi" branding. The design prioritizes clear navigation and responsive layouts.

### Technical Implementations
The core application is built with Flask, providing a web interface with authentication powered by Flask-Login. SQLAlchemy is used for object-relational mapping, managing user, device, and log data. USB/IP utilities abstract the underlying device management commands, while virtual storage utilities handle virtual USB device file management. The system includes enhanced session and error handling for API requests and detailed diagnostic tools.

### Feature Specifications
- **USB Device Management**: Enhanced capabilities for binding, publishing, and unpublishing USB devices, with advanced real-time monitoring for both local and remote devices.
- **Virtual Devices**: Management of virtual USB devices, including FIDO2 virtual devices with features like passphrase management, credential listing, and secure deletion.
- **Monitoring & Diagnostics**: Real-time monitoring, intelligent error detection and recovery mechanisms, and a comprehensive diagnostic tool (`doctor.sh`).
- **Logging**: Comprehensive operation history display with filtering, pagination, and user/IP tracking for FIDO2 operations.
- **Installation & Maintenance**: Streamlined installation and uninstallation processes, including robust Debian/Ubuntu scripts with dependency management, service configuration, and error handling.
- **Terminal Integration**: A web-based terminal for command execution with custom command buttons and history.
- **Language**: English-only interface for simplified maintenance.

### System Design Choices
The application is designed to be cross-platform compatible within Linux environments. It uses a comprehensive logging system for troubleshooting and persistent storage via a PostgreSQL database (though SQLite is also supported for simpler deployments). The system's modular design separates concerns into distinct Python modules (e.g., `app.py`, `models.py`, `usbip_utils.py`).

## External Dependencies
- **Flask**: Web framework
- **SQLAlchemy**: ORM for database interactions
- **Flask-Login**: User session management
- **Bootstrap**: Frontend framework for UI components
- **python-dotenv**: For loading environment variables (e.g., FIDO_PASSPHRASE)
- **USB/IP tools**: Underlying Linux utilities for USB device virtualization
- **PostgreSQL**: Primary database for persistent storage (SQLite also supported)

## Recent Changes

### November 24, 2025
- **Uninstall Script Hotfix**: Fixed uninstall.sh to correctly remove project folder
  - Auto-detects installation path (~$USER/orange-usbip instead of hardcoded /opt/orangeusb)
  - Automatically removes project folder without confirmation
  - Proper cleanup of all application files
- **Doctor.sh Sudo Permissions Hotfix**: Fixed diagnostic tool to run without password prompts
  - Added doctor.sh to sudoers configuration with NOPASSWD
  - Fixed script path to use absolute path instead of relative
  - Added sudo -n flag for non-interactive execution
- **Database Permissions Hotfix**: Fixed installation script to create database with correct ownership
  - Database now initialized as user (not root) before service starts
  - Automatic permission setup prevents "readonly database" errors
  - Installation is now fully automatic with no manual configuration needed
- **FIDO2 Virtual Device Integration - Logs Viewer & Portable Paths**: Completed Tasks 13 & 13.1 (73.0% progress)
  - Task 13: Comprehensive logs viewer with filtering, pagination, and cleanup
  - Task 13.1: Universal Linux compatibility with environment variable support