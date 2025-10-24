# Orange USB/IP Web Interface

## Overview
The Orange USB/IP Web Interface is a robust web-based management tool designed for configuring, monitoring, and diagnosing USB/IP devices across Linux systems. It aims to provide comprehensive device control, real-time monitoring, and advanced system diagnostics, targeting enhanced USB device binding, publication, and cross-platform compatibility. The project envisions streamlining USB device management with an intuitive, multilingual user interface.

## User Preferences
- Language: Russian/English multilingual support
- UI Style: Bootstrap dark theme with clean, professional design
- Icon Style: Orange fruit-based branding to match "Orange Pi" hardware

## System Architecture

### UI/UX Decisions
The interface utilizes a Bootstrap dark theme for a professional and clean aesthetic. Branding is consistent with "Orange Pi" hardware through the use of an orange fruit-based icon style. The UI includes real-time device status updates and a notification system for user feedback.

### Technical Implementations
The core application is built with Flask, providing web interface capabilities and authentication via Flask-Login. SQLAlchemy is used for database interactions, managing users, devices, and logs. Key functionalities are encapsulated in `usbip_utils.py` for USB/IP device management and `virtual_storage_utils.py` for virtual USB device handling. Multilingual support is provided through a dedicated translation system (`translations.py`). The system integrates comprehensive diagnostic capabilities via `doctor.sh` and includes a web-based terminal for command execution.

### Feature Specifications
- Enhanced USB device binding and publication.
- Real-time monitoring for local and remote USB devices.
- Intelligent error detection and recovery.
- Cross-platform device compatibility.
- Internationalized user interface.
- Streamlined installation and uninstallation processes.
- Improved session and error handling for API requests.
- Comprehensive diagnostic tools.
- Web terminal with command execution and management.

### System Design Choices
- **Core Components**:
    - `app.py`: Main Flask application.
    - `models.py`: Database models for users, devices, logs.
    - `usbip_utils.py`: USB/IP device management functions.
    - `virtual_storage_utils.py`: Virtual USB device file management.
    - `translations.py`: Multilingual interface support.
- **Database**: PostgreSQL database for persistent storage (though SQLite is used for simplified installations).
- **Frontend**: Bootstrap CSS framework for responsive design, SVG icons for scalable graphics.
- **Logging**: Comprehensive logging system for troubleshooting.

## External Dependencies
- **Flask**: Web framework.
- **Flask-Login**: User session management.
- **SQLAlchemy**: ORM for database interactions.
- **Bootstrap**: CSS framework.
- **USB/IP utilities**: Underlying Linux tools for USB/IP functionality.
- **PostgreSQL**: Primary database.
- **SQLite**: Alternative database for simpler setups.