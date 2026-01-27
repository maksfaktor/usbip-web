"""
Database Models for Orange USB/IP Web Interface
================================================

This module defines all SQLAlchemy ORM models for the application database.
Models represent database tables and provide an object-oriented interface
for database operations.

File: models.py
Project: Orange USB/IP Web Interface
Purpose: Define database schema and data models

Database Tables:
    - users: User accounts for authentication
    - device_aliases: Custom names for USB devices
    - usb_ports: USB port configurations
    - logs: System event logging
    - virtual_usb_devices: Virtual USB device configurations
    - virtual_usb_files: Files stored on virtual USB storage devices
    - virtual_usb_ports: Virtual USB port mappings
    - terminal_commands: Saved terminal command shortcuts
    - fido_devices: FIDO2 virtual device settings
    - fido_credentials: FIDO2 credential metadata
    - fido_logs: FIDO2 operation audit logs
"""

# Flask-Login provides user session management (login/logout/remember me)
from flask_login import UserMixin

# Flask-SQLAlchemy is the Flask wrapper for SQLAlchemy ORM
from flask_sqlalchemy import SQLAlchemy

# Python's datetime module for timestamp fields
from datetime import datetime

# Import the database instance from the main app module
# This ensures all models use the same SQLAlchemy instance
from app import db

# Werkzeug provides secure password hashing utilities
# generate_password_hash: Creates a salted hash of a password
# check_password_hash: Verifies a password against its hash
from werkzeug.security import generate_password_hash, check_password_hash


class User(UserMixin, db.Model):
    """
    User Model - Represents a user account in the system.
    
    Inherits from:
        UserMixin: Provides default Flask-Login implementations for:
                   is_authenticated, is_active, is_anonymous, get_id()
        db.Model: SQLAlchemy base model class
    
    Attributes:
        id (int): Primary key, unique user identifier
        username (str): Unique username for login (max 64 chars)
        password_hash (str): Bcrypt hash of user's password (max 256 chars)
        is_admin (bool): True if user has administrator privileges
        created_at (datetime): Timestamp when account was created
        updated_at (datetime): Timestamp of last account modification
    """
    # Define the database table name explicitly
    __tablename__ = 'users'
    
    # Primary key column - auto-incrementing integer
    id = db.Column(db.Integer, primary_key=True)
    
    # Username field - must be unique, cannot be null
    # Max 64 characters to balance storage and usability
    username = db.Column(db.String(64), unique=True, nullable=False)
    
    # Password hash storage - 256 chars accommodates most hash algorithms
    # NEVER store plaintext passwords!
    password_hash = db.Column(db.String(256), nullable=False)
    
    # Admin flag - False by default, only admins can manage users
    is_admin = db.Column(db.Boolean, default=False)
    
    # Audit timestamps - automatically set on create/update
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    def set_password(self, password):
        """
        Hash and store a new password for this user.
        
        Uses Werkzeug's generate_password_hash which applies:
        - A cryptographically secure hash algorithm (scrypt by default)
        - A random salt to prevent rainbow table attacks
        
        Args:
            password (str): The plaintext password to hash and store
        """
        self.password_hash = generate_password_hash(password)
        
    def check_password(self, password):
        """
        Verify a password against the stored hash.
        
        Args:
            password (str): The plaintext password to verify
            
        Returns:
            bool: True if password matches, False otherwise
        """
        return check_password_hash(self.password_hash, password)
        
    def get_id(self):
        """
        Return the user's unique identifier as a string.
        
        Required by Flask-Login for session management.
        Must return a string (not int) for compatibility.
        
        Returns:
            str: The user's ID as a string
        """
        return str(self.id)


class DeviceAlias(db.Model):
    """
    Device Alias Model - Stores custom friendly names for USB devices.
    
    Users can assign memorable names to USB devices instead of
    remembering cryptic bus IDs like "1-1.2".
    
    Attributes:
        id (int): Primary key
        busid (str): The USB bus ID (e.g., "1-1.2", "2-3")
        device_info (str): Original device description from system
        alias (str): User-defined friendly name for the device
        created_at (datetime): When the alias was created
        updated_at (datetime): When the alias was last modified
    """
    __tablename__ = 'device_aliases'
    
    id = db.Column(db.Integer, primary_key=True)
    
    # USB bus ID - format varies by system (e.g., "1-1", "1-1.2", "2-3.4")
    busid = db.Column(db.String(64), nullable=False)
    
    # Original device info from lsusb/usbip (e.g., "Logitech USB Mouse")
    device_info = db.Column(db.String(256))
    
    # User-friendly alias (e.g., "My Keyboard", "Security Key")
    alias = db.Column(db.String(64), nullable=False)
    
    # Audit timestamps
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    def __repr__(self):
        """String representation for debugging."""
        return f'<DeviceAlias {self.busid}: {self.alias}>'


class UsbPort(db.Model):
    """
    USB Port Model - Stores custom names for USB port locations.
    
    Helps users identify physical USB port locations by assigning
    memorable names (e.g., "Front Panel Left", "Back USB 3.0").
    
    Attributes:
        id (int): Primary key
        port_number (str): System port identifier
        custom_name (str): User-defined name for the port location
        created_at (datetime): When the port name was created
        updated_at (datetime): When the port name was last modified
    """
    __tablename__ = 'usb_ports'
    
    id = db.Column(db.Integer, primary_key=True)
    
    # System-assigned port number/identifier
    port_number = db.Column(db.String(16), nullable=False)
    
    # User-friendly port name
    custom_name = db.Column(db.String(64))
    
    # Audit timestamps
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    def __repr__(self):
        """String representation for debugging."""
        return f'<UsbPort {self.port_number}: {self.custom_name}>'


class LogEntry(db.Model):
    """
    Log Entry Model - Stores system event logs for auditing and debugging.
    
    All significant operations are logged here for troubleshooting
    and security auditing purposes.
    
    Log Levels:
        DEBUG: Detailed diagnostic information
        INFO: General operational events
        WARNING: Potential issues that need attention
        ERROR: Failures that prevented an operation
    
    Attributes:
        id (int): Primary key
        timestamp (datetime): When the event occurred
        level (str): Severity level (DEBUG/INFO/WARNING/ERROR)
        message (str): Description of the event
        source (str): Component that generated the log
    """
    __tablename__ = 'logs'
    
    id = db.Column(db.Integer, primary_key=True)
    
    # Timestamp defaults to current UTC time
    timestamp = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Log level - one of: INFO, WARNING, ERROR, DEBUG
    level = db.Column(db.String(16), nullable=False)
    
    # Log message - can be long, so using Text type
    message = db.Column(db.Text, nullable=False)
    
    # Source component - identifies which part of the system generated the log
    # Examples: "system", "usbip", "auth", "fido", "storage"
    source = db.Column(db.String(64))
    
    def __repr__(self):
        """String representation showing timestamp, level, and truncated message."""
        return f'<LogEntry {self.timestamp} {self.level}: {self.message[:30]}>'


class VirtualUsbDevice(db.Model):
    """
    Virtual USB Device Model - Configurations for emulated USB devices.
    
    The system can create virtual USB devices that appear as real hardware
    to attached clients. This is useful for virtual storage, HID devices,
    and FIDO2 security keys.
    
    Device Types:
        - hid: Human Interface Device (keyboard, mouse)
        - storage: Mass storage device (virtual flash drive)
        - serial: Serial/COM port emulation
        - fido: FIDO2/U2F security key
    
    Attributes:
        id (int): Primary key
        name (str): User-friendly device name
        device_type (str): Type of virtual device
        vendor_id (str): USB Vendor ID in hex (e.g., "1d6b")
        product_id (str): USB Product ID in hex (e.g., "0002")
        serial_number (str): Optional device serial number
        is_active (bool): Whether device is currently running
        config_json (str): JSON configuration for device-specific settings
        storage_size (int): Size in MB for storage devices
        storage_path (str): File path to storage directory
        is_system_path (bool): True if using a system directory
        created_at (datetime): Creation timestamp
        updated_at (datetime): Last modification timestamp
    """
    __tablename__ = 'virtual_usb_devices'
    
    id = db.Column(db.Integer, primary_key=True)
    
    # User-friendly name for the device
    name = db.Column(db.String(64), nullable=False)
    
    # Device type determines behavior and capabilities
    device_type = db.Column(db.String(32), nullable=False)
    
    # USB Vendor ID - 4 hex digits (e.g., "1d6b" for Linux Foundation)
    vendor_id = db.Column(db.String(6), nullable=False)
    
    # USB Product ID - 4 hex digits (e.g., "0002" for root hub)
    product_id = db.Column(db.String(6), nullable=False)
    
    # Optional serial number for device identification
    serial_number = db.Column(db.String(32))
    
    # Running state - True when device is actively emulating
    is_active = db.Column(db.Boolean, default=False)
    
    # JSON configuration for device-specific parameters
    config_json = db.Column(db.Text)
    
    # Storage device specific fields
    storage_size = db.Column(db.Integer, default=0)  # Size in MB
    storage_path = db.Column(db.String(256))  # Path to storage files
    is_system_path = db.Column(db.Boolean, default=False)  # Using system folder flag
    
    # Audit timestamps
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # USB/IP publication state
    is_published = db.Column(db.Boolean, default=False)  # True when device is published via USB/IP
    usbip_busid = db.Column(db.String(16))  # Bus ID for USB/IP (e.g., "2-3")
    
    def __repr__(self):
        """String representation showing name and USB IDs."""
        return f'<VirtualUsbDevice {self.name} ({self.vendor_id}:{self.product_id})>'


class VirtualUsbFile(db.Model):
    """
    Virtual USB File Model - Tracks files stored on virtual storage devices.
    
    When a virtual USB storage device is created, this table tracks
    all files that are "stored" on it, allowing the web interface
    to manage virtual storage contents.
    
    Attributes:
        id (int): Primary key
        device_id (int): Foreign key to parent VirtualUsbDevice
        filename (str): Original filename
        file_path (str): Relative path within device storage
        file_size (int): File size in bytes
        file_type (str): MIME type or file extension
        created_at (datetime): When file was added
        updated_at (datetime): When file was last modified
        device: Relationship to parent VirtualUsbDevice
    """
    __tablename__ = 'virtual_usb_files'
    
    id = db.Column(db.Integer, primary_key=True)
    
    # Foreign key linking to the parent virtual device
    device_id = db.Column(db.Integer, db.ForeignKey('virtual_usb_devices.id'))
    
    # Original filename as uploaded/created
    filename = db.Column(db.String(256), nullable=False)
    
    # Relative path within the device's storage directory
    file_path = db.Column(db.String(512), nullable=False)
    
    # File size in bytes for storage quota tracking
    file_size = db.Column(db.Integer, default=0)
    
    # File type/MIME type for display and handling
    file_type = db.Column(db.String(64))
    
    # Audit timestamps
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # SQLAlchemy relationship - allows device.files access
    # backref creates reverse relationship: file.device
    device = db.relationship('VirtualUsbDevice', backref=db.backref('files', lazy=True))
    
    def __repr__(self):
        """String representation showing filename and size."""
        return f'<VirtualUsbFile {self.filename} ({self.file_size} bytes)>'


class VirtualUsbPort(db.Model):
    """
    Virtual USB Port Model - Maps virtual devices to port numbers.
    
    Manages the virtual port assignments for USB/IP connections,
    tracking which virtual device is connected to which port.
    
    Attributes:
        id (int): Primary key
        name (str): User-friendly port name
        port_number (str): Virtual port identifier
        device_id (int): Foreign key to connected device
        is_connected (bool): Current connection state
        created_at (datetime): Creation timestamp
        updated_at (datetime): Last modification timestamp
        device: Relationship to connected VirtualUsbDevice
    """
    __tablename__ = 'virtual_usb_ports'
    
    id = db.Column(db.Integer, primary_key=True)
    
    # User-friendly name for the virtual port
    name = db.Column(db.String(64), nullable=False)
    
    # Virtual port number/identifier
    port_number = db.Column(db.String(16))
    
    # Foreign key to connected virtual device (if any)
    device_id = db.Column(db.Integer, db.ForeignKey('virtual_usb_devices.id'))
    
    # Current connection state
    is_connected = db.Column(db.Boolean, default=False)
    
    # Audit timestamps
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationship to connected device
    device = db.relationship('VirtualUsbDevice', backref=db.backref('ports', lazy=True))
    
    def __repr__(self):
        """String representation showing port name and number."""
        return f'<VirtualUsbPort {self.name} ({self.port_number})>'


class TerminalCommand(db.Model):
    """
    Terminal Command Model - Saved command shortcuts for quick execution.
    
    Users can save frequently used terminal commands as buttons
    for one-click execution in the web terminal interface.
    
    Attributes:
        id (int): Primary key
        name (str): Button label/short name
        command (str): Full command to execute
        description (str): Optional explanation of what the command does
        user_id (int): Foreign key to owning user
        created_at (datetime): Creation timestamp
        updated_at (datetime): Last modification timestamp
        user: Relationship to owning User
    """
    __tablename__ = 'terminal_commands'
    
    id = db.Column(db.Integer, primary_key=True)
    
    # Short name displayed on the button (e.g., "Check USB", "Restart")
    name = db.Column(db.String(64), nullable=False)
    
    # Full command to execute when button is clicked
    command = db.Column(db.Text, nullable=False)
    
    # Optional longer description for tooltip/help
    description = db.Column(db.Text)
    
    # Foreign key - commands belong to specific users
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    
    # Audit timestamps
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationship to owning user - allows user.terminal_commands access
    user = db.relationship('User', backref=db.backref('terminal_commands', lazy=True))
    
    def __repr__(self):
        """String representation showing command name."""
        return f'<TerminalCommand {self.name}>'


class FidoDevice(db.Model):
    """
    FIDO Device Model - Settings and status for the virtual FIDO2/U2F device.
    
    This model tracks the virtual FIDO2 security key emulator state,
    including whether it's running, its process ID, and configuration.
    The virtual FIDO device emulates hardware security keys like YubiKey.
    
    Attributes:
        id (int): Primary key
        is_running (bool): Whether the FIDO device is currently active
        pid (int): Process ID of the running virtual-fido process
        started_at (datetime): When the device was last started
        stopped_at (datetime): When the device was last stopped
        auto_start (bool): Whether to start automatically on system boot
        vault_path (str): Path to the credential vault file
        passphrase_hash (str): Hashed passphrase for vault encryption
        last_error (str): Last error message if startup failed
        created_at (datetime): Record creation timestamp
        updated_at (datetime): Last modification timestamp
    """
    __tablename__ = 'fido_devices'
    
    id = db.Column(db.Integer, primary_key=True)
    
    # Running state - True when virtual-fido process is active
    is_running = db.Column(db.Boolean, default=False)
    
    # Process ID for the running virtual-fido daemon
    # Used to check if process is still alive and to stop it
    pid = db.Column(db.Integer, nullable=True)
    
    # Timestamps for tracking uptime and history
    started_at = db.Column(db.DateTime, nullable=True)
    stopped_at = db.Column(db.DateTime, nullable=True)
    
    # Auto-start flag for systemd service configuration
    auto_start = db.Column(db.Boolean, default=False)
    
    # Path to credential vault file (encrypted storage)
    # Can be set via FIDO_VAULT_PATH environment variable
    vault_path = db.Column(db.String(512), nullable=True)
    
    # Hashed passphrase for vault encryption
    # The actual passphrase is NEVER stored
    passphrase_hash = db.Column(db.String(256), nullable=True)
    
    # Last error message for troubleshooting
    last_error = db.Column(db.Text, nullable=True)
    
    # Audit timestamps
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    def __repr__(self):
        """String representation showing running status and PID."""
        status = 'Running' if self.is_running else 'Stopped'
        return f'<FidoDevice {status} (PID: {self.pid})>'


class FidoCredential(db.Model):
    """
    FIDO Credential Model - Metadata for stored FIDO2 credentials.
    
    Stores metadata about WebAuthn credentials registered with the
    virtual FIDO device. This is metadata only - actual cryptographic
    credentials are stored in the encrypted vault file.
    
    Note: This table provides visibility into registered credentials
    without exposing the actual private keys, which remain in the vault.
    
    Attributes:
        id (int): Primary key
        credential_id (str): Unique credential identifier from vault
        rp_id (str): Relying Party ID (usually the domain name)
        user_id (str): User identifier from the relying party
        username (str): Username or email associated with credential
        display_name (str): Human-readable display name
        created_at (datetime): When credential was registered
        last_used (datetime): When credential was last used for auth
        use_count (int): Number of times credential was used
    """
    __tablename__ = 'fido_credentials'
    
    id = db.Column(db.Integer, primary_key=True)
    
    # Unique credential ID from the FIDO2 protocol
    # Base64-encoded binary credential identifier
    credential_id = db.Column(db.String(256), unique=True, nullable=False)
    
    # Relying Party ID - typically the domain (e.g., "github.com")
    rp_id = db.Column(db.String(256), nullable=False)
    
    # User ID assigned by the relying party (opaque identifier)
    user_id = db.Column(db.String(256), nullable=True)
    
    # Username/email used during registration
    username = db.Column(db.String(256), nullable=True)
    
    # Human-readable display name
    display_name = db.Column(db.String(256), nullable=True)
    
    # Registration timestamp
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Last authentication timestamp
    last_used = db.Column(db.DateTime, nullable=True)
    
    # Usage counter for tracking authentication frequency
    use_count = db.Column(db.Integer, default=0)
    
    def __repr__(self):
        """String representation showing RP and username."""
        return f'<FidoCredential {self.rp_id} - {self.username}>'
    
    def to_dict(self):
        """
        Convert credential to dictionary for JSON API responses.
        
        Returns:
            dict: Credential data suitable for JSON serialization
        """
        return {
            'id': self.id,
            'credential_id': self.credential_id,
            'rp_id': self.rp_id,
            'user_id': self.user_id,
            'username': self.username,
            'display_name': self.display_name,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'last_used': self.last_used.isoformat() if self.last_used else None,
            'use_count': self.use_count
        }


class FidoLog(db.Model):
    """
    FIDO Log Model - Audit log for FIDO2 operations.
    
    Records all FIDO2-related events for security auditing,
    troubleshooting, and usage tracking. Includes device
    operations and credential operations.
    
    Event Types:
        - device_start: Virtual FIDO device started
        - device_stop: Virtual FIDO device stopped
        - registration: New credential registered (WebAuthn create)
        - authentication: Credential used for auth (WebAuthn get)
        - credential_delete: Credential was deleted
    
    Status Values:
        - success: Operation completed successfully
        - failed: Operation failed (check details)
        - pending: Operation in progress
    
    Attributes:
        id (int): Primary key
        timestamp (datetime): When the event occurred
        event_type (str): Type of operation performed
        rp_id (str): Relying Party ID for credential operations
        credential_id (str): Credential ID if applicable
        status (str): Operation result (success/failed/pending)
        details (str): Additional details or error messages
        ip_address (str): Client IP address for the request
        user_id (int): Foreign key to web interface user (if logged in)
        user: Relationship to User model
    """
    __tablename__ = 'fido_logs'
    
    id = db.Column(db.Integer, primary_key=True)
    
    # Event timestamp with index for efficient time-based queries
    timestamp = db.Column(db.DateTime, default=datetime.utcnow, index=True)
    
    # Event type categorizes the operation
    event_type = db.Column(db.String(64), nullable=False)
    
    # Relying Party ID for credential-related operations
    rp_id = db.Column(db.String(256), nullable=True)
    
    # Credential ID for operations involving a specific credential
    credential_id = db.Column(db.String(256), nullable=True)
    
    # Operation status: success, failed, or pending
    status = db.Column(db.String(32), nullable=False)
    
    # Additional details, error messages, or diagnostic info
    details = db.Column(db.Text, nullable=True)
    
    # Client IP address for security auditing
    ip_address = db.Column(db.String(64), nullable=True)
    
    # Foreign key to web interface user who initiated the operation
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=True)
    
    # Relationship to User for easy access to user data
    user = db.relationship('User', backref=db.backref('fido_logs', lazy=True))
    
    def __repr__(self):
        """String representation showing timestamp, event, and status."""
        return f'<FidoLog {self.timestamp} {self.event_type} - {self.status}>'
    
    def to_dict(self):
        """
        Convert log entry to dictionary for JSON API responses.
        
        Returns:
            dict: Log entry data suitable for JSON serialization
        """
        return {
            'id': self.id,
            'timestamp': self.timestamp.isoformat() if self.timestamp else None,
            'event_type': self.event_type,
            'rp_id': self.rp_id,
            'credential_id': self.credential_id,
            'status': self.status,
            'details': self.details,
            'ip_address': self.ip_address,
            'user_id': self.user_id
        }
