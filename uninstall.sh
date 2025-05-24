#!/bin/bash

# Colors for pretty output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Application info
APP_NAME="OrangeUSB Web Interface"
APP_DIR="/opt/orangeusb"
SERVICE_NAME="orange-usbip"
SUDOERS_FILE="/etc/sudoers.d/usbip-"
BACKUP_DIR="/var/backups/orangeusb"

# Print colored step message
print_step() {
    echo -e "${BLUE}[*] $1${NC}"
}

# Print success message
print_success() {
    echo -e "${GREEN}[✓] $1${NC}"
}

# Print warning message
print_warning() {
    echo -e "${YELLOW}[!] $1${NC}"
}

# Print error message
print_error() {
    echo -e "${RED}[✗] $1${NC}"
}

# Check if running as root
if [[ $EUID -ne 0 ]]; then
    print_error "This script must be run as root (sudo)."
    exit 1
fi

# Function to create backup of settings and database
backup_settings() {
    print_step "Creating backup of settings and database..."
    
    # Create timestamp for backup
    TIMESTAMP=$(date +"%Y%m%d_%H%M%S")
    BACKUP_PATH="${BACKUP_DIR}/${TIMESTAMP}"
    
    # Create backup directory
    mkdir -p "$BACKUP_PATH"
    
    # Backup database
    if [ -f "${APP_DIR}/usbip_web.db" ]; then
        cp "${APP_DIR}/usbip_web.db" "${BACKUP_PATH}/usbip_web.db"
        print_success "Database backup created at ${BACKUP_PATH}/usbip_web.db"
    else
        print_warning "Database file not found, skipping database backup."
    fi
    
    # Backup configuration files
    if [ -d "${APP_DIR}" ]; then
        # Create a tarball of the application directory
        tar -czf "${BACKUP_PATH}/orangeusb_config.tar.gz" -C "${APP_DIR}" .
        print_success "Configuration backup created at ${BACKUP_PATH}/orangeusb_config.tar.gz"
    else
        print_warning "Application directory not found, skipping configuration backup."
    fi
    
    print_success "Backup completed. All backups stored in: ${BACKUP_PATH}"
}

# Function to uninstall the application
remove_application() {
    print_step "Stopping and removing systemd service..."
    
    # Stop and disable the service
    systemctl stop ${SERVICE_NAME} 2>/dev/null
    systemctl disable ${SERVICE_NAME} 2>/dev/null
    
    # Remove service file
    if [ -f "/etc/systemd/system/${SERVICE_NAME}.service" ]; then
        rm "/etc/systemd/system/${SERVICE_NAME}.service"
        print_success "Service file removed."
    else
        print_warning "Service file not found, skipping."
    fi
    
    # Reload systemd
    systemctl daemon-reload
    
    # Remove sudoers file
    print_step "Removing sudoers configuration..."
    
    # Get current user
    CURRENT_USER=${SUDO_USER:-$(whoami)}
    
    if [ -f "${SUDOERS_FILE}${CURRENT_USER}" ]; then
        rm "${SUDOERS_FILE}${CURRENT_USER}"
        print_success "Sudoers configuration removed."
    else
        print_warning "Sudoers configuration not found, skipping."
    fi
    
    # Remove application files
    print_step "Removing application files..."
    
    if [ -d "$APP_DIR" ]; then
        rm -rf "$APP_DIR"
        print_success "Application files removed."
    else
        print_warning "Application directory not found, skipping."
    fi
    
    print_success "Uninstallation completed."
}

# Main uninstall function
uninstall_application() {
    echo "============================================================"
    echo "           ${APP_NAME} Uninstaller                          "
    echo "============================================================"
    
    # Ask for confirmation
    read -p "Are you sure you want to uninstall ${APP_NAME}? [y/N] " -n 1 -r
    echo
    
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        print_warning "Uninstallation cancelled."
        exit 0
    fi
    
    # Create backup before uninstalling
    backup_settings
    
    # Remove the application
    remove_application
    
    echo
    print_success "${APP_NAME} has been successfully uninstalled."
    print_warning "Note: USB/IP related packages (usbip, usbutils, etc.) were not removed."
    print_warning "If you want to remove them, please use your package manager manually."
    echo "============================================================"
}

# Execute the uninstall
uninstall_application