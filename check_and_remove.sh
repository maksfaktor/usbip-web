#!/bin/bash

# Orange USB/IP Service and Application Removal Script
# Interactive script to check and remove Orange USB/IP service and application

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Function to print colored output
print_color() {
    local color=$1
    local message=$2
    echo -e "${color}${message}${NC}"
}

# Function to print header
print_header() {
    print_color $GREEN "========================================================"
    print_color $GREEN "  Orange USB/IP Service and Application Removal Tool   "
    print_color $GREEN "========================================================"
    echo ""
}

# Function to check if script is run as root
check_root() {
    if [ "$EUID" -ne 0 ]; then
        print_color $RED "Error: This script must be run with superuser privileges (sudo)."
        echo "Examples:"
        echo "  sudo bash -c \"\$(curl -fsSL https://raw.githubusercontent.com/maksfaktor/usbip-web/main/check_and_remove.sh)\""
        echo "  sudo ./check_and_remove.sh"
        exit 1
    fi
    

}

# Function to check service status
check_service() {
    local service_name=$1
    local service_file="/etc/systemd/system/${service_name}.service"
    local system_service_file="/lib/systemd/system/${service_name}.service"
    
    local service_exists=false
    local service_active=false
    local service_enabled=false
    
    # Check if service files exist
    if [ -f "$service_file" ] || [ -f "$system_service_file" ]; then
        service_exists=true
    fi
    
    # Check if service is active
    if systemctl is-active --quiet "$service_name" 2>/dev/null; then
        service_active=true
    fi
    
    # Check if service is enabled
    if systemctl is-enabled --quiet "$service_name" 2>/dev/null; then
        service_enabled=true
    fi
    
    # Check if service is loaded (even if inactive) - use timeout for faster execution
    if timeout 5 systemctl list-unit-files 2>/dev/null | grep -q "^${service_name}.service"; then
        service_exists=true
    fi
    
    echo "$service_exists:$service_active:$service_enabled"
}

# Function to remove service
remove_service() {
    local service_name=$1
    
    print_color $YELLOW "Removing $service_name service..."
    
    # Stop the service if running
    if systemctl is-active --quiet "$service_name" 2>/dev/null; then
        print_color $BLUE "  → Stopping $service_name service..."
        systemctl stop "$service_name" 2>/dev/null || true
    fi
    
    # Disable the service if enabled
    if systemctl is-enabled --quiet "$service_name" 2>/dev/null; then
        print_color $BLUE "  → Disabling $service_name service..."
        systemctl disable "$service_name" 2>/dev/null || true
    fi
    
    # Remove service files
    local service_file="/etc/systemd/system/${service_name}.service"
    local system_service_file="/lib/systemd/system/${service_name}.service"
    
    if [ -f "$service_file" ]; then
        print_color $BLUE "  → Removing $service_file..."
        rm -f "$service_file"
    fi
    
    if [ -f "$system_service_file" ]; then
        print_color $BLUE "  → Removing $system_service_file..."
        rm -f "$system_service_file"
    fi
    
    # Reload systemd daemon
    print_color $BLUE "  → Reloading systemd daemon..."
    systemctl daemon-reload 2>/dev/null || true
    systemctl reset-failed 2>/dev/null || true
    
    print_color $GREEN "✓ $service_name service removed successfully"
}

# Function to check if directory exists and get its size
check_directory() {
    local dir_path=$1
    
    if [ -d "$dir_path" ]; then
        local size=$(du -sh "$dir_path" 2>/dev/null | cut -f1)
        echo "exists:$size"
    else
        echo "not_exists:"
    fi
}

# Function to remove directory
remove_directory() {
    local dir_path=$1
    local dir_name=$(basename "$dir_path")
    
    print_color $YELLOW "Removing $dir_name directory..."
    
    if [ -d "$dir_path" ]; then
        print_color $BLUE "  → Removing directory: $dir_path"
        rm -rf "$dir_path"
        print_color $GREEN "✓ $dir_name directory removed successfully"
    else
        print_color $YELLOW "  → Directory $dir_path does not exist"
    fi
}

# Function to get user confirmation
get_confirmation() {
    local prompt=$1
    local response
    
    while true; do
        echo -n "$prompt [y/N]: "
        read -r response
        case $response in
            [Yy]|[Yy][Ee][Ss]) return 0 ;;
            [Nn]|[Nn][Oo]|"") return 1 ;;
            *) print_color $RED "Please answer yes (y) or no (n)." ;;
        esac
    done
}

# Function to check for running processes
check_processes() {
    local processes_found=false
    
    # Check for usbipd processes
    if pgrep -f "usbipd" > /dev/null; then
        processes_found=true
        print_color $YELLOW "Found running usbipd processes:"
        ps aux | grep -v grep | grep usbipd | while read line; do
            print_color $BLUE "  → $line"
        done
    fi
    
    # Check for python processes running orange-usbip
    if pgrep -f "orange-usbip" > /dev/null; then
        processes_found=true
        print_color $YELLOW "Found running orange-usbip processes:"
        ps aux | grep -v grep | grep orange-usbip | while read line; do
            print_color $BLUE "  → $line"
        done
    fi
    
    # Check for gunicorn processes
    if pgrep -f "gunicorn.*main:app" > /dev/null; then
        processes_found=true
        print_color $YELLOW "Found running gunicorn processes (possibly orange-usbip):"
        ps aux | grep -v grep | grep "gunicorn.*main:app" | while read line; do
            print_color $BLUE "  → $line"
        done
    fi
    
    if [ "$processes_found" = true ]; then
        echo ""
        if get_confirmation "Would you like to terminate these processes?"; then
            print_color $YELLOW "Terminating processes..."
            pkill -f "usbipd" 2>/dev/null || true
            pkill -f "orange-usbip" 2>/dev/null || true
            pkill -f "gunicorn.*main:app" 2>/dev/null || true
            sleep 2
            print_color $GREEN "✓ Processes terminated"
        fi
    else
        print_color $GREEN "✓ No running processes found"
    fi
}

# Main function
main() {
    print_header
    
    # Check root privileges
    check_root
    
    print_color $BLUE "Checking for Orange USB/IP installation..."
    echo ""
    
    # Check for running processes
    print_color $BLUE "=== Checking for running processes ==="
    check_processes
    echo ""
    
    # Check orange-usbip service
    print_color $BLUE "=== Checking orange-usbip service ==="
    service_info=$(check_service "orange-usbip")
    IFS=':' read -r exists active enabled <<< "$service_info"
    
    if [ "$exists" = "true" ]; then
        print_color $YELLOW "Orange USB/IP service detected:"
        [ "$active" = "true" ] && print_color $BLUE "  → Status: ACTIVE" || print_color $BLUE "  → Status: INACTIVE"
        [ "$enabled" = "true" ] && print_color $BLUE "  → Auto-start: ENABLED" || print_color $BLUE "  → Auto-start: DISABLED"
        echo ""
        
        if get_confirmation "Would you like to remove the orange-usbip service?"; then
            remove_service "orange-usbip"
        else
            print_color $YELLOW "Skipping orange-usbip service removal"
        fi
    else
        print_color $GREEN "✓ No orange-usbip service found"
    fi
    echo ""
    
    # Check usbipd service (conflicting service)
    print_color $BLUE "=== Checking usbipd service ==="
    service_info=$(check_service "usbipd")
    IFS=':' read -r exists active enabled <<< "$service_info"
    
    if [ "$exists" = "true" ]; then
        print_color $YELLOW "USBIPD service detected:"
        [ "$active" = "true" ] && print_color $BLUE "  → Status: ACTIVE" || print_color $BLUE "  → Status: INACTIVE"
        [ "$enabled" = "true" ] && print_color $BLUE "  → Auto-start: ENABLED" || print_color $BLUE "  → Auto-start: DISABLED"
        echo ""
        
        if get_confirmation "Would you like to remove the usbipd service?"; then
            remove_service "usbipd"
        else
            print_color $YELLOW "Skipping usbipd service removal"
        fi
    else
        print_color $GREEN "✓ No usbipd service found"
    fi
    echo ""
    
    # Determine the real user (not sudo) - using same method as install script
    if [ -n "$SUDO_USER" ]; then
        REAL_USER=$SUDO_USER
    else
        REAL_USER=$(whoami)
    fi
    USER_HOME=$(eval echo ~$REAL_USER)
    APP_DIR="$USER_HOME/orange-usbip"
    
    # Check application directory
    print_color $BLUE "=== Checking application directory ==="
    dir_info=$(check_directory "$APP_DIR")
    IFS=':' read -r exists size <<< "$dir_info"
    
    if [ "$exists" = "exists" ]; then
        print_color $YELLOW "Orange USB/IP application directory found:"
        print_color $BLUE "  → Location: $APP_DIR"
        print_color $BLUE "  → Size: $size"
        echo ""
        
        if get_confirmation "Would you like to remove the application directory?"; then
            remove_directory "$APP_DIR"
        else
            print_color $YELLOW "Skipping application directory removal"
        fi
    else
        print_color $GREEN "✓ No application directory found at $APP_DIR"
    fi
    echo ""
    
    # Check for additional common locations
    print_color $BLUE "=== Checking additional locations ==="
    
    # Check /opt/orange-usbip
    if [ -d "/opt/orange-usbip" ]; then
        print_color $YELLOW "Found Orange USB/IP in /opt/orange-usbip"
        if get_confirmation "Would you like to remove /opt/orange-usbip?"; then
            remove_directory "/opt/orange-usbip"
        fi
    fi
    
    # Check /usr/local/orange-usbip
    if [ -d "/usr/local/orange-usbip" ]; then
        print_color $YELLOW "Found Orange USB/IP in /usr/local/orange-usbip"
        if get_confirmation "Would you like to remove /usr/local/orange-usbip?"; then
            remove_directory "/usr/local/orange-usbip"
        fi
    fi
    
    # Check for configuration files
    print_color $BLUE "=== Checking configuration files ==="
    config_found=false
    
    if [ -f "/etc/orange-usbip.conf" ]; then
        config_found=true
        print_color $YELLOW "Found configuration file: /etc/orange-usbip.conf"
    fi
    
    if [ -f "/etc/default/orange-usbip" ]; then
        config_found=true
        print_color $YELLOW "Found configuration file: /etc/default/orange-usbip"
    fi
    
    if [ "$config_found" = true ]; then
        if get_confirmation "Would you like to remove configuration files?"; then
            [ -f "/etc/orange-usbip.conf" ] && rm -f "/etc/orange-usbip.conf"
            [ -f "/etc/default/orange-usbip" ] && rm -f "/etc/default/orange-usbip"
            print_color $GREEN "✓ Configuration files removed"
        fi
    else
        print_color $GREEN "✓ No configuration files found"
    fi
    
    echo ""
    print_color $GREEN "========================================================"
    print_color $GREEN "  Orange USB/IP removal check completed                 "
    print_color $GREEN "========================================================"
    
    # Final status
    print_color $BLUE "Final system status:"
    
    # Re-check services
    service_info=$(check_service "orange-usbip")
    IFS=':' read -r exists active enabled <<< "$service_info"
    if [ "$exists" = "true" ]; then
        print_color $YELLOW "  → orange-usbip service: STILL PRESENT"
    else
        print_color $GREEN "  → orange-usbip service: REMOVED"
    fi
    
    service_info=$(check_service "usbipd")
    IFS=':' read -r exists active enabled <<< "$service_info"
    if [ "$exists" = "true" ]; then
        print_color $YELLOW "  → usbipd service: STILL PRESENT"
    else
        print_color $GREEN "  → usbipd service: REMOVED"
    fi
    
    # Re-check directories
    if [ -d "$APP_DIR" ]; then
        print_color $YELLOW "  → Application directory: STILL PRESENT ($APP_DIR)"
    else
        print_color $GREEN "  → Application directory: REMOVED"
    fi
    
    # Check processes one more time
    if pgrep -f "usbipd\|orange-usbip\|gunicorn.*main:app" > /dev/null; then
        print_color $YELLOW "  → Related processes: STILL RUNNING"
    else
        print_color $GREEN "  → Related processes: NONE FOUND"
    fi
    
    echo ""
    print_color $GREEN "Script completed successfully!"
}

# Run main function
main "$@"