#!/bin/bash

# Orange USBIP - Automatic installation script for Debian/Ubuntu systems
# Created: $(date +%Y-%m-%d)

set -e  # Stop execution on errors

# Function for displaying colored text
echo_color() {
    local color=$1
    local message=$2
    case $color in
        "green") echo -e "\033[0;32m$message\033[0m" ;;
        "red") echo -e "\033[0;31m$message\033[0m" ;;
        "yellow") echo -e "\033[0;33m$message\033[0m" ;;
        "blue") echo -e "\033[0;34m$message\033[0m" ;;
        *) echo "$message" ;;
    esac
}

# Function for displaying progress
progress_update() {
    local step=$1
    local total=$2
    local message=$3
    echo_color "blue" "[$step/$total] $message"
}

# Check if script is run with root privileges
if [ "$EUID" -ne 0 ]; then
    echo_color "red" "Error: this script must be run with superuser privileges (sudo)."
    echo "Run: sudo $0"
    exit 1
fi

# Determine the real user (not sudo)
if [ -n "$SUDO_USER" ]; then
    REAL_USER=$SUDO_USER
else
    REAL_USER=$(whoami)
fi
USER_HOME=$(eval echo ~$REAL_USER)

echo_color "green" "===================================================="
echo_color "green" "  Orange USBIP Automatic Installation for Debian    "
echo_color "green" "===================================================="
echo ""
echo_color "yellow" "This script will set up the USB/IP server and client on your system."
echo ""

TOTAL_STEPS=10
CURRENT_STEP=0

# Step 1: Check operating system
CURRENT_STEP=$((CURRENT_STEP + 1))
progress_update $CURRENT_STEP $TOTAL_STEPS "Checking operating system..."

if ! command -v apt-get &> /dev/null; then
    echo_color "red" "This system does not use apt-get. This script is designed for Debian/Ubuntu-like systems."
    exit 1
fi

# Check architecture
ARCH=$(uname -m)

# Supported architectures: x86, x86_64, arm64/aarch64
if [[ "$ARCH" == "arm"* ]] && [[ "$ARCH" != "armv7"* ]]; then
    echo_color "green" "✓ Architecture $ARCH is compatible (64-bit ARM)."
elif [[ "$ARCH" == "aarch64" ]]; then
    echo_color "green" "✓ Architecture $ARCH is compatible (64-bit ARM)."
elif [[ "$ARCH" == "armv7"* ]]; then
    echo_color "yellow" "For 32-bit ARM systems (ARMv7), it is recommended to use the install_arm.sh script"
    echo "Continue with installation? (y/n)"
    read -r response
    if [[ "$response" != "y" ]]; then
        echo_color "yellow" "Installation aborted by user."
        exit 0
    fi
elif [[ "$ARCH" == "x86_64" ]] || [[ "$ARCH" == "i686" ]]; then
    echo_color "green" "✓ Architecture $ARCH is compatible (x86/x86_64)."
else
    echo_color "yellow" "Architecture $ARCH has not been tested, but we will try to install."
fi

# Step 2: Update system
CURRENT_STEP=$((CURRENT_STEP + 1))
progress_update $CURRENT_STEP $TOTAL_STEPS "Updating package list..."

apt-get update -qq
echo_color "green" "✓ Repositories updated."

# Step 3: Install required dependencies
CURRENT_STEP=$((CURRENT_STEP + 1))
progress_update $CURRENT_STEP $TOTAL_STEPS "Installing required packages..."

apt-get install -y git python3 python3-pip python3-venv linux-tools-generic usbutils curl > /dev/null 2>&1

# Install uv - modern Python package manager (priority installation)
echo_color "blue" "Installing uv - modern Python package manager..."

# Initialize variables to track installation attempts
UV_INSTALLED=false
INSTALL_METHODS_TRIED=0
INSTALL_METHODS_TOTAL=3

# Method 1: Try installing via official installer script (recommended)
echo_color "blue" "  → Method 1/3: Using official installer script..."
curl -sSf https://astral.sh/uv/install.sh | sh > /dev/null 2>&1
if command -v uv &> /dev/null || [ -f "$HOME/.cargo/bin/uv" ]; then
    echo_color "green" "  ✓ uv successfully installed via official script."
    UV_INSTALLED=true
    # Add uv to PATH
    export PATH="$HOME/.cargo/bin:$PATH"
else
    echo_color "yellow" "  ✗ Official installer failed."
    INSTALL_METHODS_TRIED=$((INSTALL_METHODS_TRIED + 1))
fi

# Method 2: Try installing via pip if method 1 failed
if [ "$UV_INSTALLED" = false ]; then
    echo_color "blue" "  → Method 2/3: Trying installation via pip..."
    pip3 install -q --break-system-packages uv > /dev/null 2>&1
    if command -v uv &> /dev/null; then
        echo_color "green" "  ✓ uv successfully installed via pip."
        UV_INSTALLED=true
    else
        echo_color "yellow" "  ✗ pip installation failed."
        INSTALL_METHODS_TRIED=$((INSTALL_METHODS_TRIED + 1))
    fi
fi

# Method 3: Try installing via pipx if methods 1 and 2 failed
if [ "$UV_INSTALLED" = false ]; then
    echo_color "blue" "  → Method 3/3: Trying installation via pipx..."
    # Check if pipx is installed, otherwise install it
    if ! command -v pipx &> /dev/null; then
        echo_color "blue" "    → pipx not found, installing pipx first..."
        pip3 install -q --break-system-packages pipx > /dev/null 2>&1
        python3 -m pipx ensurepath > /dev/null 2>&1
    fi
    
    # Try installing uv via pipx
    if command -v pipx &> /dev/null; then
        pipx install uv > /dev/null 2>&1
        if command -v uv &> /dev/null; then
            echo_color "green" "  ✓ uv successfully installed via pipx."
            UV_INSTALLED=true
        else
            echo_color "yellow" "  ✗ pipx installation failed."
            INSTALL_METHODS_TRIED=$((INSTALL_METHODS_TRIED + 1))
        fi
    else
        echo_color "yellow" "  ✗ Could not install pipx."
        INSTALL_METHODS_TRIED=$((INSTALL_METHODS_TRIED + 1))
    fi
fi

# Final check and user prompt if all methods failed
if [ "$UV_INSTALLED" = false ]; then
    echo_color "red" "All uv installation methods failed ($INSTALL_METHODS_TRIED/$INSTALL_METHODS_TOTAL)."
    echo_color "yellow" "Potential reasons:"
    echo_color "yellow" "  - Network connectivity issues"
    echo_color "yellow" "  - Missing build dependencies (rustc, cargo)"
    echo_color "yellow" "  - Insufficient permissions"
    
    echo "Do you want to continue installation using standard pip? (y/n)"
    read -r response
    if [[ "$response" != "y" ]]; then
        echo_color "red" "Installation aborted by user."
        exit 1
    fi
    echo_color "yellow" "Continuing installation with standard pip..."
else
    echo_color "green" "✓ uv package manager is ready to use."
fi

echo_color "green" "✓ Required packages installed."

# Step 4: Check USB/IP installation
CURRENT_STEP=$((CURRENT_STEP + 1))
progress_update $CURRENT_STEP $TOTAL_STEPS "Checking and configuring USB/IP..."

# Variable to track if components requiring reboot were installed
KERNEL_MODULES_INSTALLED=false

# Determine kernel version
echo_color "blue" "    → Determining kernel version..."
KERNEL_VERSION=$(uname -r)
KERNEL_MAJOR=$(echo $KERNEL_VERSION | cut -d. -f1)
KERNEL_MINOR=$(echo $KERNEL_VERSION | cut -d. -f2)
echo_color "blue" "    → Detected kernel version: $KERNEL_VERSION"

# Install appropriate linux-tools package for the specific kernel version
echo_color "blue" "    → Installing Linux Tools for current kernel..."
if apt-cache show linux-tools-$KERNEL_VERSION &> /dev/null; then
    echo_color "blue" "    → Found package linux-tools-$KERNEL_VERSION"
    apt-get install -y linux-tools-$KERNEL_VERSION > /dev/null 2>&1
    KERNEL_MODULES_INSTALLED=true
elif apt-cache show linux-tools-$(uname -r | cut -d- -f1) &> /dev/null; then
    KERNEL_BASE_VERSION=$(uname -r | cut -d- -f1)
    echo_color "blue" "    → Found package linux-tools-$KERNEL_BASE_VERSION"
    apt-get install -y linux-tools-$KERNEL_BASE_VERSION > /dev/null 2>&1
    KERNEL_MODULES_INSTALLED=true
else
    echo_color "yellow" "    → No specific linux-tools package found for your kernel"
    echo_color "blue" "    → Installing generic linux-tools-generic package..."
    apt-get install -y linux-tools-generic > /dev/null 2>&1
    KERNEL_MODULES_INSTALLED=true
fi

# Create symlink if necessary
if ! command -v usbip &> /dev/null; then
    echo_color "blue" "    → Searching for usbip utility in the system..."
    USBIP_PATH=$(find /usr/lib/linux-tools -name "usbip" | head -n 1)
    if [ -n "$USBIP_PATH" ]; then
        echo_color "blue" "    → Creating symbolic link to usbip..."
        ln -sf "$USBIP_PATH" /usr/local/bin/usbip
    else
        echo_color "yellow" "    → Could not find USB/IP utility. Trying other methods..."
        echo_color "blue" "    → Attempting direct installation of USB/IP packages..."
        apt-get install -y linux-tools-generic hwdata usbip > /dev/null 2>&1
    fi
fi

# Check if USB/IP was successfully installed
if ! command -v usbip &> /dev/null; then
    if [ "$ARCH" == "armv7"* ]; then
        echo_color "yellow" "⚠ On ARMv7, additional USB/IP installation steps may be required."
        echo_color "yellow" "   It is recommended to use the install_arm.sh script for this architecture."
        
        echo "Do you want to continue installation without USB/IP? (y/n)"
        read -r response
        if [[ "$response" != "y" ]]; then
            echo_color "blue" "Installation aborted. Use install_arm.sh script"
            exit 0
        fi
    fi
    
    echo_color "red" "⚠ Failed to install USB/IP. Continuing installation without USB/IP."
    echo_color "yellow" "You will need to install USB/IP manually later."
else
    echo_color "green" "✓ USB/IP successfully installed."
fi

# Step 5: Load kernel modules
CURRENT_STEP=$((CURRENT_STEP + 1))
progress_update $CURRENT_STEP $TOTAL_STEPS "Configuring kernel modules for USB/IP..."

# Add modules to autoload
MODULES_ADDED=false
if ! grep -q "usbip-core" /etc/modules; then
    echo "usbip-core" >> /etc/modules
    MODULES_ADDED=true
fi
if ! grep -q "usbip-host" /etc/modules; then
    echo "usbip-host" >> /etc/modules
    MODULES_ADDED=true
fi
if ! grep -q "vhci-hcd" /etc/modules; then
    echo "vhci-hcd" >> /etc/modules
    MODULES_ADDED=true
fi

# Try loading modules
MODULES_LOADED=true
echo_color "blue" "    → Loading module usbip-core..."
modprobe usbip-core 2>/dev/null || {
    echo_color "yellow" "    ⚠ Failed to load module usbip-core"
    MODULES_LOADED=false
}

echo_color "blue" "    → Loading module usbip-host..."
modprobe usbip-host 2>/dev/null || {
    echo_color "yellow" "    ⚠ Failed to load module usbip-host"
    MODULES_LOADED=false
}

echo_color "blue" "    → Loading module vhci-hcd..."
modprobe vhci-hcd 2>/dev/null || {
    echo_color "yellow" "    ⚠ Failed to load module vhci-hcd"
    MODULES_LOADED=false
}

# If modules were added to autoload or new kernel components installed,
# and not all modules loaded - a reboot is likely needed
if ([ "$MODULES_ADDED" = true ] || [ "$KERNEL_MODULES_INSTALLED" = true ]) && [ "$MODULES_LOADED" = false ]; then
    echo_color "red" ""
    echo_color "red" "⚠ WARNING: System reboot may be required"
    echo_color "red" "to fully activate USB/IP kernel modules!"
    echo_color "yellow" ""
    echo_color "yellow" "After rebooting, run this script again to complete installation."
    echo_color "yellow" "Reboot command: sudo reboot"
    echo_color "yellow" ""
    
    echo "Continue installation without rebooting? (y/n)"
    read -r response
    if [[ "$response" != "y" ]]; then
        echo_color "blue" "Installation paused. Please reboot the system and run the script again."
        exit 0
    fi
    
    echo_color "yellow" "Continuing installation. Some features may not work until reboot."
fi

echo_color "green" "✓ USB/IP modules configured."

# Step 6: Configure USB/IP daemon
CURRENT_STEP=$((CURRENT_STEP + 1))
progress_update $CURRENT_STEP $TOTAL_STEPS "Configuring USB/IP daemon..."

# Create systemd service for usbipd if it doesn't exist
if [ ! -f "/etc/systemd/system/usbipd.service" ]; then
    cat > /etc/systemd/system/usbipd.service << 'EOF'
[Unit]
Description=USB/IP daemon
After=network.target

[Service]
Type=simple
ExecStart=/usr/sbin/usbipd -D
Restart=on-failure

[Install]
WantedBy=multi-user.target
EOF

    systemctl daemon-reload
    systemctl enable usbipd
    systemctl start usbipd || echo_color "yellow" "Failed to start usbipd, check the path to the binary file"
fi

echo_color "green" "✓ USB/IP daemon configured."

# Step 7: Set up application directory
CURRENT_STEP=$((CURRENT_STEP + 1))
progress_update $CURRENT_STEP $TOTAL_STEPS "Creating application directory..."

APP_DIR="$USER_HOME/orange-usbip"
if [ ! -d "$APP_DIR" ]; then
    mkdir -p "$APP_DIR"
    chown $REAL_USER:$REAL_USER "$APP_DIR"
fi

# Clone repository
cd "$APP_DIR"
if [ -d ".git" ]; then
    echo "Updating existing repository..."
    sudo -u $REAL_USER git pull
else
    echo "Cloning repository..."
    sudo -u $REAL_USER git clone https://github.com/maksfaktor/usbip-web.git .
fi

echo_color "green" "✓ Repository successfully downloaded to $APP_DIR."

# Step 8: Set up Python virtual environment
CURRENT_STEP=$((CURRENT_STEP + 1))
progress_update $CURRENT_STEP $TOTAL_STEPS "Setting up Python virtual environment..."

cd "$APP_DIR"
if [ ! -d "venv" ]; then
    sudo -u $REAL_USER python3 -m venv venv
fi

# Install dependencies using uv or pip
if command -v uv &> /dev/null; then
    echo_color "blue" "Using uv for fast dependency installation..."
    sudo -u $REAL_USER bash -c "
    source venv/bin/activate
    uv pip install --upgrade pip
    uv pip install -r requirements-deploy.txt
    deactivate
    "
else
    echo_color "yellow" "Using standard pip for dependency installation..."
    sudo -u $REAL_USER bash -c "
    source venv/bin/activate
    pip install --upgrade pip
    pip install -r requirements-deploy.txt
    deactivate
    "
fi

echo_color "green" "✓ Python virtual environment configured."

# Step 9: Create systemd service
CURRENT_STEP=$((CURRENT_STEP + 1))
progress_update $CURRENT_STEP $TOTAL_STEPS "Creating systemd service..."

cat > /etc/systemd/system/orange-usbip.service << EOF
[Unit]
Description=Orange USBIP Web Interface
After=network.target usbipd.service

[Service]
User=$REAL_USER
Group=$REAL_USER
WorkingDirectory=$APP_DIR
ExecStart=$APP_DIR/venv/bin/gunicorn --bind 0.0.0.0:5000 main:app
Restart=on-failure
Environment="PATH=$APP_DIR/venv/bin:/usr/local/sbin:/usr/local/bin:/usr/sbin:/usr/bin:/sbin:/bin"

[Install]
WantedBy=multi-user.target
EOF

systemctl daemon-reload
systemctl enable orange-usbip
systemctl start orange-usbip

echo_color "green" "✓ Systemd service created and started."

# Step 10: Configure access to USB/IP via sudo
CURRENT_STEP=$((CURRENT_STEP + 1))
progress_update $CURRENT_STEP $TOTAL_STEPS "Configuring access rights for USB/IP..."

# Configure sudo for user
if [ ! -f "/etc/sudoers.d/usbip-$REAL_USER" ]; then
    cat > "/etc/sudoers.d/usbip-$REAL_USER" << EOF
$REAL_USER ALL=(ALL) NOPASSWD: /usr/sbin/usbip
$REAL_USER ALL=(ALL) NOPASSWD: /usr/lib/linux-tools/*/usbip
$REAL_USER ALL=(ALL) NOPASSWD: /usr/local/bin/usbip
EOF
    chmod 440 "/etc/sudoers.d/usbip-$REAL_USER"
fi

echo_color "green" "✓ Access rights configured."

# Check if service started
if systemctl is-active --quiet orange-usbip; then
    # Get IP address
    IP_ADDR=$(hostname -I | awk '{print $1}')
    
    echo_color "green" "===================================================="
    echo_color "green" "  Orange USBIP Installation Successfully Completed! "
    echo_color "green" "===================================================="
    echo ""
    echo_color "yellow" "Service available at: http://$IP_ADDR:5000"
    echo_color "yellow" "Login: admin"
    echo_color "yellow" "Password: admin"
    echo ""
    echo_color "red" "IMPORTANT: Change your password after first login!"
    echo ""
    echo_color "blue" "Service management:"
    echo " - Restart:      sudo systemctl restart orange-usbip"
    echo " - Stop:         sudo systemctl stop orange-usbip"
    echo " - Status:       sudo systemctl status orange-usbip"
    echo " - Logs:         sudo journalctl -u orange-usbip"
    echo ""
else
    echo_color "red" "Service failed to start. Check logs: sudo journalctl -u orange-usbip"
    exit 1
fi

exit 0