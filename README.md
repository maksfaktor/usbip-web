# Orange USBIP

A comprehensive web-based solution for managing USB/IP on Linux, allowing you to share, connect, and emulate USB devices over the network.

<div align="center">

**🏆 Completely cross-platform USB device management over network**  
**💻 Works on all Linux: ARM, x86, x86_64, ARM64 📱**

</div>

## 📌 Quick One-line Installation

### ARMv7 (Orange Pi, Raspberry Pi 32-bit):
```bash
sudo bash -c "$(curl -fsSL https://raw.githubusercontent.com/maksfaktor/usbip-web/main/install_arm.sh)"
```

### x86, x86_64, ARM64 (Raspberry Pi 64-bit):
```bash
sudo bash -c "$(curl -fsSL https://raw.githubusercontent.com/maksfaktor/usbip-web/main/install_debian.sh)"
```

### Installation Options:
```bash
# Show help and all options
sudo bash -c "$(curl -fsSL https://raw.githubusercontent.com/maksfaktor/usbip-web/main/install_debian.sh)" -- --help

# Force update (overwrite local changes)
sudo bash -c "$(curl -fsSL https://raw.githubusercontent.com/maksfaktor/usbip-web/main/install_debian.sh)" -- -f

# Use stable backup version if needed
sudo bash -c "$(curl -fsSL https://raw.githubusercontent.com/maksfaktor/usbip-web/main/install_debian_old.sh)"
```

### One-line Uninstallation:
```bash
sudo bash -c "$(curl -fsSL https://raw.githubusercontent.com/maksfaktor/usbip-web/main/uninstall.sh)"
```

### Interactive Service and Application Removal:
```bash
# Download and run interactive removal script
curl -fsSL https://raw.githubusercontent.com/maksfaktor/usbip-web/main/check_and_remove.sh -o check_and_remove.sh
chmod +x check_and_remove.sh
sudo ./check_and_remove.sh
```

This script provides:
- Interactive detection and removal of orange-usbip and usbipd services
- Application directory cleanup with size reporting
- Running process termination with user confirmation
- Comprehensive system status verification

## What is Orange USBIP?

Orange USBIP is a Flask-based web interface for USB/IP technology that allows you to use USB devices over a network. The project is designed for easy management of USB devices on all Linux platforms, including ARM (Raspberry Pi, Orange Pi), x86, x86_64, and ARM64.

## Key Features

✅ **Physical USB Device Management:**
- Share local USB devices for remote access
- Connect to remote devices over the network
- Configure aliases for easy device identification

✅ **Virtual USB Device Emulation:**
- Create virtual HID devices (keyboards, mice)
- Emulate USB storage devices with managed storage
- Configure virtual COM ports

✅ **Additional Features:**
- Multilingual interface (English and Russian)
- Secure access with authentication
- Detailed action logging
- Automatic network interface detection

## Technologies

- Python 3
- Flask
- SQLAlchemy
- SQLite
- USB/IP (Linux)
- Bootstrap 5
- Multilingual interface (English and Russian)

## Requirements

- Linux with USB/IP utility installed
- Python 3.7+

### Installing USB/IP on Linux

On most Linux distributions, you can install the USB/IP utility as follows:

#### Ubuntu/Debian:
```
sudo apt update
sudo apt install linux-tools-generic
```

### Database Information

The application uses SQLite by default, which requires no additional configuration. The database will be automatically created when the application is first launched.

## Installation

### One-line Installation

Simply copy and paste **one** of the following commands into your terminal:

#### For ARMv7 (Orange Pi, Raspberry Pi 32-bit, etc.):

```bash
sudo bash -c "$(curl -fsSL https://raw.githubusercontent.com/maksfaktor/usbip-web/main/install_arm.sh)"
```

#### For x86, x86_64, and ARM64 (including Raspberry Pi 64-bit):

```bash
sudo bash -c "$(curl -fsSL https://raw.githubusercontent.com/maksfaktor/usbip-web/main/install_debian.sh)"
```

### Uninstallation

If you need to uninstall Orange USBIP Web Interface, you have several options:

#### Option 1: Direct download and uninstall (one-line command)

```bash
sudo bash -c "$(curl -fsSL https://raw.githubusercontent.com/maksfaktor/usbip-web/main/uninstall.sh)"
```

#### Option 2: Using uninstall.sh script

```bash
sudo ./uninstall.sh
```

#### Option 3: Using installation scripts with --uninstall parameter

```bash
# For ARM systems
sudo ./install_arm.sh --uninstall

# For Debian/Ubuntu systems
sudo ./install_debian.sh --uninstall
```

The uninstall process will:
- Create a backup of your settings and database in `/var/backups/orangeusb/`
- Stop and remove the systemd service
- Remove application files and configuration
- Clean up the sudoers configuration

### Standard Installation

If you prefer to check the script before running it, you can use the standard approach:

1. Download the installation script
2. Make it executable
3. Run it as superuser

#### For ARM devices (Orange Pi, Raspberry Pi 32-bit):

```bash
wget https://raw.githubusercontent.com/maksfaktor/usbip-web/main/install_arm.sh
chmod +x install_arm.sh
sudo ./install_arm.sh
```

#### For x86, x86_64, and ARM64 systems:

```bash
wget https://raw.githubusercontent.com/maksfaktor/usbip-web/main/install_debian.sh
chmod +x install_debian.sh
sudo ./install_debian.sh
```

### What do the installation scripts do?

The scripts automatically perform all necessary steps:
1. ✅ Check and install all system dependencies
2. ✅ Configure kernel modules for USB/IP
3. ✅ Create and start systemd services
4. ✅ Set up access permissions
5. ✅ Create a working directory and Python virtual environment
6. ✅ Check if a system reboot is needed
7. ✅ Display the IP address for accessing the web interface

After successful installation, the script will display the address for accessing the web interface and the default credentials (`admin`/`admin`). The application will run as a system service that starts automatically when the system boots.

## Usage

After launching the application, open your browser and go to http://localhost:5000/

By default, a user with the login `admin` and password `admin` is created.
**Important**: After the first login, be sure to change the administrator password!

## Cross-platform Compatibility

The application is designed to work on various processor architectures:
- ARM (Orange Pi, Raspberry Pi, etc.)
- x86
- x86-64

### Setup on Orange Pi, Raspberry Pi, and other ARM devices

For installation on ARM devices, it is recommended to use the special automatic script `install_arm.sh`, as described in the "Installation" section. The script handles all platform-specific features, including:

1. Compilation and installation of USB/IP from source (standard packages may not work on some ARM platforms)
2. Configuration and loading of compatible kernel modules
3. Creating necessary system services
4. Optimization for devices with limited resources

After installation, the web interface will be available on port 5000, and logs can be viewed using `sudo journalctl -u orange-usbip`.

## Security

All USB/IP commands are executed with root privileges via sudo.
It is recommended to configure sudoers to run specific usbip commands without a password.

### Configuring Sudo for USB/IP

To avoid constantly entering a password when running USB/IP commands, configure the sudoers file:

```
# Open the sudoers file for editing
sudo visudo -f /etc/sudoers.d/usbip

# Add the following lines, replacing YOUR_USERNAME with your username
YOUR_USERNAME ALL=(ALL) NOPASSWD: /usr/sbin/usbip
YOUR_USERNAME ALL=(ALL) NOPASSWD: /usr/lib/linux-tools/*/usbip

# Save the file and exit (in vi: press ESC, then :wq and Enter)
```

After this, you will be able to run usbip commands with sudo without being prompted for a password.

## Testing in a Local Network

You can set up a test environment with multiple computers, where each can act as both a USB/IP server (providing USB devices) and a client (connecting to remote USB devices).

### Setting up a Test Environment with Two Computers

This guide will help you set up two computers in a local network to test USB/IP functionality.

#### Prerequisites

- Two computers with Linux support
- Local network with connectivity between computers
- USB devices for testing

#### Step 1: Network Configuration

1. Set static IP addresses on both computers:

   **Computer A:**
   ```
   sudo ip addr add 192.168.1.10/24 dev eth0
   ```

   **Computer B:**
   ```
   sudo ip addr add 192.168.1.11/24 dev eth0
   ```

   Replace `eth0` with your network interface name.

2. Make sure the computers can see each other:

   ```
   ping 192.168.1.10  # from Computer B
   ping 192.168.1.11  # from Computer A
   ```

3. Configure the firewall to allow connections on port 3240:

   ```
   sudo ufw allow 3240/tcp  # for Ubuntu/Debian with ufw
   # or
   sudo firewall-cmd --permanent --add-port=3240/tcp  # for Fedora/RHEL
   sudo firewall-cmd --reload
   ```

#### Step 2: Installation on Both Computers

Follow the instructions from the "Installation" section for each computer:

1. Install USB/IP
2. Install dependencies
3. Clone and configure the application

#### Step 3: Starting the USB/IP Daemon

On both computers, start the USB/IP daemon:

```
sudo systemctl start usbipd
sudo systemctl enable usbipd
```

#### Step 4: Running the Application

On both computers, start the application:

```
source venv/bin/activate
gunicorn --bind 0.0.0.0:5000 main:app
```

#### Step 5: Testing Functionality

1. **Testing Device Publication:**
   - On Computer A, open the web interface at http://192.168.1.10:5000/
   - Log in
   - Find your USB devices on the main page
   - Click the "Publish" button for one of the devices

2. **Testing Connection to Remote Devices:**
   - On Computer B, open the web interface at http://192.168.1.11:5000/
   - Log in
   - Go to the "Remote Devices" page
   - Enter Computer A's IP address (192.168.1.10) and click "Search for Devices"
   - You should see the published devices from Computer A
   - Click "Connect" for one of the devices
   - Return to the main page where the connected remote device should now be displayed

3. **Testing in the Opposite Direction:**
   - Repeat steps 1-2, but publish devices from Computer B and connect to them from Computer A

### Troubleshooting

### Diagnostic Tool

Orange USBIP comes with a built-in diagnostic tool that helps identify and resolve common issues.
Run the diagnostic tool with the following command:

```bash
sudo ./doctor.sh
```

The diagnostic tool will check:
- Operating system compatibility
- Required commands availability
- Service status (usbipd and orange-usbip)
- Kernel modules
- Open ports (3240 for usbipd and 5000 for web interface)
- Firewall configuration
- Published USB devices
- Network interfaces
- Connectivity with remote servers

### Common Issues

1. **Devices don't appear on the remote devices page:**
   - Make sure port 3240 is open in the firewall
   - Check if the usbipd daemon is running on the server computer
   - Ensure the device is properly published

2. **Error when connecting to a device:**
   - Check logs on both computers (`journalctl -u usbipd`)
   - Make sure the device is supported by USB/IP (not all devices work)
   - Verify necessary access permissions

3. **Device appears but doesn't work after connection:**
   - Some devices require additional drivers or configuration
   - USB devices requiring high data transfer rates may work unstably over the network
   - Try disconnecting and reconnecting the device

## License

MIT

## Project Structure

### Main Working Files:
✓ app.py - Main application file with routes and logic
✓ models.py - SQLite data models
✓ storage_routes.py - Routes for storage management
✓ translations.py - Multilingual system
✓ usbip_utils.py - Utilities for working with USB/IP
✓ virtual_storage_utils.py - Functions for virtual storage
✓ main.py - Application launcher

### Static Files:
All files in the static/css, static/js, and static/img directories are used in templates via url_for.

### Directories to Ignore in Git:
✓ __pycache__ - Python module cache
✓ .cache - UV cache
✓ attached_assets - Replit support files