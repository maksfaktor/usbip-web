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
