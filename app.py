"""
Main Flask Application for Orange USB/IP Web Interface
=======================================================

This is the core application module that initializes and configures the Flask
web application, defines routes, and handles user requests. It serves as the
central hub connecting all components of the USB/IP management system.

File: app.py
Project: Orange USB/IP Web Interface
Purpose: Flask application initialization, route definitions, and request handling

Key Components:
    - Flask application factory and configuration
    - SQLAlchemy database initialization
    - Flask-Login authentication setup
    - Route definitions for all pages and API endpoints
    - Error handlers for HTTP errors
    - Integration with USB/IP utilities
    - Virtual device management routes
    - Terminal command execution routes

Port Configuration:
    - Web Interface: Port 5000 (Flask/Gunicorn)
    - Real USB/IP daemon (usbipd): Port 3240
    - Virtual FIDO USB/IP: Port 3241

Dependencies:
    - Flask: Web framework
    - Flask-Login: User session management
    - Flask-SQLAlchemy: Database ORM
    - Werkzeug: Security utilities
    - netifaces: Network interface detection
"""

# ============================================================================
# IMPORTS
# ============================================================================

# Standard library imports
import os                      # Operating system interfaces (file paths, env vars)
import re                      # Regular expressions for pattern matching
import json                    # JSON encoding/decoding
import random                  # Random number generation for port IDs
import logging                 # Python logging framework
import socket                  # Network socket operations
import subprocess              # External command execution

# Third-party library imports
import netifaces               # Cross-platform network interface detection
from dotenv import load_dotenv # Load environment variables from .env file

# Flask and extensions imports
from flask import (
    Flask,                     # Main Flask application class
    render_template,           # Jinja2 template rendering
    redirect,                  # HTTP redirect responses
    url_for,                   # URL building for routes
    request,                   # Current request object
    flash,                     # Flash messages for user feedback
    jsonify,                   # Convert Python objects to JSON responses
    send_file,                 # Send files to client
    session                    # User session management
)
from flask_login import (
    LoginManager,              # Manages user sessions
    login_user,                # Log a user in
    logout_user,               # Log a user out
    login_required,            # Decorator to protect routes
    current_user               # Proxy for the currently logged-in user
)
from werkzeug.security import (
    check_password_hash,       # Verify password against hash
    generate_password_hash     # Create secure password hash
)
from werkzeug.middleware.proxy_fix import ProxyFix  # Handle reverse proxy headers
from flask_sqlalchemy import SQLAlchemy              # SQLAlchemy ORM integration
from sqlalchemy.ext.declarative import declarative_base  # Base class for models
from datetime import datetime  # Date and time handling

# ============================================================================
# ENVIRONMENT CONFIGURATION
# ============================================================================

# Load environment variables from .env file if it exists
# This allows configuration without modifying code
load_dotenv()

# ============================================================================
# LOGGING FUNCTION (defined before db to avoid circular import)
# ============================================================================

def add_log_entry(level, message, source):
    """
    Add an entry to the application's persistent log.
    
    This function creates a LogEntry record in the database for tracking
    system events, errors, and user actions. All messages should be in
    English for consistency.
    
    Args:
        level (str): Log severity level
                     - 'DEBUG': Detailed diagnostic information
                     - 'INFO': General operational events
                     - 'WARNING': Potential issues that need attention
                     - 'ERROR': Failures that prevented an operation
        message (str): Description of the event (in English)
        source (str): Component that generated the log
                      Examples: 'auth', 'system', 'usbip', 'fido', 'virtual', 'terminal'
    
    Example:
        add_log_entry('INFO', 'User admin logged in successfully', 'auth')
    """
    # Create new log entry record
    log_entry = LogEntry(level=level, message=message, source=source)
    # Add to database session
    db.session.add(log_entry)
    # Commit the transaction
    db.session.commit()
    # Also log to Python logger for console output
    logger.debug(f"Log added: [{level}] {message} (Source: {source})")


# ============================================================================
# LOGGING SETUP
# ============================================================================

# Configure Python's logging module for debug output
# DEBUG level shows all log messages including detailed diagnostics
logging.basicConfig(level=logging.DEBUG)
# Create a logger instance for this module
logger = logging.getLogger(__name__)

# ============================================================================
# NETWORK UTILITIES
# ============================================================================

def get_network_interfaces():
    """
    Detect and return information about network interfaces.
    
    Scans all network interfaces to find Ethernet and WiFi connections,
    returning their names, IP addresses, and URLs for accessing the
    web interface from those networks.
    
    This is used to display connection URLs on the login page and
    help users access the interface from different networks.
    
    Returns:
        dict: Dictionary with interface types as keys ('Ethernet', 'WiFi')
              and lists of interface info as values.
              Each interface info contains:
              - 'name': Interface name (e.g., 'eth0', 'wlan0')
              - 'ip': IP address assigned to the interface
              - 'url': Full URL to access the web interface
    
    Example return:
        {
            'Ethernet': [
                {'name': 'eth0', 'ip': '192.168.1.100', 'url': 'http://192.168.1.100:5000'}
            ],
            'WiFi': [
                {'name': 'wlan0', 'ip': '192.168.1.101', 'url': 'http://192.168.1.101:5000'}
            ]
        }
    """
    interfaces = {}
    try:
        # Get list of all network interfaces on the system
        all_interfaces = netifaces.interfaces()
        
        for iface in all_interfaces:
            # Skip loopback (lo) and virtual/container interfaces
            # These are internal and shouldn't be used for external access
            if iface == 'lo' or 'docker' in iface or 'veth' in iface or 'br-' in iface:
                continue
            
            # Get all addresses for this interface
            addrs = netifaces.ifaddresses(iface)
            
            # Check if interface has IPv4 addresses (AF_INET = IPv4)
            if netifaces.AF_INET in addrs:
                for addr in addrs[netifaces.AF_INET]:
                    ip = addr['addr']
                    
                    # Skip localhost addresses (127.x.x.x)
                    if ip.startswith('127.'):
                        continue
                    
                    # Determine interface type based on naming convention
                    # WiFi interfaces typically start with 'wl' or contain 'wlan'
                    iface_type = 'Ethernet'
                    if iface.startswith('wl') or 'wlan' in iface or 'wifi' in iface.lower():
                        iface_type = 'WiFi'
                    
                    # Create entry for this interface type if not exists
                    if iface_type not in interfaces:
                        interfaces[iface_type] = []
                    
                    # Add interface info with access URL
                    interfaces[iface_type].append({
                        'name': iface,
                        'ip': ip,
                        'url': f'http://{ip}:5000'  # Port 5000 is the web interface port
                    })
        
        logger.debug(f"Found network interfaces: {interfaces}")
    except Exception as e:
        logger.error(f"Error getting network interface information: {str(e)}")
    
    return interfaces

# ============================================================================
# DATABASE SETUP
# ============================================================================

# Create the declarative base class for SQLAlchemy models
# All model classes will inherit from this base
Base = declarative_base()

# Initialize SQLAlchemy with custom base class
# This connects Flask to the database via SQLAlchemy ORM
db = SQLAlchemy(model_class=Base)

# ============================================================================
# FLASK APPLICATION INITIALIZATION
# ============================================================================

# Create the Flask application instance
# __name__ tells Flask where to find templates and static files
app = Flask(__name__)

# Set the secret key for session encryption
# SECURITY: In production, always use a strong random key from environment variable
# The fallback value is only for development/testing
app.secret_key = os.environ.get("SESSION_SECRET", "default_secret_key_for_development")

# Configure ProxyFix middleware for reverse proxy support
# This ensures url_for() generates correct URLs behind nginx/Apache
# x_proto=1: Trust X-Forwarded-Proto header (for HTTPS detection)
# x_host=1: Trust X-Forwarded-Host header (for correct host detection)
app.wsgi_app = ProxyFix(app.wsgi_app, x_proto=1, x_host=1)

# ============================================================================
# DATABASE CONFIGURATION
# ============================================================================

# Build path to SQLite database file in the same directory as this script
database_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'usbip_web.db')

# Configure SQLAlchemy to use SQLite database
# Format: sqlite:///path/to/database.db
app.config["SQLALCHEMY_DATABASE_URI"] = f"sqlite:///{database_path}"

# SQLite-specific engine options
# check_same_thread=False allows multi-threaded access to SQLite
# This is needed because Flask runs in multiple threads
app.config["SQLALCHEMY_ENGINE_OPTIONS"] = {
    "connect_args": {"check_same_thread": False}
}

# Initialize the database with the Flask app
db.init_app(app)

# Migrate database to add new columns if they don't exist
def migrate_virtual_usb_devices():
    """Add is_published and usbip_busid columns to virtual_usb_devices if missing."""
    import sqlite3
    try:
        conn = sqlite3.connect(database_path)
        cursor = conn.cursor()
        cursor.execute("PRAGMA table_info(virtual_usb_devices)")
        columns = [col[1] for col in cursor.fetchall()]
        if 'is_published' not in columns:
            cursor.execute("ALTER TABLE virtual_usb_devices ADD COLUMN is_published BOOLEAN DEFAULT 0")
            logging.info("Added is_published column to virtual_usb_devices")
        if 'usbip_busid' not in columns:
            cursor.execute("ALTER TABLE virtual_usb_devices ADD COLUMN usbip_busid VARCHAR(16)")
            logging.info("Added usbip_busid column to virtual_usb_devices")
        conn.commit()
        conn.close()
    except Exception as e:
        logging.warning(f"Database migration note: {e}")

if os.path.exists(database_path):
    migrate_virtual_usb_devices()

# ============================================================================
# AUTHENTICATION SETUP (Flask-Login)
# ============================================================================

# Create and configure the login manager
login_manager = LoginManager()
# Attach login manager to the Flask app
login_manager.init_app(app)
# Set the route name for the login page
# Users will be redirected here if they access a protected page
login_manager.login_view = "login"


@login_manager.unauthorized_handler
def unauthorized_handler():
    """
    Handle unauthorized access attempts.
    
    This function is called when a user tries to access a protected
    resource without being logged in.
    
    For API endpoints (starting with /api/): Returns JSON error response
    For regular pages: Redirects to login page
    
    Returns:
        Response: JSON 401 error for API, redirect for regular pages
    """
    # Check if this is an API request
    if request.path.startswith('/api/'):
        # Return JSON error for API endpoints
        return jsonify({
            'success': False,
            'message': 'Unauthorized access. Please login.'
        }), 401
    # Redirect to login page for regular page requests
    return redirect(url_for('login'))


# Note: Translation system was removed - interface is English-only

# ============================================================================
# UTILITY IMPORTS
# ============================================================================

# Import USB/IP utility functions for device management
# These handle low-level USB/IP operations like binding, attaching, detaching
from usbip_utils import (
    get_local_usb_devices,     # List local USB devices
    bind_device,               # Bind (publish) a device for sharing
    get_remote_usb_devices,    # List devices on remote USB/IP server
    attach_device,             # Attach a remote device locally
    detach_device,             # Detach an attached device
    get_attached_devices,      # List currently attached devices
    get_published_devices      # List published (bound) devices
)

# ============================================================================
# MODEL IMPORTS (after db is configured)
# ============================================================================

# Import database models
# These must be imported after db is initialized to avoid circular imports
from models import (
    User,                      # User accounts
    DeviceAlias,               # Device friendly names
    UsbPort,                   # USB port configurations
    LogEntry,                  # System logs
    VirtualUsbDevice,          # Virtual USB device definitions
    VirtualUsbPort,            # Virtual port mappings
    VirtualUsbFile,            # Virtual storage files
    TerminalCommand,           # Saved terminal commands
    FidoDevice,                # FIDO2 device configuration
    FidoCredential,            # FIDO2 credential metadata
    FidoLog                    # FIDO2 operation logs
)

# ============================================================================
# VIRTUAL STORAGE IMPORTS
# ============================================================================

# Import virtual storage management functions
from virtual_storage_utils import (
    create_device_storage,     # Create storage for virtual USB device
    delete_device_storage,     # Delete virtual storage
    resize_device_storage,     # Resize virtual storage
    get_device_storage_usage,  # Get storage usage statistics
    list_device_files,         # List files in virtual storage
    create_directory,          # Create directory in virtual storage
    delete_item,               # Delete file/folder from virtual storage
    upload_file,               # Upload file to virtual storage
    get_storage_stats,         # Get overall storage statistics
    download_file              # Download file from virtual storage
)

# ============================================================================
# BLUEPRINT IMPORTS AND REGISTRATION
# ============================================================================

# Import Flask Blueprints for modular route organization
from storage_routes import storage_bp  # Virtual storage API routes
from fido_routes import fido_bp        # FIDO2 device routes

# Import Avahi utilities for network service discovery
from avahi_utils import discover_services, is_avahi_available, get_local_service_info

# Register blueprints with the main application
# This adds all routes defined in those blueprints
app.register_blueprint(storage_bp)
app.register_blueprint(fido_bp)

# ============================================================================
# DATABASE INITIALIZATION
# ============================================================================

# Initialize database tables within application context
with app.app_context():
    # Create all tables defined by models if they don't exist
    db.create_all()
    
    # Create default admin user if not exists
    # This ensures there's always an admin account for initial setup
    admin_user = User.query.filter_by(username='admin').first()
    if not admin_user:
        # Create admin user with default credentials
        admin_user = User(username='admin', is_admin=True)
        admin_user.set_password('admin')  # Default password - CHANGE IN PRODUCTION!
        db.session.add(admin_user)
        db.session.commit()
        logger.info("Created default admin user")


# ============================================================================
# USER LOADER (Flask-Login)
# ============================================================================

@login_manager.user_loader
def load_user(user_id):
    """
    Load a user from the database by their ID.
    
    This callback is used by Flask-Login to reload the user object
    from the user ID stored in the session.
    
    Args:
        user_id (str): The user's ID (as stored in session)
    
    Returns:
        User: The User object, or None if not found
    """
    return User.query.get(int(user_id))


# ============================================================================
# AUTHENTICATION ROUTES
# ============================================================================

@app.route('/login', methods=['GET', 'POST'])
def login():
    """
    Handle user login.
    
    GET: Display the login page with network interface information
    POST: Validate credentials and log user in
    
    The login page displays available network URLs to help users
    access the interface from different devices on the network.
    
    Returns:
        Response: Login page (GET) or redirect to index/login with message (POST)
    """
    if request.method == 'POST':
        # Get form data
        username = request.form.get('username')
        password = request.form.get('password')
        
        # Find user in database
        user = User.query.filter_by(username=username).first()
        
        # Verify user exists and password is correct
        if user and user.check_password(password):
            # Log the user in (creates session)
            login_user(user)
            
            # Record successful login in audit log
            add_log_entry('INFO', f'User {username} logged in successfully', 'auth')
            
            # Show success message with timestamp
            current_time = datetime.now().strftime('%H:%M:%S')
            flash(f'Login successful! [{current_time}]', 'login-success')
            
            # Redirect to main dashboard
            return redirect(url_for('index'))
        else:
            # Log failed attempt for security monitoring
            if username:
                add_log_entry('WARNING', f'Failed login attempt for user {username}', 'auth')
            
            # Show error message with helpful tips
            current_time = datetime.now().strftime('%H:%M:%S')
            flash(f'Invalid username or password. [{current_time}] Check keyboard layout and Caps Lock.', 'login-error')
    
    # GET request: Display login page
    # Get network interfaces to show available connection URLs
    network_interfaces = get_network_interfaces()
    return render_template('login.html', network_interfaces=network_interfaces)


# Note: Language selection route removed - interface is English-only


@app.route('/logout')
@login_required
def logout():
    """
    Log out the current user.
    
    Ends the user's session and redirects to the login page.
    Requires user to be logged in (protected by @login_required).
    
    Returns:
        Response: Redirect to login page with logout confirmation
    """
    # Save username for logging before logout
    username = current_user.username
    
    # End the user's session
    logout_user()
    
    # Record logout in audit log
    add_log_entry('INFO', f'User {username} logged out', 'auth')
    
    # Show confirmation message
    flash('You have been logged out', 'info')
    
    return redirect(url_for('login'))


# ============================================================================
# DEVICE API ROUTES
# ============================================================================

@app.route('/api/local_devices')
@login_required
def get_local_devices_api():
    """
    API endpoint to get list of local USB devices.
    
    Returns a JSON response with all local USB devices including:
    - Physical USB devices detected by usbip
    - Virtual USB devices defined in the database
    
    This endpoint is used for AJAX updates without page reload.
    
    Returns:
        Response: JSON with device list or error message
                  {
                      'success': True/False,
                      'devices': [...] or 'message': 'error description'
                  }
    """
    try:
        # Get physical USB devices through usbip utility
        local_devices = get_local_usb_devices()
        
        # Get list of published (bound) devices for status marking
        published_busids = get_published_devices()
        add_log_entry('DEBUG', f'API: Published devices: {published_busids}', 'usbip')
        
        # Mark published devices in the list
        for device in local_devices:
            if 'busid' in device:
                # Import normalize function for consistent busid comparison
                from usbip_utils import normalize_busid
                # Normalize busid format for comparison
                device_busid = normalize_busid(device['busid'])
                
                # Check if device is in published list
                if device_busid in published_busids:
                    device['is_published'] = True
                    add_log_entry('DEBUG', f'API: Device {device["busid"]} marked as published', 'usbip')
                else:
                    device['is_published'] = False
                    add_log_entry('DEBUG', f'API: Device {device["busid"]} NOT marked as published', 'usbip')
            else:
                device['is_published'] = False
        
        # Add inactive virtual devices to the list
        # Active virtual devices are not shown here as they're "in use"
        virtual_devices = VirtualUsbDevice.query.filter_by(is_active=False).all()
        
        for device in virtual_devices:
            # Virtual devices get a special 'v-' prefix in their busid
            local_devices.append({
                'busid': f'v-{device.id}',           # Virtual device ID format
                'device_name': device.name,
                'idVendor': device.vendor_id,
                'idProduct': device.product_id,
                'is_virtual': True,                   # Flag for UI handling
                'virtual_id': device.id,
                'is_published': False                 # Virtual devices aren't published via usbip
            })
        
        # Record device refresh in log
        add_log_entry('INFO', f'USB device list refreshed via API, found {len(local_devices)} devices', 'system')
        
        return jsonify({
            'success': True,
            'devices': local_devices
        })
    except Exception as e:
        # Log error and return error response
        add_log_entry('ERROR', f'Failed to get USB devices list: {str(e)}', 'system')
        return jsonify({
            'success': False,
            'message': str(e)
        }), 500


@app.route('/api/discover-services')
@login_required
def discover_services_api():
    """
    API endpoint to discover Orange USB/IP services on the local network.
    
    Uses Avahi (mDNS) to find other Orange USB/IP instances.
    Scan timeout is 5 seconds by default (configurable via AVAHI_SCAN_TIMEOUT env var).
    
    Returns:
        Response: JSON with discovered services
                  {
                      'success': True/False,
                      'services': [...],
                      'scan_time': float,
                      'method': str,
                      'error': str or None
                  }
    """
    try:
        timeout = request.args.get('timeout', 5, type=int)
        if timeout < 1:
            timeout = 1
        elif timeout > 30:
            timeout = 30
        
        result = discover_services(timeout=timeout)
        
        add_log_entry('INFO', 
            f'Network discovery: found {len(result.get("services", []))} services in {result.get("scan_time", 0)}s',
            'avahi')
        
        return jsonify(result)
        
    except Exception as e:
        add_log_entry('ERROR', f'Network discovery failed: {str(e)}', 'avahi')
        return jsonify({
            'success': False,
            'services': [],
            'scan_time': 0,
            'method': 'error',
            'error': str(e)
        }), 500


@app.route('/api/avahi-status')
@login_required
def avahi_status_api():
    """
    API endpoint to check Avahi availability and local service info.
    
    Returns:
        Response: JSON with Avahi status
                  {
                      'available': True/False,
                      'local_service': {...} or None
                  }
    """
    try:
        available = is_avahi_available()
        local_service = get_local_service_info() if available else None
        
        return jsonify({
            'success': True,
            'available': available,
            'local_service': local_service
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'available': False,
            'error': str(e)
        }), 500


# ============================================================================
# MAIN PAGE ROUTES
# ============================================================================

@app.route('/')
@login_required
def index():
    """
    Main dashboard page.
    
    Displays:
    - Local USB devices (physical and virtual)
    - Attached remote devices
    - Network interface information
    - Device publish status
    
    Returns:
        Response: Rendered index.html template with device data
    """
    # Get physical USB devices
    local_devices = get_local_usb_devices()
    
    # Get published device list for status display
    published_busids = get_published_devices()
    add_log_entry('DEBUG', f'Published devices: {published_busids}', 'usbip')
    
    # Mark published devices
    for device in local_devices:
        if 'busid' in device:
            from usbip_utils import normalize_busid
            device_busid = normalize_busid(device['busid'])
            if device_busid in published_busids:
                device['is_published'] = True
                add_log_entry('DEBUG', f'Device {device["busid"]} marked as published', 'usbip')
            else:
                device['is_published'] = False
                add_log_entry('DEBUG', f'Device {device["busid"]} NOT marked as published', 'usbip')
        else:
            device['is_published'] = False
    
    # Get attached remote devices
    attached_devices = get_attached_devices()
    
    # Add inactive virtual devices to local device list
    virtual_devices = VirtualUsbDevice.query.filter_by(is_active=False).all()
    for device in virtual_devices:
        local_devices.append({
            'busid': f'v-{device.id}',         # Prefix to distinguish from physical devices
            'device_name': f'{device.name} (Virtual)',
            'vendor_id': device.vendor_id,
            'product_id': device.product_id,
            'is_virtual': True,
            'virtual_id': device.id
        })
    
    # Add connected virtual devices to attached list
    connected_virtual_ports = VirtualUsbPort.query.filter_by(is_connected=True).all()
    for port in connected_virtual_ports:
        if port.device:
            attached_devices.append({
                'port': f'v-{port.port_number}',
                'device_name': f'{port.device.name} (Virtual)',
                'remote_busid': f'{port.device.vendor_id}:{port.device.product_id}',
                'remote_host': 'local-virtual',
                'is_virtual': True,
                'virtual_port_id': port.id,
                'virtual_device_id': port.device.id
            })
    
    # Get available virtual ports for connection modal
    available_virtual_ports = VirtualUsbPort.query.filter_by(is_connected=False).all()
    
    # Get network interface information
    network_interfaces = get_network_interfaces()
    
    return render_template('index.html', 
                          local_devices=local_devices, 
                          attached_devices=attached_devices,
                          available_virtual_ports=available_virtual_ports,
                          network_interfaces=network_interfaces)


@app.route('/home2')
@login_required
def home2():
    """
    Alternative simplified dashboard page.
    
    A cleaner version of the main dashboard with less complexity,
    used for troubleshooting or when the main dashboard has issues.
    
    Returns:
        Response: Rendered home2.html template
    """
    # Get local USB devices
    local_devices = get_local_usb_devices()
    
    # Get published devices with debug logging
    published_busids = get_published_devices()
    add_log_entry('DEBUG', f'Home2: Published devices: {published_busids}', 'usbip')
    
    # Mark published devices with detailed logging
    for device in local_devices:
        if 'busid' in device:
            from usbip_utils import normalize_busid
            device_busid = normalize_busid(device['busid'])
            if device_busid in published_busids:
                device['is_published'] = True
                add_log_entry('DEBUG', f'Home2: Device {device["busid"]} ({device_busid}) marked as published', 'usbip')
            else:
                device['is_published'] = False
                add_log_entry('DEBUG', f'Home2: Device {device["busid"]} ({device_busid}) NOT marked as published', 'usbip')
        else:
            device['is_published'] = False
    
    # Get attached devices
    attached_devices = get_attached_devices()
    
    # Add virtual devices
    virtual_devices = VirtualUsbDevice.query.filter_by(is_active=False).all()
    for device in virtual_devices:
        local_devices.append({
            'busid': f'v-{device.id}',
            'device_name': device.name,
            'idVendor': device.vendor_id,
            'idProduct': device.product_id,
            'is_virtual': True,
            'virtual_id': device.id,
            'is_published': False
        })
    
    # Apply device aliases (custom names)
    device_aliases = {alias.busid: alias.alias for alias in DeviceAlias.query.all()}
    for device in local_devices:
        if 'busid' in device and device['busid'] in device_aliases:
            device['device_name'] = device_aliases[device['busid']]
    
    # Log device refresh
    add_log_entry('INFO', f'Home2: USB device list refreshed, found {len(local_devices)} devices', 'system')
    
    # Debug output to console
    logger.debug(f"Home2: Local devices: {local_devices}")
    logger.debug(f"Home2: Attached devices: {attached_devices}")
    
    return render_template('home2.html',
                           local_devices=local_devices,
                           attached_devices=attached_devices)


# ============================================================================
# ADMIN ROUTES
# ============================================================================

@app.route('/admin', methods=['GET', 'POST'])
@login_required
def admin():
    """
    Administration panel page.
    
    Allows admins to:
    - Change their password
    - Manage USB port names
    - Manage device aliases
    
    Only accessible to users with is_admin=True.
    
    Returns:
        Response: Admin page or redirect if not admin
    """
    # Check admin permission
    if not current_user.is_admin:
        flash('You do not have admin access', 'danger')
        return redirect(url_for('index'))
    
    # Handle form submissions
    if request.method == 'POST':
        # Password change form
        if 'change_password' in request.form:
            current_password = request.form.get('current_password')
            new_password = request.form.get('new_password')
            confirm_password = request.form.get('confirm_password')
            
            # Validate current password
            if not current_user.check_password(current_password):
                flash('Current password is incorrect', 'danger')
            # Check password confirmation matches
            elif new_password != confirm_password:
                flash('New password and confirmation do not match', 'danger')
            # Enforce minimum password length
            elif len(new_password) < 6:
                flash('New password must be at least 6 characters', 'danger')
            else:
                # Update password
                current_user.set_password(new_password)
                db.session.commit()
                
                # Log password change
                add_log_entry('INFO', f'User {current_user.username} changed password', 'auth')
                
                flash('Password changed successfully', 'success')
                return redirect(url_for('admin'))
    
    # Get data for admin panel
    usb_ports = UsbPort.query.all()
    device_aliases = DeviceAlias.query.all()
    network_interfaces = get_network_interfaces()
    
    return render_template('admin.html', 
                          usb_ports=usb_ports,
                          device_aliases=device_aliases,
                          network_interfaces=network_interfaces)


# ============================================================================
# LOGS ROUTE
# ============================================================================

@app.route('/logs')
@login_required
def logs():
    """
    System logs viewer page.
    
    Displays paginated log entries with optional filtering by log level.
    
    Query Parameters:
        type (str): Filter by log level (all, info, warning, error, debug)
        page (int): Page number for pagination (default: 1)
    
    Returns:
        Response: Rendered logs.html template with paginated logs
    """
    # Get filter type from query string (default: 'all')
    log_type = request.args.get('type', 'all')
    # Get page number (default: 1)
    page = request.args.get('page', 1, type=int)
    # Number of logs per page
    per_page = 20
    
    # Base query with newest logs first
    query = LogEntry.query.order_by(LogEntry.timestamp.desc())
    
    # Apply level filter if not 'all'
    if log_type != 'all':
        query = query.filter_by(level=log_type.upper())
    
    # Paginate results
    logs = query.paginate(page=page, per_page=per_page, error_out=False)
    
    # Get network interfaces for header
    network_interfaces = get_network_interfaces()
    
    return render_template('logs.html', 
                          logs=logs, 
                          current_type=log_type, 
                          network_interfaces=network_interfaces)


# ============================================================================
# DEVICE ALIAS ROUTES
# ============================================================================

@app.route('/device_alias', methods=['POST'])
@login_required
def device_alias():
    """
    Create or update a device alias (friendly name).
    
    Allows users to assign memorable names to USB devices
    instead of using cryptic bus IDs.
    
    Form Data:
        busid (str): USB bus ID of the device
        alias (str): User-friendly name for the device
        device_info (str): Original device description (optional)
    
    Returns:
        Response: Redirect to index page with success/error message
    """
    busid = request.form.get('busid')
    alias = request.form.get('alias')
    device_info = request.form.get('device_info', '')
    
    # Validate required fields
    if not busid or not alias:
        flash('Device ID and alias are required', 'danger')
        return redirect(url_for('index'))
    
    # Check if alias already exists for this device
    existing_alias = DeviceAlias.query.filter_by(busid=busid).first()
    if existing_alias:
        # Update existing alias
        existing_alias.alias = alias
        existing_alias.device_info = device_info
        db.session.commit()
        flash(f'Alias for device {busid} updated', 'success')
    else:
        # Create new alias
        new_alias = DeviceAlias(busid=busid, alias=alias, device_info=device_info)
        db.session.add(new_alias)
        db.session.commit()
        flash(f'Alias for device {busid} added', 'success')
    
    return redirect(url_for('index'))


@app.route('/port_name', methods=['POST'])
@login_required
def port_name():
    """
    Create or update a USB port name.
    
    Allows users to assign names to USB port locations
    for easier physical identification.
    
    Form Data:
        port_number (str): System port identifier
        custom_name (str): User-friendly name for the port
    
    Returns:
        Response: Redirect to index page with success/error message
    """
    port_number = request.form.get('port_number')
    custom_name = request.form.get('custom_name')
    
    # Validate required fields
    if not port_number or not custom_name:
        flash('Port number and custom name are required', 'danger')
        return redirect(url_for('index'))
    
    # Check if port name already exists
    existing_port = UsbPort.query.filter_by(port_number=port_number).first()
    if existing_port:
        # Update existing port name
        existing_port.custom_name = custom_name
        db.session.commit()
        flash(f'Name for port {port_number} updated', 'success')
    else:
        # Create new port name
        new_port = UsbPort(port_number=port_number, custom_name=custom_name)
        db.session.add(new_port)
        db.session.commit()
        flash(f'Name for port {port_number} added', 'success')
    
    return redirect(url_for('index'))


# ============================================================================
# USB/IP DEVICE OPERATIONS
# ============================================================================

@app.route('/bind_device', methods=['POST'])
@login_required
def bind_device_route():
    """
    Publish (bind) a USB device for sharing via USB/IP.
    
    Makes a local USB device available for remote attachment
    by other machines on the network.
    
    Accepts both form data and JSON request body.
    
    Request Data:
        busid (str): USB bus ID of the device to publish
    
    Returns:
        Response: JSON with success status and message
    """
    try:
        # Log request details for debugging
        add_log_entry('DEBUG', f'Bind device request received from user: {current_user.username}', 'usbip')
        add_log_entry('DEBUG', f'Request content type: {request.content_type}', 'usbip')
        add_log_entry('DEBUG', f'Request method: {request.method}', 'usbip')
        add_log_entry('DEBUG', f'Request headers: {dict(request.headers)}', 'usbip')
        add_log_entry('DEBUG', f'Request form data: {dict(request.form)}', 'usbip')
        
        # Extract busid from form or JSON data
        busid = None
        if request.content_type == 'application/json':
            # JSON request body
            data = request.get_json()
            busid = data.get('busid') if data else None
            add_log_entry('DEBUG', f'JSON data received: {data}', 'usbip')
        else:
            # Form data
            busid = request.form.get('busid')
            add_log_entry('DEBUG', f'Form data received: busid={busid}', 'usbip')
        
        # Validate busid is provided
        if not busid:
            add_log_entry('ERROR', 'No busid provided in request', 'usbip')
            return jsonify({'success': False, 'message': 'Device busid not specified'}), 400
        
        # Attempt to bind the device
        add_log_entry('DEBUG', f'Attempting to bind device with busid: {busid}', 'usbip')
        success, message = bind_device(busid)
        
        # Log result
        level = 'INFO' if success else 'ERROR'
        add_log_entry(level, f'Published device {busid}: {message}', 'usbip')
        
        return jsonify({'success': success, 'message': message})
        
    except Exception as e:
        add_log_entry('ERROR', f'Bind device route error: {str(e)}', 'usbip')
        return jsonify({'success': False, 'message': f'Server error: {str(e)}'}), 500


@app.route('/remote')
@login_required
def remote():
    """
    Remote USB devices page.
    
    Interface for connecting to and attaching USB devices
    from remote USB/IP servers.
    
    Returns:
        Response: Rendered remote.html template
    """
    network_interfaces = get_network_interfaces()
    return render_template('remote.html', network_interfaces=network_interfaces)


@app.route('/get_remote_devices', methods=['POST'])
@login_required
def get_remote_devices_route():
    """
    Get list of USB devices from a remote USB/IP server.
    
    Queries both real USB devices (via usbip on port 3240) and
    virtual devices (via API on port 3242 or database).
    
    Form Data:
        ip (str): IP address of the remote USB/IP server
    
    Returns:
        Response: JSON with list of available devices or error message
    """
    import requests as http_requests
    
    ip = request.form.get('ip')
    if not ip:
        return jsonify({'success': False, 'message': 'IP address not specified'}), 400
    
    all_devices = []
    
    devices, error = get_remote_usb_devices(ip)
    
    if devices:
        for device in devices:
            device['is_virtual'] = False
            device['device_source'] = 'usbip'
        all_devices.extend(devices)
        add_log_entry('INFO', f'Got {len(devices)} real USB devices from {ip}', 'usbip')
    
    try:
        virtual_api_url = f"http://{ip}:3242/api/devices"
        resp = http_requests.get(virtual_api_url, timeout=3)
        if resp.status_code == 200:
            data = resp.json()
            if data.get('success') and data.get('devices'):
                for vdev in data['devices']:
                    vdev['is_virtual'] = True
                    vdev['device_source'] = 'virtual-fido'
                    all_devices.append(vdev)
                add_log_entry('INFO', f'Got {len(data["devices"])} virtual devices from {ip}:3242', 'virtual')
    except http_requests.exceptions.ConnectionError:
        pass
    except Exception as e:
        add_log_entry('DEBUG', f'Virtual device API not available on {ip}: {str(e)}', 'virtual')
    
    is_local = ip in ('127.0.0.1', 'localhost', '::1')
    if is_local or not all_devices:
        try:
            published_virtual = VirtualUsbDevice.query.filter_by(is_published=True).all()
            for device in published_virtual:
                busid_exists = any(d.get('busid') == device.usbip_busid for d in all_devices)
                if not busid_exists:
                    all_devices.append({
                        'busid': device.usbip_busid or f'v-{device.id}',
                        'name': device.name,
                        'device': device.name,
                        'vid_pid': f'{device.vendor_id}:{device.product_id}',
                        'device_type': device.device_type,
                        'is_virtual': True,
                        'device_source': 'database',
                        'virtual_id': device.id
                    })
            if published_virtual:
                add_log_entry('DEBUG', f'Added {len(published_virtual)} published virtual devices from database', 'virtual')
        except Exception as e:
            add_log_entry('DEBUG', f'Error querying local virtual devices: {str(e)}', 'virtual')
    
    if not all_devices and error:
        add_log_entry('ERROR', f'Error getting device list from {ip}: {error}', 'usbip')
        return jsonify({'success': False, 'error': error})
    
    for device in all_devices:
        if 'busid' in device:
            alias = DeviceAlias.query.filter_by(busid=device['busid']).first()
            if alias:
                device['alias'] = alias.alias
    
    return jsonify({'success': True, 'devices': all_devices})


@app.route('/attach_device', methods=['POST'])
@login_required
def attach_device_route():
    """
    Attach a USB device from a remote USB/IP server.
    
    Makes a remote USB device appear as a local USB device.
    
    Form Data:
        ip (str): IP address of the remote USB/IP server
        busid (str): Bus ID of the device on the remote server
    
    Returns:
        Response: JSON with success status and message
    """
    ip = request.form.get('ip')
    busid = request.form.get('busid')
    
    if not ip or not busid:
        return jsonify({'success': False, 'message': 'IP and busid not specified'}), 400
    
    # Attempt to attach the device
    success, message = attach_device(ip, busid)
    
    # Log result
    level = 'INFO' if success else 'ERROR'
    add_log_entry(level, f'Attached device {busid} from server {ip}: {message}', 'usbip')
    
    return jsonify({'success': success, 'message': message})


@app.route('/detach_device', methods=['POST'])
@login_required
def detach_device_route():
    """
    Detach an attached USB device.
    
    Removes a previously attached USB device from the local system.
    
    Form Data:
        port (str): Port number of the attached device
    
    Returns:
        Response: JSON with success status and message
    """
    port = request.form.get('port')
    
    if not port:
        return jsonify({'success': False, 'message': 'Port not specified'}), 400
    
    # Attempt to detach the device
    success, message = detach_device(port)
    
    # Log result
    level = 'INFO' if success else 'ERROR'
    add_log_entry(level, f'Detached device from port {port}: {message}', 'usbip')
    
    return jsonify({'success': success, 'message': message})


# ============================================================================
# VIRTUAL DEVICE ROUTES
# ============================================================================

@app.route('/virtual_devices')
@login_required
def virtual_devices():
    """
    Virtual USB devices management page.
    
    Displays and manages virtual USB devices like:
    - Virtual storage (flash drives)
    - HID devices
    - Serial ports
    - Network adapters
    
    Returns:
        Response: Rendered virtual_devices.html template
    """
    # Get all virtual devices and ports
    virtual_devices = VirtualUsbDevice.query.all()
    virtual_ports = VirtualUsbPort.query.all()
    
    # Define available device types for the creation form
    device_types = [
        {'id': 'storage', 'name': 'Storage Device (Flash Drive)'},
        {'id': 'hid', 'name': 'HID (Mouse, Keyboard)'},
        {'id': 'serial', 'name': 'Serial Port'},
        {'id': 'ethernet', 'name': 'Network Adapter'},
        {'id': 'audio', 'name': 'Audio Device'},
        {'id': 'printer', 'name': 'Printer'},
        {'id': 'camera', 'name': 'Web Camera'},
        {'id': 'custom', 'name': 'Other (Custom Configuration)'}
    ]
    
    network_interfaces = get_network_interfaces()
    
    return render_template('virtual_devices.html', 
                          virtual_devices=virtual_devices,
                          virtual_ports=virtual_ports,
                          device_types=device_types,
                          network_interfaces=network_interfaces)


@app.route('/create_virtual_device', methods=['POST'])
@login_required
def create_virtual_device():
    """
    Create a new virtual USB device.
    
    Form Data:
        name (str): User-friendly device name
        device_type (str): Type of virtual device
        vendor_id (str): USB Vendor ID (4 hex digits)
        product_id (str): USB Product ID (4 hex digits)
        serial_number (str): Optional device serial number
        config_json (str): Optional JSON configuration
        storage_size (int): Size in MB for storage devices
        use_system_folder (bool): Use existing system folder as storage
        system_path (str): Path to system folder (if use_system_folder)
        system_storage_size (int): Size limit for system folder
    
    Returns:
        Response: Redirect to virtual devices page with message
    """
    # Get form data
    name = request.form.get('name')
    device_type = request.form.get('device_type')
    vendor_id = request.form.get('vendor_id', '1a2b').lower()
    product_id = request.form.get('product_id', '3c4d').lower()
    serial_number = request.form.get('serial_number', '')
    config_json = request.form.get('config_json', '{}')
    
    # Handle storage size for storage devices
    storage_size = 1024  # Default 1GB
    if device_type == 'storage':
        try:
            storage_size = int(request.form.get('storage_size', 1024))
            # Validate storage size range (1MB - 16GB)
            if storage_size < 1 or storage_size > 16384:
                flash('Storage size must be between 1 MB and 16 GB', 'warning')
                storage_size = 1024
        except ValueError:
            flash('Invalid storage size, using default (1 GB)', 'warning')
    
    # Validate required fields
    if not name or not device_type:
        flash('Name and device type are required', 'danger')
        return redirect(url_for('virtual_devices'))
    
    # Validate VID/PID format (must be 4 hex characters)
    vid_pattern = re.compile(r'^[0-9a-f]{4}$')
    if not vid_pattern.match(vendor_id) or not vid_pattern.match(product_id):
        flash('Vendor ID and Product ID must be 4 hex characters (0-9, a-f)', 'danger')
        return redirect(url_for('virtual_devices'))
    
    # Create virtual device in database
    device = VirtualUsbDevice(
        name=name,
        device_type=device_type,
        vendor_id=vendor_id,
        product_id=product_id,
        serial_number=serial_number,
        config_json=config_json,
        storage_size=storage_size if device_type == 'storage' else 0
    )
    db.session.add(device)
    db.session.commit()  # Commit first to get device ID
    
    # Create storage if this is a storage device
    if device_type == 'storage':
        use_system_folder = 'use_system_folder' in request.form
        
        if use_system_folder:
            # Use existing system folder
            system_path = request.form.get('system_path', '').strip()
            
            # Get size limit for system folder
            try:
                system_storage_size = int(request.form.get('system_storage_size', 1024))
                if system_storage_size < 1 or system_storage_size > 16384:
                    system_storage_size = 1024
            except ValueError:
                system_storage_size = 1024
            
            # Validate path is provided
            if not system_path:
                flash('System folder path is required', 'danger')
                db.session.delete(device)
                db.session.commit()
                return redirect(url_for('virtual_devices'))
            
            # Create storage with system folder
            if not create_device_storage(device, system_storage_size, system_path):
                flash('Failed to create storage with specified system folder', 'danger')
                db.session.delete(device)
                db.session.commit()
                return redirect(url_for('virtual_devices'))
        else:
            # Create regular virtual storage
            create_device_storage(device, storage_size)
    
    # Log creation
    log_message = f'Created virtual device: {name} ({vendor_id}:{product_id})'
    if device_type == 'storage':
        if 'use_system_folder' in request.form:
            system_path = request.form.get('system_path', '').strip()
            system_storage_size = int(request.form.get('system_storage_size', 1024))
            log_message += f' with system folder {system_path} ({system_storage_size} MB)'
        else:
            log_message += f' with virtual storage {storage_size} MB'
    
    add_log_entry('INFO', log_message, 'virtual')
    
    flash(f'Virtual device "{name}" created', 'success')
    return redirect(url_for('virtual_devices'))


@app.route('/create_virtual_port', methods=['POST'])
@login_required
def create_virtual_port():
    """
    Create a new virtual USB port.
    
    Form Data:
        name (str): User-friendly port name
        port_number (str): Port identifier (auto-generated if empty)
        device_id (int): Optional device to connect to port
    
    Returns:
        Response: Redirect to virtual devices page with message
    """
    name = request.form.get('name')
    # Generate random port number if not provided
    port_number = request.form.get('port_number', f'vp{random.randint(0, 9999):04d}')
    device_id = request.form.get('device_id')
    
    # Validate name
    if not name:
        flash('Port name is required', 'danger')
        return redirect(url_for('virtual_devices'))
    
    # Create virtual port
    port = VirtualUsbPort(
        name=name,
        port_number=port_number,
        device_id=device_id if device_id else None
    )
    db.session.add(port)
    
    # Log creation
    add_log_entry('INFO', f'Created virtual port: {name} ({port_number})', 'virtual')
    
    flash(f'Virtual port "{name}" created', 'success')
    return redirect(url_for('virtual_devices'))


@app.route('/connect_virtual_device', methods=['POST'])
@login_required
def connect_virtual_device():
    """
    Connect a virtual device to a virtual port.
    
    Form Data:
        port_id (int): ID of the virtual port
        device_id (int): ID of the virtual device
    
    Returns:
        Response: Redirect to virtual devices page with message
    """
    port_id = request.form.get('port_id')
    device_id = request.form.get('device_id')
    
    # Get port and device from database
    port = VirtualUsbPort.query.get(port_id)
    device = VirtualUsbDevice.query.get(device_id)
    
    if not port or not device:
        flash('Port or device not found', 'danger')
        return redirect(url_for('virtual_devices'))
    
    # Connect device to port
    port.device_id = device.id
    port.is_connected = True
    device.is_active = True
    
    # Log connection
    add_log_entry('INFO', f'Device {device.name} connected to port {port.name}', 'virtual')
    
    flash(f'Device {device.name} connected to port {port.name}', 'success')
    return redirect(url_for('virtual_devices'))


@app.route('/disconnect_virtual_device', methods=['POST'])
@login_required
def disconnect_virtual_device():
    """
    Disconnect a virtual device from its port.
    
    Form Data:
        port_id (int): ID of the virtual port
    
    Returns:
        Response: Redirect to virtual devices page with message
    """
    port_id = request.form.get('port_id')
    
    # Get port from database
    port = VirtualUsbPort.query.get(port_id)
    
    if not port:
        flash('Port not found', 'danger')
        return redirect(url_for('virtual_devices'))
    
    # Save device name for logging
    device_name = "No device"
    if port.device:
        device_name = port.device.name
        port.device.is_active = False
    
    # Disconnect device from port
    port.device_id = None
    port.is_connected = False
    
    # Log disconnection
    add_log_entry('INFO', f'Device {device_name} disconnected from port {port.name}', 'virtual')
    
    flash(f'Device disconnected from port {port.name}', 'success')
    return redirect(url_for('virtual_devices'))


@app.route('/delete_virtual_device', methods=['POST'])
@login_required
def delete_virtual_device():
    """
    Delete a virtual USB device.
    
    Disconnects the device from all ports and removes its storage.
    
    Form Data:
        device_id (int): ID of the device to delete
    
    Returns:
        Response: Redirect to virtual devices page with message
    """
    device_id = request.form.get('device_id')
    
    # Get device from database
    device = VirtualUsbDevice.query.get(device_id)
    
    if not device:
        flash('Device not found', 'danger')
        return redirect(url_for('virtual_devices'))
    
    # Disconnect from all ports first
    for port in VirtualUsbPort.query.filter_by(device_id=device.id).all():
        port.device_id = None
        port.is_connected = False
    
    # Delete storage if this is a storage device
    if device.device_type == 'storage' and device.storage_path:
        delete_device_storage(device)
    
    # Delete the device
    device_name = device.name
    db.session.delete(device)
    
    # Log deletion
    add_log_entry('INFO', f'Virtual device {device_name} deleted', 'virtual')
    
    flash(f'Virtual device "{device_name}" deleted', 'success')
    return redirect(url_for('virtual_devices'))


@app.route('/delete_virtual_port', methods=['POST'])
@login_required
def delete_virtual_port():
    """
    Delete a virtual USB port.
    
    Form Data:
        port_id (int): ID of the port to delete
    
    Returns:
        Response: Redirect to virtual devices page with message
    """
    port_id = request.form.get('port_id')
    
    # Get port from database
    port = VirtualUsbPort.query.get(port_id)
    
    if not port:
        flash('Port not found', 'danger')
        return redirect(url_for('virtual_devices'))
    
    # Delete the port
    port_name = port.name
    db.session.delete(port)
    
    # Log deletion
    add_log_entry('INFO', f'Virtual port {port_name} deleted', 'virtual')
    
    flash(f'Virtual port "{port_name}" deleted', 'success')
    return redirect(url_for('virtual_devices'))


# ============================================================================
# VIRTUAL DEVICE USB/IP PUBLICATION
# ============================================================================

@app.route('/publish_virtual_device', methods=['POST'])
@login_required
def publish_virtual_device():
    """
    Publish a virtual USB device via USB/IP protocol.
    
    This registers the device with the virtual-fido USB/IP server,
    making it discoverable via 'usbip list -r localhost -p 3241'.
    
    Form Data:
        device_id (int): ID of the virtual device to publish
    
    Returns:
        Response: Redirect to virtual devices page with status message
    """
    import requests
    
    device_id = request.form.get('device_id')
    device = VirtualUsbDevice.query.get(device_id)
    
    if not device:
        flash('Device not found', 'danger')
        return redirect(url_for('virtual_devices'))
    
    if device.is_published:
        flash(f'Device "{device.name}" is already published', 'warning')
        return redirect(url_for('virtual_devices'))
    
    next_devnum = VirtualUsbDevice.query.filter_by(is_published=True).count() + 3
    busid = f"2-{next_devnum}"
    
    try:
        api_url = "http://127.0.0.1:3242/api/devices/register"
        payload = {
            "busid": busid,
            "device_type": device.device_type,
            "storage_path": device.storage_path or "",
            "size_mb": device.storage_size or 64,
            "name": device.name
        }
        
        response = requests.post(api_url, json=payload, timeout=5)
        
        if response.status_code == 200:
            device.is_published = True
            device.usbip_busid = busid
            device.is_active = True
            db.session.commit()
            
            add_log_entry('INFO', f'Virtual device {device.name} published on USB/IP bus {busid}', 'virtual')
            flash(f'Device "{device.name}" published successfully (Bus ID: {busid})', 'success')
        else:
            add_log_entry('ERROR', f'Failed to publish device {device.name}: API returned {response.status_code}', 'virtual')
            flash(f'Failed to publish device: API error', 'danger')
            
    except requests.exceptions.ConnectionError:
        device.is_published = True
        device.usbip_busid = busid
        device.is_active = True
        db.session.commit()
        
        add_log_entry('INFO', f'Virtual device {device.name} marked as published (Bus ID: {busid}) - API not available', 'virtual')
        flash(f'Device "{device.name}" published (Bus ID: {busid})', 'success')
        
    except Exception as e:
        add_log_entry('ERROR', f'Error publishing device {device.name}: {str(e)}', 'virtual')
        flash(f'Error publishing device: {str(e)}', 'danger')
    
    return redirect(url_for('virtual_devices'))


@app.route('/unpublish_virtual_device', methods=['POST'])
@login_required
def unpublish_virtual_device():
    """
    Unpublish a virtual USB device from USB/IP.
    
    Removes the device from the virtual-fido USB/IP server,
    making it no longer discoverable via USB/IP.
    
    Form Data:
        device_id (int): ID of the virtual device to unpublish
    
    Returns:
        Response: Redirect to virtual devices page with status message
    """
    import requests
    
    device_id = request.form.get('device_id')
    device = VirtualUsbDevice.query.get(device_id)
    
    if not device:
        flash('Device not found', 'danger')
        return redirect(url_for('virtual_devices'))
    
    if not device.is_published:
        flash(f'Device "{device.name}" is not published', 'warning')
        return redirect(url_for('virtual_devices'))
    
    try:
        if device.usbip_busid:
            api_url = "http://127.0.0.1:3242/api/devices/unregister"
            payload = {"busid": device.usbip_busid}
            
            try:
                requests.post(api_url, json=payload, timeout=5)
            except:
                pass
        
        device.is_published = False
        device.usbip_busid = None
        device.is_active = False
        db.session.commit()
        
        add_log_entry('INFO', f'Virtual device {device.name} unpublished from USB/IP', 'virtual')
        flash(f'Device "{device.name}" unpublished successfully', 'success')
        
    except Exception as e:
        add_log_entry('ERROR', f'Error unpublishing device {device.name}: {str(e)}', 'virtual')
        flash(f'Error unpublishing device: {str(e)}', 'danger')
    
    return redirect(url_for('virtual_devices'))


@app.route('/api/virtual_devices', methods=['GET'])
def api_get_virtual_devices():
    """
    API endpoint to get list of published virtual devices.
    
    This endpoint is used by the Remote Devices page to query
    virtual devices available on the USB/IP server.
    
    Returns:
        Response: JSON with list of published virtual devices
    """
    published_devices = VirtualUsbDevice.query.filter_by(is_published=True).all()
    
    devices = []
    for device in published_devices:
        devices.append({
            'busid': device.usbip_busid or f'v-{device.id}',
            'name': device.name,
            'device_type': device.device_type,
            'vendor_id': device.vendor_id,
            'product_id': device.product_id,
            'is_virtual': True,
            'storage_size': device.storage_size
        })
    
    return {'success': True, 'devices': devices}


# Note: Storage routes are registered via Blueprint (storage_bp)


# ============================================================================
# SYSTEM DIRECTORY BROWSER API
# ============================================================================

@app.route('/get_system_directories', methods=['GET'])
@login_required
def get_system_directories():
    """
    API to browse system directories.
    
    Returns list of directories and files in a given path.
    Used by the file browser when selecting system folders for virtual storage.
    
    Query Parameters:
        path (str): Directory path to browse (default: '/')
    
    Returns:
        Response: JSON with directory listing
                  {
                      'current_path': '/path/to/current',
                      'parent_path': '/path/to',
                      'writable': True/False,
                      'directories': [...],
                      'files': [...]
                  }
    """
    base_path = request.args.get('path', '/')
    
    # Security: Normalize path and prevent directory traversal
    base_path = os.path.normpath(base_path)
    if base_path.startswith('..'):
        base_path = '/'
    
    try:
        dirs = []
        files = []
        
        # List directory contents
        for item in os.listdir(base_path):
            full_path = os.path.join(base_path, item)
            
            # Skip hidden files and folders
            if item.startswith('.'):
                continue
            
            if os.path.isdir(full_path):
                # Check write permission for directories
                writable = os.access(full_path, os.W_OK)
                dirs.append({
                    'name': item,
                    'path': full_path,
                    'writable': writable
                })
            else:
                # Include file information
                size = os.path.getsize(full_path)
                files.append({
                    'name': item,
                    'path': full_path,
                    'size': size
                })
        
        # Get parent directory path
        parent_dir = os.path.dirname(base_path) if base_path != '/' else '/'
        
        # Check if current directory is writable
        current_writable = os.access(base_path, os.W_OK)
        
        return jsonify({
            'current_path': base_path,
            'parent_path': parent_dir,
            'writable': current_writable,
            'directories': dirs,
            'files': files
        })
    
    except Exception as e:
        return jsonify({
            'error': str(e),
            'current_path': base_path
        }), 500


# ============================================================================
# ERROR HANDLERS
# ============================================================================

@app.errorhandler(400)
def bad_request(error):
    """Handle 400 Bad Request errors."""
    return render_template('error.html', 
                          error_code="400",
                          error_title="Bad Request",
                          error_description="The server could not process your request due to invalid data. Please check your input and try again."), 400


@app.errorhandler(401)
def unauthorized(error):
    """Handle 401 Unauthorized errors."""
    return render_template('error.html', 
                          error_code="401",
                          error_title="Unauthorized",
                          error_description="Authentication is required to access this page. Please log in."), 401


@app.errorhandler(403)
def forbidden(error):
    """Handle 403 Forbidden errors."""
    return render_template('error.html', 
                          error_code="403",
                          error_title="Access Forbidden",
                          error_description="You do not have permission to access this page."), 403


@app.errorhandler(404)
def page_not_found(error):
    """Handle 404 Not Found errors."""
    return render_template('error.html', 
                          error_code="404",
                          error_title="Page Not Found",
                          error_description="The requested page does not exist. It may have been moved or deleted."), 404


@app.errorhandler(500)
def internal_server_error(error):
    """Handle 500 Internal Server errors."""
    return render_template('error.html', 
                          error_code="500",
                          error_title="Internal Server Error",
                          error_description="An unexpected error occurred on the server. Our team is working to fix it."), 500


@app.errorhandler(503)
def service_unavailable(error):
    """Handle 503 Service Unavailable errors."""
    return render_template('error.html', 
                          error_code="503",
                          error_title="Service Unavailable",
                          error_description="The service is temporarily unavailable. Please try again later."), 503


@app.errorhandler(Exception)
def handle_exception(error):
    """
    Handle all other unhandled exceptions.
    
    This is a catch-all error handler for any exception that
    isn't handled by the specific error handlers above.
    """
    # Get HTTP code if available
    if hasattr(error, 'code'):
        code = error.code
    else:
        code = 500
    
    # Log the error
    app.logger.error(f"Unhandled error: {error}")
    
    return render_template('error.html', 
                          error_code=str(code),
                          error_title="Server Error",
                          error_description="An unexpected error occurred. Please try again later or contact the administrator."), code


# ============================================================================
# DIAGNOSTIC ROUTES
# ============================================================================

@app.route('/api/run_doctor', methods=['POST'])
@login_required
def run_doctor():
    """
    Run the diagnostic script (doctor.sh).
    
    Executes the doctor.sh script which checks system status,
    USB/IP configuration, and diagnoses common issues.
    
    Returns:
        Response: JSON with diagnostic output
                  {
                      'success': True/False,
                      'output': 'diagnostic output...',
                      'message': 'status message'
                  }
    """
    try:
        # Get path to doctor.sh script
        script_dir = os.path.dirname(os.path.abspath(__file__))
        doctor_script = os.path.join(script_dir, 'doctor.sh')
        
        # Check if script exists
        if not os.path.exists(doctor_script):
            return jsonify({
                'success': False,
                'message': 'doctor.sh script not found'
            }), 404
        
        # Ensure script is executable
        os.chmod(doctor_script, 0o755)
        
        # Run doctor.sh with sudo (non-interactive mode with -n flag)
        process = subprocess.Popen(
            ['sudo', '-n', doctor_script], 
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            universal_newlines=True
        )
        
        stdout, stderr = process.communicate()
        
        # Log result
        if process.returncode == 0:
            add_log_entry('INFO', 'doctor.sh executed successfully', 'system')
        else:
            add_log_entry('ERROR', f'Error executing doctor.sh: {stderr}', 'system')
        
        # Format output for display
        output = stdout if stdout else "No output"
        if stderr:
            output += f"\n\nErrors:\n{stderr}"
        
        return jsonify({
            'success': process.returncode == 0,
            'output': output,
            'message': 'Diagnostics completed successfully' if process.returncode == 0 else 'Error during diagnostics'
        })
    except Exception as e:
        add_log_entry('ERROR', f'Exception running doctor.sh: {str(e)}', 'system')
        return jsonify({
            'success': False,
            'message': f'Error: {str(e)}'
        }), 500


# ============================================================================
# TERMINAL ROUTES
# ============================================================================

@app.route('/terminal')
@login_required
def terminal():
    """
    Web terminal page.
    
    Provides a web-based terminal interface for executing
    shell commands with saved command shortcuts.
    
    Returns:
        Response: Rendered terminal.html template
    """
    try:
        add_log_entry('DEBUG', f'Terminal page accessed by user: {current_user.username}', 'terminal')
        
        # Get user's saved commands
        try:
            add_log_entry('DEBUG', 'Checking TerminalCommand model availability', 'terminal')
            user_commands = TerminalCommand.query.filter_by(user_id=current_user.id).order_by(TerminalCommand.created_at.desc()).all()
            add_log_entry('DEBUG', f'Found {len(user_commands)} terminal commands for user', 'terminal')
        except Exception as e:
            add_log_entry('ERROR', f'TerminalCommand model error: {str(e)}', 'terminal')
            user_commands = []
        
        # Render template
        try:
            add_log_entry('DEBUG', 'Attempting to render terminal.html template', 'terminal')
            result = render_template('terminal.html', user_commands=user_commands)
            add_log_entry('DEBUG', 'Terminal template rendered successfully', 'terminal')
            return result
        except Exception as e:
            add_log_entry('ERROR', f'Template rendering error: {str(e)}', 'terminal')
            raise
            
    except Exception as e:
        add_log_entry('ERROR', f'Terminal page error: {str(e)}', 'terminal')
        return render_template('error.html', 
                             error_code=500,
                             error_message="Error loading terminal",
                             error_details=str(e))


@app.route('/terminal/execute', methods=['POST'])
@login_required
def execute_terminal_command():
    """
    Execute a shell command from the web terminal.
    
    WARNING: This executes arbitrary shell commands. Ensure proper
    access controls and consider limiting allowed commands.
    
    Request JSON:
        command (str): Shell command to execute
    
    Returns:
        Response: JSON with command output
                  {
                      'success': True/False,
                      'output': 'stdout...',
                      'error': 'stderr...',
                      'return_code': 0,
                      'command': 'executed command'
                  }
    """
    try:
        data = request.get_json()
        command = data.get('command', '').strip()
        
        # Validate command is not empty
        if not command:
            return jsonify({
                'success': False,
                'message': 'Command cannot be empty'
            }), 400
        
        # Log command execution
        add_log_entry('INFO', f'Terminal command executed: {command}', 'terminal')
        
        # Execute the command
        try:
            result = subprocess.run(
                command,
                shell=True,               # Execute through shell
                capture_output=True,      # Capture stdout and stderr
                text=True,                # Return string output
                timeout=30,               # 30 second timeout
                cwd=os.getcwd()           # Use current working directory
            )
            
            output = result.stdout
            error = result.stderr
            return_code = result.returncode
            
            # Build response
            response_data = {
                'success': True,
                'output': output,
                'error': error,
                'return_code': return_code,
                'command': command
            }
            
            return jsonify(response_data)
            
        except subprocess.TimeoutExpired:
            return jsonify({
                'success': False,
                'message': 'Command timed out (30 second limit)',
                'command': command
            }), 408
            
        except Exception as e:
            return jsonify({
                'success': False,
                'message': f'Error executing command: {str(e)}',
                'command': command
            }), 500
            
    except Exception as e:
        add_log_entry('ERROR', f'Terminal API error: {str(e)}', 'terminal')
        return jsonify({
            'success': False,
            'message': f'Server error: {str(e)}'
        }), 500


@app.route('/terminal/commands', methods=['POST'])
@login_required
def create_terminal_command():
    """
    Create a new saved terminal command button.
    
    Form Data:
        name (str): Button label
        command (str): Command to execute
        description (str): Optional description
    
    Returns:
        Response: Redirect to terminal page with message
    """
    try:
        name = request.form.get('name', '').strip()
        command = request.form.get('command', '').strip()
        description = request.form.get('description', '').strip()
        
        # Validate required fields
        if not name or not command:
            flash('Name and command are required', 'danger')
            return redirect(url_for('terminal'))
        
        # Check for duplicate name
        existing_command = TerminalCommand.query.filter_by(
            user_id=current_user.id,
            name=name
        ).first()
        
        if existing_command:
            flash('A command with this name already exists', 'warning')
            return redirect(url_for('terminal'))
        
        # Create new command
        new_command = TerminalCommand(
            name=name,
            command=command,
            description=description,
            user_id=current_user.id
        )
        
        db.session.add(new_command)
        db.session.commit()
        
        flash(f'Command "{name}" created successfully', 'success')
        add_log_entry('INFO', f'Terminal command created: {name}', 'terminal')
        
        return redirect(url_for('terminal'))
        
    except Exception as e:
        db.session.rollback()
        add_log_entry('ERROR', f'Error creating terminal command: {str(e)}', 'terminal')
        flash(f'Error creating command: {str(e)}', 'danger')
        return redirect(url_for('terminal'))


@app.route('/terminal/commands/<int:command_id>', methods=['POST'])
@login_required
def update_terminal_command(command_id):
    """
    Update an existing terminal command button.
    
    Args:
        command_id (int): ID of the command to update
    
    Form Data:
        name (str): New button label
        command (str): New command to execute
        description (str): New description
    
    Returns:
        Response: Redirect to terminal page with message
    """
    try:
        # Find the command (must belong to current user)
        command_obj = TerminalCommand.query.filter_by(
            id=command_id,
            user_id=current_user.id
        ).first()
        
        if not command_obj:
            flash('Command not found', 'danger')
            return redirect(url_for('terminal'))
        
        name = request.form.get('name', '').strip()
        command = request.form.get('command', '').strip()
        description = request.form.get('description', '').strip()
        
        # Validate required fields
        if not name or not command:
            flash('Name and command are required', 'danger')
            return redirect(url_for('terminal'))
        
        # Check for duplicate name (excluding current command)
        existing_command = TerminalCommand.query.filter_by(
            user_id=current_user.id,
            name=name
        ).filter(TerminalCommand.id != command_id).first()
        
        if existing_command:
            flash('A command with this name already exists', 'warning')
            return redirect(url_for('terminal'))
        
        # Update command
        command_obj.name = name
        command_obj.command = command
        command_obj.description = description
        command_obj.updated_at = datetime.utcnow()
        
        db.session.commit()
        
        flash(f'Command "{name}" updated successfully', 'success')
        add_log_entry('INFO', f'Terminal command updated: {name}', 'terminal')
        
        return redirect(url_for('terminal'))
        
    except Exception as e:
        db.session.rollback()
        add_log_entry('ERROR', f'Error updating terminal command: {str(e)}', 'terminal')
        flash(f'Error updating command: {str(e)}', 'danger')
        return redirect(url_for('terminal'))


@app.route('/terminal/commands/<int:command_id>/delete', methods=['POST'])
@login_required
def delete_terminal_command(command_id):
    """
    Delete a terminal command button.
    
    Args:
        command_id (int): ID of the command to delete
    
    Returns:
        Response: Redirect to terminal page with message
    """
    try:
        # Find the command (must belong to current user)
        command_obj = TerminalCommand.query.filter_by(
            id=command_id,
            user_id=current_user.id
        ).first()
        
        if not command_obj:
            flash('Command not found', 'danger')
            return redirect(url_for('terminal'))
        
        command_name = command_obj.name
        db.session.delete(command_obj)
        db.session.commit()
        
        flash(f'Command "{command_name}" deleted successfully', 'success')
        add_log_entry('INFO', f'Terminal command deleted: {command_name}', 'terminal')
        
        return redirect(url_for('terminal'))
        
    except Exception as e:
        db.session.rollback()
        add_log_entry('ERROR', f'Error deleting terminal command: {str(e)}', 'terminal')
        flash(f'Error deleting command: {str(e)}', 'danger')
        return redirect(url_for('terminal'))


# ============================================================================
# DEVELOPMENT SERVER
# ============================================================================

if __name__ == '__main__':
    # Run the development server
    # Only used when running main.py directly, not through Gunicorn
    # WARNING: Do not use debug=True in production!
    app.run(host="0.0.0.0", port=5000, debug=True)
