#!/bin/bash

# Orange USBIP - Fix Gunicorn installation
# This script fixes missing gunicorn issue

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

echo_color "green" "===================================================="
echo_color "green" "  Orange USBIP - Gunicorn Fix Script               "
echo_color "green" "===================================================="
echo ""

# Check if script is run with root privileges
if [ "$EUID" -ne 0 ]; then
    echo_color "red" "Error: this script must be run with superuser privileges (sudo)."
    echo "Run: sudo $0"
    exit 1
fi

# Determine the real user
if [ -n "$SUDO_USER" ]; then
    REAL_USER=$SUDO_USER
else
    REAL_USER=$(whoami)
fi
USER_HOME=$(eval echo ~$REAL_USER)
APP_DIR="$USER_HOME/orange-usbip"

echo_color "blue" "[1/4] Checking installation directory..."

if [ ! -d "$APP_DIR" ]; then
    echo_color "red" "✗ Orange USBIP directory not found at $APP_DIR"
    echo_color "yellow" "Please run the installation script first:"
    echo "sudo bash -c \"\$(curl -fsSL https://raw.githubusercontent.com/maksfaktor/usbip-web/main/install_debian.sh)\""
    exit 1
fi

cd "$APP_DIR"
echo_color "green" "✓ Found installation at $APP_DIR"

echo_color "blue" "[2/4] Checking virtual environment..."

if [ ! -d "venv" ]; then
    echo_color "yellow" "⚠ Virtual environment not found, creating..."
    sudo -u $REAL_USER python3 -m venv venv
    echo_color "green" "✓ Virtual environment created."
else
    echo_color "green" "✓ Virtual environment exists."
fi

echo_color "blue" "[3/4] Checking requirements-deploy.txt..."

if [ ! -f "requirements-deploy.txt" ]; then
    echo_color "yellow" "⚠ requirements-deploy.txt not found, downloading..."
    sudo -u $REAL_USER curl -fsSL https://raw.githubusercontent.com/maksfaktor/usbip-web/main/requirements-deploy.txt -o requirements-deploy.txt
    echo_color "green" "✓ Downloaded requirements-deploy.txt"
else
    echo_color "green" "✓ requirements-deploy.txt exists."
fi

echo_color "blue" "[4/4] Installing Python packages..."

# Try with uv first, fallback to pip
if command -v uv &> /dev/null || [ -f "$USER_HOME/.cargo/bin/uv" ]; then
    export PATH="$USER_HOME/.cargo/bin:$PATH"
    echo_color "blue" "Using uv for installation..."
    sudo -u $REAL_USER bash -c "
    source venv/bin/activate
    export PATH=\"$USER_HOME/.cargo/bin:\$PATH\"
    uv pip install --upgrade pip
    uv pip install -r requirements-deploy.txt
    deactivate
    " || {
        echo_color "yellow" "  ⚠ uv failed, using standard pip..."
        sudo -u $REAL_USER bash -c "
        source venv/bin/activate
        pip install --upgrade pip
        pip install -r requirements-deploy.txt
        deactivate
        "
    }
else
    echo_color "yellow" "Using standard pip..."
    sudo -u $REAL_USER bash -c "
    source venv/bin/activate
    pip install --upgrade pip
    pip install -r requirements-deploy.txt
    deactivate
    "
fi

echo ""
echo_color "blue" "Verifying gunicorn installation..."

sudo -u $REAL_USER bash -c "
source venv/bin/activate
if command -v gunicorn &> /dev/null; then
    echo -e '\033[0;32m✓ Gunicorn successfully installed!\033[0m'
    echo -e '\033[0;34mVersion: \033[0m\$(gunicorn --version)'
else
    echo -e '\033[0;31m✗ Gunicorn installation failed\033[0m'
    exit 1
fi
deactivate
"

if [ $? -eq 0 ]; then
    echo ""
    echo_color "green" "===================================================="
    echo_color "green" "  Gunicorn has been successfully installed!        "
    echo_color "green" "===================================================="
    echo ""
    echo_color "blue" "Restarting orange-usbip service..."
    
    systemctl restart orange-usbip
    
    if systemctl is-active --quiet orange-usbip; then
        echo_color "green" "✓ Service restarted successfully!"
    else
        echo_color "yellow" "⚠ Service restart failed. Check logs with:"
        echo "sudo journalctl -u orange-usbip -n 50"
    fi
    
    echo ""
    echo_color "blue" "You can now use the application!"
else
    echo ""
    echo_color "red" "===================================================="
    echo_color "red" "  Installation failed. Please try manual install:  "
    echo_color "red" "===================================================="
    echo ""
    echo "cd $APP_DIR"
    echo "source venv/bin/activate"
    echo "pip install --upgrade pip"
    echo "pip install -r requirements-deploy.txt"
    exit 1
fi
