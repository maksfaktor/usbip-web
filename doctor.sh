#!/bin/bash
#####################################################################
# Orange USBIP Diagnostic Script (doctor.sh)
# 
# This script helps diagnose common issues with USB/IP connections,
# checking system configuration, services, and network connectivity.
# 
# Usage: sudo ./doctor.sh
# 
# Author: Orange USBIP Team
# License: MIT
# Repository: https://github.com/maksfaktor/usbip-web
# 
# Created: May 2025
# Last Updated: May 24, 2025
#####################################################################

# Functions for colored output
RED='\033[0;31m'    # Used for errors and critical issues
GREEN='\033[0;32m'  # Used for success messages and working components
YELLOW='\033[0;33m' # Used for warnings and recommendations
BLUE='\033[0;34m'   # Used for headers and informational sections
NC='\033[0m'        # No Color - resets text formatting

# Function for colored text output
# Parameters:
#   $1: color name (red|green|yellow|blue)
#   $2: message to display
echo_color() {
    color=$1
    message=$2
    case "$color" in
        "red") echo -e "${RED}$message${NC}" ;;
        "green") echo -e "${GREEN}$message${NC}" ;;
        "yellow") echo -e "${YELLOW}$message${NC}" ;;
        "blue") echo -e "${BLUE}$message${NC}" ;;
        *) echo "$message" ;;
    esac
}

# Function to check command execution status and display appropriate message
# Parameters:
#   $1: Success message to display
#   $2: (Optional) Recommendation if check fails
check_status() {
    if [ $? -eq 0 ]; then
        echo_color "green" "✓ $1"
    else
        echo_color "red" "✗ $1"
        if [ ! -z "$2" ]; then
            echo_color "yellow" "  → $2"
        fi
    fi
}

# Function to display section header with formatting
# Parameters:
#   $1: Header text
show_header() {
    echo ""
    echo_color "blue" "===================================================="
    echo_color "blue" "  $1"
    echo_color "blue" "===================================================="
    echo ""
}

# Function to check if a command exists in the system
# Parameters:
#   $1: Command name to check
check_command() {
    command -v $1 > /dev/null 2>&1
    check_status "Command $1 is available" "Please install package containing $1 command"
}

#####################################################################
# Main diagnostic routines
#####################################################################

# Clear the screen and show welcome message
clear
show_header "Orange USBIP Diagnostic Tool"

#####################################################################
# Section 1: Operating System Check
# Displays information about the current operating system
#####################################################################
show_header "1. Operating System Check"
echo "OS Name: $(uname -s)"
echo "OS Version: $(uname -r)"
echo "Architecture: $(uname -m)"

#####################################################################
# Section 2: Required Commands Check
# Verifies all necessary commands are available in the system
#####################################################################
show_header "2. Required Commands Check"
check_command "usbip"     # Main USB/IP command
check_command "gunicorn"  # Web server for the application
check_command "python3"   # Required for running the application
check_command "systemctl" # For service management
check_command "nc"        # For network connectivity tests

#####################################################################
# Section 3: Services Check
# Checks if usbipd and orange-usbip services are running
#####################################################################
show_header "3. Services Check"

# Check if usbipd service is running via systemd
echo "Checking usbipd service:"
systemctl is-active --quiet usbipd
if [ $? -eq 0 ]; then
    echo_color "green" "✓ usbipd service is running"
else
    echo_color "red" "✗ usbipd service is not running"
    echo_color "yellow" "  → Searching for usbipd executable..."
    
    # If service is not running, try to find the executable manually
    USBIPD_PATH=$(find /usr -name "usbipd" -type f -executable 2>/dev/null | head -1)
    if [ -z "$USBIPD_PATH" ]; then
        echo_color "red" "  → usbipd executable not found"
    else
        echo_color "green" "  → Found usbipd executable: $USBIPD_PATH"
        echo_color "yellow" "  → Checking for running usbipd process..."
        
        # Check if usbipd is running as a standalone process
        ps aux | grep -v grep | grep -q usbipd
        if [ $? -eq 0 ]; then
            echo_color "green" "  → usbipd process is running"
        else
            echo_color "red" "  → usbipd process is not running"
            echo_color "yellow" "  → Recommended: start usbipd manually: sudo $USBIPD_PATH -D"
        fi
    fi
fi

# Check if orange-usbip service is running
echo "Checking Orange USBIP service:"
systemctl is-active --quiet orange-usbip
if [ $? -eq 0 ]; then
    echo_color "green" "✓ orange-usbip service is running"
else
    echo_color "red" "✗ orange-usbip service is not running"
    echo_color "yellow" "  → Recommended: start service: sudo systemctl start orange-usbip"
fi

#####################################################################
# Section 4: Kernel Modules Check
# Verifies if required kernel modules are loaded
#####################################################################
show_header "4. Kernel Modules Check"

# Check usbip-core module (required for basic USB/IP functionality)
echo "Checking usbip-core module:"
lsmod | grep -q usbip_core
check_status "usbip-core module is loaded" "Load module: sudo modprobe usbip-core"

# Check usbip-host module (required for sharing local devices)
echo "Checking usbip-host module:"
lsmod | grep -q usbip_host
check_status "usbip-host module is loaded" "Load module: sudo modprobe usbip-host"

# Check vhci-hcd module (required for attaching remote devices)
echo "Checking vhci-hcd module:"
lsmod | grep -q vhci_hcd
check_status "vhci-hcd module is loaded" "Load module: sudo modprobe vhci-hcd"

#####################################################################
# Section 5: Open Ports Check
# Checks if the required network ports are open and listening
#####################################################################
show_header "5. Open Ports Check"

# Check if usbipd port (3240) is listening
echo "Checking port 3240 (usbipd):"
netstat -tuln | grep -q ":3240 "
if [ $? -eq 0 ]; then
    echo_color "green" "✓ Port 3240 is listening"
else
    echo_color "red" "✗ Port 3240 is not listening"
    echo_color "yellow" "  → usbipd service is not running or not listening on port"
    echo_color "yellow" "  → Recommended: restart usbipd service: sudo systemctl restart usbipd"
fi

# Check if web interface port (5000) is listening
echo "Checking port 5000 (Orange USBIP Web):"
netstat -tuln | grep -q ":5000 "
if [ $? -eq 0 ]; then
    echo_color "green" "✓ Port 5000 is listening"
else
    echo_color "red" "✗ Port 5000 is not listening"
    echo_color "yellow" "  → Orange USBIP Web interface is not running"
    echo_color "yellow" "  → Recommended: restart orange-usbip service"
fi

#####################################################################
# Section 6: Firewall Check
# Verifies if firewall settings allow USB/IP traffic
#####################################################################
show_header "6. Firewall Check"

# Check UFW (Uncomplicated Firewall) if installed
if command -v ufw > /dev/null 2>&1; then
    echo "UFW Status:"
    sudo ufw status | grep -q "Status: active"
    if [ $? -eq 0 ]; then
        echo_color "yellow" "UFW is active, checking rules for ports 3240 and 5000:"
        
        # Check if port 3240 is allowed in UFW
        sudo ufw status | grep -q "3240"
        if [ $? -eq 0 ]; then
            echo_color "green" "✓ Port 3240 is allowed in UFW"
        else
            echo_color "red" "✗ Port 3240 is not allowed in UFW"
            echo_color "yellow" "  → Recommended: allow port: sudo ufw allow 3240/tcp"
        fi
        
        # Check if port 5000 is allowed in UFW
        sudo ufw status | grep -q "5000"
        if [ $? -eq 0 ]; then
            echo_color "green" "✓ Port 5000 is allowed in UFW"
        else
            echo_color "red" "✗ Port 5000 is not allowed in UFW"
            echo_color "yellow" "  → Recommended: allow port: sudo ufw allow 5000/tcp"
        fi
    else
        echo_color "green" "UFW is inactive, ports are not blocked"
    fi
else
    # If UFW is not installed, check iptables directly
    echo_color "yellow" "UFW is not installed, checking iptables:"
    sudo iptables -L INPUT -n | grep -q "3240"
    if [ $? -eq 0 ]; then
        echo_color "green" "✓ Port 3240 is allowed in iptables"
    else
        echo_color "yellow" "Port 3240 might be blocked in iptables"
        echo_color "yellow" "  → Recommended: allow port: sudo iptables -I INPUT -p tcp --dport 3240 -j ACCEPT"
    fi
fi

#####################################################################
# Section 7: Published Devices Check
# Checks for available and published USB devices
#####################################################################
show_header "7. Published Devices Check"

# Try to list available USB devices
sudo usbip list -l > /dev/null 2>&1
if [ $? -eq 0 ]; then
    # List local USB devices
    echo "Local USB devices:"
    DEVICES=$(sudo usbip list -l | grep -c "busid")
    if [ $DEVICES -gt 0 ]; then
        echo_color "green" "✓ Found $DEVICES devices"
        echo ""
        sudo usbip list -l | grep -A 1 "busid" | grep -v "\-\-" | sed 's/^/  /'
    else
        echo_color "yellow" "✗ No USB devices found"
    fi
    
    # List published (bound) devices
    echo ""
    echo "Published devices:"
    PUBLISHED=$(sudo usbip port | grep -c "usbip")
    if [ $PUBLISHED -gt 0 ]; then
        echo_color "green" "✓ Found $PUBLISHED published devices"
        echo ""
        sudo usbip port | grep -A 1 "Port" | grep -v "\-\-" | sed 's/^/  /'
    else
        echo_color "yellow" "✗ No published devices"
        echo_color "yellow" "  → To publish a device use: sudo usbip bind -b <busid>"
    fi
else
    echo_color "red" "✗ Failed to get USB devices list"
    echo_color "yellow" "  → usbip command might not be available or doesn't have proper permissions"
fi

#####################################################################
# Section 8: Network Interfaces Check
# Displays information about network interfaces
#####################################################################
show_header "8. Network Interfaces Check"

# Check for network interfaces using 'ip' command (modern) or fallback to 'ifconfig'
if command -v ip > /dev/null 2>&1; then
    echo "Available network interfaces:"
    ip -br addr show | grep -v "lo" | awk '{print "  " $1 ": " $3}'
    
    echo ""
    echo "Default routes:"
    ip route | grep default | sed 's/^/  /'
else
    echo_color "yellow" "ip command not found, using ifconfig"
    ifconfig | grep -E "inet|eth|wlan" | grep -v "inet6" | sed 's/^/  /'
fi

#####################################################################
# Section 9: Network Connection Test
# Tests connectivity to a remote USB/IP server
#####################################################################
show_header "9. Network Connection Test"
echo "Enter remote server IP address to test (or leave empty to skip):"
read remote_ip

if [ ! -z "$remote_ip" ]; then
    # Test basic connectivity with ping
    echo "Testing connectivity to $remote_ip via ping:"
    ping -c 3 $remote_ip > /dev/null 2>&1
    check_status "Server $remote_ip is reachable via ping" "Check network connection and firewall settings"
    
    # Test if USB/IP port is accessible
    echo "Testing port 3240 on $remote_ip:"
    nc -z -w 5 $remote_ip 3240 > /dev/null 2>&1
    check_status "Port 3240 on $remote_ip is accessible" "Make sure usbipd is running on remote server and port 3240 is allowed"
    
    # Test USB/IP connection and list remote devices
    echo "Testing connection to remote server via usbip:"
    sudo usbip list -r $remote_ip > /dev/null 2>&1
    if [ $? -eq 0 ]; then
        echo_color "green" "✓ Successfully connected to server $remote_ip"
        echo ""
        echo "Available devices on server $remote_ip:"
        sudo usbip list -r $remote_ip | grep -A 1 "busid" | grep -v "\-\-" | sed 's/^/  /'
    else
        echo_color "red" "✗ Failed to get devices list from server $remote_ip"
        echo_color "yellow" "  → Make sure that on remote server:"
        echo_color "yellow" "    1. usbipd service is running"
        echo_color "yellow" "    2. There are published devices"
        echo_color "yellow" "    3. Connections to port 3240 are allowed"
    fi
fi

#####################################################################
# Conclusion
#####################################################################
show_header "Diagnostics Complete"
echo "If you encountered any issues, please refer to documentation or support forum."
echo "For more information: https://github.com/maksfaktor/usbip-web"
echo ""