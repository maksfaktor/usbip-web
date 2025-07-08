# Changelog - Orange USB/IP Web Interface

## [2025-07-08] - Major Installation Script Enhancement

### Added
- **Professional Installation Script** (`install_debian.sh`) with comprehensive features:
  - System requirements validation and automated dependency management
  - Intelligent cleanup of previous installations to prevent conflicts
  - Enhanced USB/IP daemon configuration with security hardening
  - Robust error handling with timeout protection and diagnostic feedback
  - Visual progress tracking with step-by-step installation status
  - Complete help system with `--help` option support
  - Support for force updates with `--force` option

### Changed
- **Backup System**: Created `install_debian_old.sh` as stable backup version
- **Documentation**: Updated README.md with installation options and backup instructions
- **Service Configuration**: Improved systemd service configuration with better security settings
- **Error Handling**: Enhanced error detection and recovery mechanisms

### Technical Improvements
- Added comprehensive system requirement checking
- Implemented process conflict detection and resolution
- Enhanced service startup with timeout protection
- Added detailed diagnostic functions for troubleshooting
- Improved installation progress tracking with visual feedback

### Files Modified
- `install_debian.sh` - Completely rebuilt with professional features
- `install_debian_old.sh` - Added as backup of previous version
- `README.md` - Updated with new installation options
- `replit.md` - Updated project documentation
- GitHub repository updated with all changes

### Installation Options
```bash
# Standard installation
sudo bash -c "$(curl -fsSL https://raw.githubusercontent.com/maksfaktor/usbip-web/main/install_debian.sh)"

# Show help
sudo bash -c "$(curl -fsSL https://raw.githubusercontent.com/maksfaktor/usbip-web/main/install_debian.sh)" -- --help

# Force update
sudo bash -c "$(curl -fsSL https://raw.githubusercontent.com/maksfaktor/usbip-web/main/install_debian.sh)" -- -f

# Use stable backup version
sudo bash -c "$(curl -fsSL https://raw.githubusercontent.com/maksfaktor/usbip-web/main/install_debian_old.sh)"
```

### Compatibility
- Fully tested on Debian/Ubuntu systems
- Compatible with all architectures (x86, x86_64, ARM, ARM64)
- Maintains backward compatibility with existing installations