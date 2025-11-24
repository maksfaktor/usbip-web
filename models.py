from flask_login import UserMixin
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime
from app import db
from werkzeug.security import generate_password_hash, check_password_hash

class User(UserMixin, db.Model):
    __tablename__ = 'users'
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(64), unique=True, nullable=False)
    password_hash = db.Column(db.String(256), nullable=False)
    is_admin = db.Column(db.Boolean, default=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    def set_password(self, password):
        self.password_hash = generate_password_hash(password)
        
    def check_password(self, password):
        return check_password_hash(self.password_hash, password)
        
    def get_id(self):
        return str(self.id)

class DeviceAlias(db.Model):
    __tablename__ = 'device_aliases'
    id = db.Column(db.Integer, primary_key=True)
    busid = db.Column(db.String(64), nullable=False)
    device_info = db.Column(db.String(256))
    alias = db.Column(db.String(64), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    def __repr__(self):
        return f'<DeviceAlias {self.busid}: {self.alias}>'

class UsbPort(db.Model):
    __tablename__ = 'usb_ports'
    id = db.Column(db.Integer, primary_key=True)
    port_number = db.Column(db.String(16), nullable=False)
    custom_name = db.Column(db.String(64))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    def __repr__(self):
        return f'<UsbPort {self.port_number}: {self.custom_name}>'

class LogEntry(db.Model):
    __tablename__ = 'logs'
    id = db.Column(db.Integer, primary_key=True)
    timestamp = db.Column(db.DateTime, default=datetime.utcnow)
    level = db.Column(db.String(16), nullable=False)  # INFO, WARNING, ERROR, DEBUG
    message = db.Column(db.Text, nullable=False)
    source = db.Column(db.String(64))  # Источник лога: system, usbip, user, etc.
    
    def __repr__(self):
        return f'<LogEntry {self.timestamp} {self.level}: {self.message[:30]}>'

class VirtualUsbDevice(db.Model):
    __tablename__ = 'virtual_usb_devices'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(64), nullable=False)
    device_type = db.Column(db.String(32), nullable=False)  # hid, storage, serial, etc.
    vendor_id = db.Column(db.String(6), nullable=False)  # формат: 1d6b
    product_id = db.Column(db.String(6), nullable=False)  # формат: 0002
    serial_number = db.Column(db.String(32))
    is_active = db.Column(db.Boolean, default=False)
    config_json = db.Column(db.Text)  # JSON с конфигурацией устройства
    storage_size = db.Column(db.Integer, default=0)  # Размер хранилища в МБ (для storage устройств)
    storage_path = db.Column(db.String(256))  # Путь к директории с файлами устройства
    is_system_path = db.Column(db.Boolean, default=False)  # Флаг, указывающий, что используется системная папка
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    def __repr__(self):
        return f'<VirtualUsbDevice {self.name} ({self.vendor_id}:{self.product_id})>'

class VirtualUsbFile(db.Model):
    __tablename__ = 'virtual_usb_files'
    id = db.Column(db.Integer, primary_key=True)
    device_id = db.Column(db.Integer, db.ForeignKey('virtual_usb_devices.id'))
    filename = db.Column(db.String(256), nullable=False)
    file_path = db.Column(db.String(512), nullable=False)  # Относительный путь внутри storage_path
    file_size = db.Column(db.Integer, default=0)  # Размер файла в байтах
    file_type = db.Column(db.String(64))  # Тип файла
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Связь с виртуальным устройством
    device = db.relationship('VirtualUsbDevice', backref=db.backref('files', lazy=True))
    
    def __repr__(self):
        return f'<VirtualUsbFile {self.filename} ({self.file_size} bytes)>'

class VirtualUsbPort(db.Model):
    __tablename__ = 'virtual_usb_ports'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(64), nullable=False)
    port_number = db.Column(db.String(16))  # Виртуальный номер порта
    device_id = db.Column(db.Integer, db.ForeignKey('virtual_usb_devices.id'))
    is_connected = db.Column(db.Boolean, default=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Связь с виртуальным устройством
    device = db.relationship('VirtualUsbDevice', backref=db.backref('ports', lazy=True))
    
    def __repr__(self):
        return f'<VirtualUsbPort {self.name} ({self.port_number})>'


class TerminalCommand(db.Model):
    __tablename__ = 'terminal_commands'
    
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(64), nullable=False)  # Короткое название кнопки
    command = db.Column(db.Text, nullable=False)  # Команда для выполнения
    description = db.Column(db.Text)  # Описание команды
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Связь с пользователем
    user = db.relationship('User', backref=db.backref('terminal_commands', lazy=True))
    
    def __repr__(self):
        return f'<TerminalCommand {self.name}>'


class FidoDevice(db.Model):
    """FIDO2 Virtual Device settings and status"""
    __tablename__ = 'fido_devices'
    
    id = db.Column(db.Integer, primary_key=True)
    is_running = db.Column(db.Boolean, default=False)
    pid = db.Column(db.Integer, nullable=True)
    started_at = db.Column(db.DateTime, nullable=True)
    stopped_at = db.Column(db.DateTime, nullable=True)
    auto_start = db.Column(db.Boolean, default=False)
    vault_path = db.Column(db.String(512), nullable=True)  # Path determined dynamically from env or fido_utils
    passphrase_hash = db.Column(db.String(256), nullable=True)  # Хешированный passphrase
    last_error = db.Column(db.Text, nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    def __repr__(self):
        status = 'Running' if self.is_running else 'Stopped'
        return f'<FidoDevice {status} (PID: {self.pid})>'


class FidoCredential(db.Model):
    """Metadata for FIDO2 credentials (not the actual credentials)"""
    __tablename__ = 'fido_credentials'
    
    id = db.Column(db.Integer, primary_key=True)
    credential_id = db.Column(db.String(256), unique=True, nullable=False)  # ID из vault
    rp_id = db.Column(db.String(256), nullable=False)  # Relying Party ID (domain)
    user_id = db.Column(db.String(256), nullable=True)  # User ID
    username = db.Column(db.String(256), nullable=True)  # Username/email
    display_name = db.Column(db.String(256), nullable=True)  # Display name
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    last_used = db.Column(db.DateTime, nullable=True)
    use_count = db.Column(db.Integer, default=0)
    
    def __repr__(self):
        return f'<FidoCredential {self.rp_id} - {self.username}>'
    
    def to_dict(self):
        """Convert to dictionary for JSON serialization"""
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
    """Log of FIDO2 operations"""
    __tablename__ = 'fido_logs'
    
    id = db.Column(db.Integer, primary_key=True)
    timestamp = db.Column(db.DateTime, default=datetime.utcnow, index=True)
    event_type = db.Column(db.String(64), nullable=False)  # device_start, device_stop, registration, authentication, credential_delete
    rp_id = db.Column(db.String(256), nullable=True)  # Domain для credential операций
    credential_id = db.Column(db.String(256), nullable=True)  # ID credential если есть
    status = db.Column(db.String(32), nullable=False)  # success, failed, pending
    details = db.Column(db.Text, nullable=True)  # Дополнительные детали
    ip_address = db.Column(db.String(64), nullable=True)  # IP пользователя
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=True)
    
    # Связь с пользователем
    user = db.relationship('User', backref=db.backref('fido_logs', lazy=True))
    
    def __repr__(self):
        return f'<FidoLog {self.timestamp} {self.event_type} - {self.status}>'
    
    def to_dict(self):
        """Convert to dictionary for JSON serialization"""
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
