#!/bin/bash

# Orange USBIP - Automatic installation script for ARM devices (Raspberry Pi, Orange Pi)
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
echo_color "green" "  Orange USBIP Automatic Installation for ARM       "
echo_color "green" "===================================================="
echo ""
echo_color "yellow" "This script will set up the USB/IP server and client on your device."
echo ""

TOTAL_STEPS=10
CURRENT_STEP=0

# Step 1: Check architecture
CURRENT_STEP=$((CURRENT_STEP + 1))
progress_update $CURRENT_STEP $TOTAL_STEPS "Checking system architecture..."

ARCH=$(uname -m)
if [[ "$ARCH" != arm* ]] && [[ "$ARCH" != "aarch"* ]]; then
    echo_color "red" "Architecture $ARCH is not ARM. Use the install_debian.sh script for other architectures."
    exit 1
fi

echo_color "green" "✓ Architecture $ARCH is compatible."

# Step 2: Update system
CURRENT_STEP=$((CURRENT_STEP + 1))
progress_update $CURRENT_STEP $TOTAL_STEPS "Updating package list..."

apt-get update -qq
echo_color "green" "✓ Repositories updated."

# Step 3: Install required dependencies
CURRENT_STEP=$((CURRENT_STEP + 1))
progress_update $CURRENT_STEP $TOTAL_STEPS "Installing required packages..."

apt-get install -y git python3 python3-pip python3-venv usbutils linux-tools-generic build-essential libnl-3-dev libnl-genl-3-dev curl > /dev/null 2>&1

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

# Step 3.1: Check USB/IP installation
echo_color "blue" "[$CURRENT_STEP/$TOTAL_STEPS] Checking and configuring USB/IP..."

# Variable to track if components requiring reboot were installed
KERNEL_MODULES_INSTALLED=false

if ! command -v usbip &> /dev/null; then
    echo_color "yellow" "USB/IP not found. Installing..."
    
    # Clone USB/IP tools repository (for ARM compatibility)
    cd /tmp
    if [ -d "linux-tools-usbip" ]; then
        rm -rf linux-tools-usbip
    fi
    
    echo_color "blue" "    → Downloading USB/IP source code..."
    git clone https://github.com/masahir0y/linux-tools-usbip.git > /dev/null 2>&1 || {
        echo_color "red" "Failed to download USB/IP source code. Check your internet connection."
        exit 1
    }
    
    echo_color "blue" "    → Compiling USB/IP (this may take some time)..."
    cd linux-tools-usbip
    make > /dev/null 2>&1 || {
        echo_color "red" "Error compiling USB/IP."
        echo_color "yellow" "You may need to install additional packages: build-essential, libnl-3-dev, libnl-genl-3-dev"
        exit 1
    }
    
    echo_color "blue" "    → Installing USB/IP..."
    make install > /dev/null 2>&1 || {
        echo_color "red" "Error installing USB/IP."
        exit 1
    }
    
    # Check again
    if ! command -v usbip &> /dev/null; then
        echo_color "red" "Failed to install USB/IP. Try installing manually."
        exit 1
    fi
    
    KERNEL_MODULES_INSTALLED=true
fi

echo_color "green" "✓ USB/IP successfully installed."

# Step 4: Load kernel modules
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
    echo_color "yellow" "After reboot, run this script again to complete installation."
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

# Step 5: Configure USB/IP daemon
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
    systemctl start usbipd
fi

echo_color "green" "✓ USB/IP daemon configured and started."

# Step 6: Set up application directory
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

# Step 7: Set up Python virtual environment
CURRENT_STEP=$((CURRENT_STEP + 1))
progress_update $CURRENT_STEP $TOTAL_STEPS "Setting up Python virtual environment..."

cd "$APP_DIR"
if [ ! -d "venv" ]; then
    sudo -u $REAL_USER python3 -m venv venv
fi

# Install dependencies using uv or pip
if command -v uv &> /dev/null || [ -f "$HOME/.cargo/bin/uv" ]; then
    # Make sure uv is in PATH for the installation process
    export PATH="$HOME/.cargo/bin:$PATH"
    echo_color "blue" "Using uv for fast dependency installation..."
    sudo -u $REAL_USER bash -c "
    source venv/bin/activate
    # Ensure uv is in PATH for the user as well
    export PATH=\"$HOME/.cargo/bin:\$PATH\"
    uv pip install --upgrade pip
    uv pip install -r requirements-deploy.txt
    deactivate
    " || {
        echo_color "yellow" "  ⚠ uv installation failed, falling back to standard pip..."
        sudo -u $REAL_USER bash -c "
        source venv/bin/activate
        pip install --upgrade pip
        pip install -r requirements-deploy.txt
        deactivate
        "
    }
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

# Step 8: Create user for running the service (if it doesn't exist)
CURRENT_STEP=$((CURRENT_STEP + 1))
progress_update $CURRENT_STEP $TOTAL_STEPS "Configuring service user..."

if ! id "usbip" &>/dev/null; then
    useradd -r -s /bin/false -d /nonexistent usbip
fi

# Configure sudo for usbip user
if [ ! -f "/etc/sudoers.d/usbip" ]; then
    cat > /etc/sudoers.d/usbip << 'EOF'
usbip ALL=(ALL) NOPASSWD: /usr/sbin/usbip
usbip ALL=(ALL) NOPASSWD: /usr/lib/linux-tools/*/usbip
EOF
    chmod 440 /etc/sudoers.d/usbip
fi

echo_color "green" "✓ User and access rights configured."

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

# Step 10: Finalize installation
CURRENT_STEP=$((CURRENT_STEP + 1))
progress_update $CURRENT_STEP $TOTAL_STEPS "Checking functionality..."

# Wait a few seconds for the service to start
sleep 5

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