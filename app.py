import os
import re
import json
import random
import logging
import socket
import subprocess
import netifaces
from flask import Flask, render_template, redirect, url_for, request, flash, jsonify, send_file, session
from flask_login import LoginManager, login_user, logout_user, login_required, current_user
from werkzeug.security import check_password_hash, generate_password_hash
from werkzeug.middleware.proxy_fix import ProxyFix
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy.ext.declarative import declarative_base
from datetime import datetime
from translations import get_translation

# Функция для добавления записей в журнал
def add_log_entry(level, message, source):
    """
    Добавляет запись в журнал логов.
    Все сообщения записываются на английском языке для обеспечения 
    единообразия при смене языка интерфейса.
    
    Args:
        level (str): Уровень логирования (INFO, WARNING, ERROR, DEBUG)
        message (str): Сообщение для записи (на английском)
        source (str): Источник сообщения (auth, system, usbip, etc.)
    """
    log_entry = LogEntry(level=level, message=message, source=source)
    db.session.add(log_entry)
    db.session.commit()
    logger.debug(f"Log added: [{level}] {message} (Source: {source})")


# Настройка логгирования
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

# Функция для получения информации о сетевых интерфейсах
def get_network_interfaces():
    """
    Получает информацию о сетевых интерфейсах (Ethernet и WiFi) и их IP-адресах.
    Возвращает словарь с интерфейсами и их адресами.
    """
    interfaces = {}
    try:
        # Получаем список всех интерфейсов
        all_interfaces = netifaces.interfaces()
        
        for iface in all_interfaces:
            # Пропускаем loopback и виртуальные интерфейсы
            if iface == 'lo' or 'docker' in iface or 'veth' in iface or 'br-' in iface:
                continue
                
            addrs = netifaces.ifaddresses(iface)
            # Проверяем наличие IPv4 адресов
            if netifaces.AF_INET in addrs:
                for addr in addrs[netifaces.AF_INET]:
                    ip = addr['addr']
                    # Пропускаем localhost
                    if ip.startswith('127.'):
                        continue
                    
                    # Определяем тип интерфейса (Ethernet или WiFi)
                    iface_type = 'Ethernet'
                    if iface.startswith('wl') or 'wlan' in iface or 'wifi' in iface.lower():
                        iface_type = 'WiFi'
                    
                    # Добавляем в словарь
                    if iface_type not in interfaces:
                        interfaces[iface_type] = []
                    interfaces[iface_type].append({
                        'name': iface,
                        'ip': ip,
                        'url': f'http://{ip}:5000'
                    })
        
        logger.debug(f"Найденные сетевые интерфейсы: {interfaces}")
    except Exception as e:
        logger.error(f"Ошибка при получении информации о сетевых интерфейсах: {str(e)}")
    
    return interfaces

# Создание базового класса для SQLAlchemy
Base = declarative_base()

# Инициализация SQLAlchemy с базовым классом
db = SQLAlchemy(model_class=Base)

# Создание Flask-приложения
app = Flask(__name__)
app.secret_key = os.environ.get("SESSION_SECRET", "default_secret_key_for_development")
app.wsgi_app = ProxyFix(app.wsgi_app, x_proto=1, x_host=1)

# Настройка базы данных SQLite
database_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'usbip_web.db')
app.config["SQLALCHEMY_DATABASE_URI"] = f"sqlite:///{database_path}"
app.config["SQLALCHEMY_ENGINE_OPTIONS"] = {
    "connect_args": {"check_same_thread": False}
}
db.init_app(app)

# Настройка Flask-Login
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = "login"

# Обработчик для неавторизованных запросов к API
@login_manager.unauthorized_handler
def unauthorized_handler():
    if request.path.startswith('/api/'):
        return jsonify({
            'success': False,
            'message': 'Unauthorized access. Please login.'
        }), 401
    return redirect(url_for('login'))

# Helper function to get current language
def get_current_language():
    """
    Получает текущий язык пользователя из сессии.
    Если язык не выбран, возвращает язык по умолчанию (английский).
    """
    return session.get('language', 'en')

# Add translation function to template context
@app.context_processor
def inject_translation():
    """
    Добавляет функцию перевода в контекст шаблона.
    """
    def translate(key, default=None):
        return get_translation(key, get_current_language()) if default is None else default
    return dict(t=translate)

# Импортирование утилит
from usbip_utils import get_local_usb_devices, bind_device, get_remote_usb_devices, attach_device, detach_device, get_attached_devices, get_published_devices

# Импортирование моделей (после настройки db)
from models import User, DeviceAlias, UsbPort, LogEntry, VirtualUsbDevice, VirtualUsbPort, VirtualUsbFile, TerminalCommand

# Импортирование модулей для управления виртуальным хранилищем
from virtual_storage_utils import (
    create_device_storage, delete_device_storage, resize_device_storage,
    get_device_storage_usage, list_device_files, create_directory,
    delete_item, upload_file, get_storage_stats, download_file
)
from storage_routes import storage_bp

# Регистрация Blueprint для управления хранилищем
app.register_blueprint(storage_bp)

# Инициализация базы данных
with app.app_context():
    db.create_all()
    # Создание администратора, если он не существует
    admin_user = User.query.filter_by(username='admin').first()
    if not admin_user:
        admin_user = User(username='admin', is_admin=True)
        admin_user.set_password('admin')
        db.session.add(admin_user)
        db.session.commit()
        logger.info("Создан пользователь admin")

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        
        user = User.query.filter_by(username=username).first()
        if user and user.check_password(password):
            login_user(user)
            # Запись в лог
            add_log_entry('INFO', f'User {username} logged in successfully', 'auth')
            
            # Добавляем текущее время к сообщению об успешном входе
            current_time = datetime.now().strftime('%H:%M:%S')
            flash(f'Вход выполнен успешно! [{current_time}]', 'login-success')
            return redirect(url_for('index'))
        else:
            # Запись в лог о неудачной попытке
            if username:
                add_log_entry('WARNING', f'Failed login attempt for user {username}', 'auth')
            
            # Добавляем время и подсказку о проверке раскладки/Caps Lock
            current_time = datetime.now().strftime('%H:%M:%S')
            flash(f'Неверное имя пользователя или пароль. [{current_time}] Проверьте раскладку клавиатуры и состояние Caps Lock.', 'login-error')
    
    # Получаем информацию о сетевых интерфейсах
    network_interfaces = get_network_interfaces()
    return render_template('login.html', network_interfaces=network_interfaces)

@app.route('/set_language/<language>')
def set_language(language):
    """
    Устанавливает язык интерфейса.
    
    Args:
        language (str): Код языка ('en' или 'ru')
    """
    if language in ['en', 'ru']:
        session['language'] = language
    
    # Перенаправляем на предыдущую страницу или на главную
    next_page = request.args.get('next') or request.referrer or url_for('index')
    return redirect(next_page)

@app.route('/logout')
@login_required
def logout():
    username = current_user.username
    logout_user()
    
    # Запись в лог
    add_log_entry('INFO', f'User {username} logged out', 'auth')
    
    # Используем функцию перевода
    lang = get_current_language()
    message = 'You have been logged out' if lang == 'en' else 'Вы вышли из системы'
    flash(message, 'info')
    return redirect(url_for('login'))

@app.route('/api/local_devices')
@login_required
def get_local_devices_api():
    """
    API для получения списка локальных USB устройств.
    Возвращает JSON с устройствами для обновления списка без перезагрузки страницы.
    """
    try:
        # Получаем реальные USB устройства через usbip
        local_devices = get_local_usb_devices()
        
        # Получаем список опубликованных устройств
        published_busids = get_published_devices()
        add_log_entry('DEBUG', f'API: Published devices: {published_busids}', 'usbip')
        
        # Помечаем опубликованные устройства
        for device in local_devices:
            # Нормализуем busid устройства для правильного сравнения
            if 'busid' in device:
                from usbip_utils import normalize_busid
                device_busid = normalize_busid(device['busid'])
                if device_busid in published_busids:
                    device['is_published'] = True
                    add_log_entry('DEBUG', f'API: Device {device["busid"]} marked as published', 'usbip')
                else:
                    device['is_published'] = False
                    add_log_entry('DEBUG', f'API: Device {device["busid"]} NOT marked as published', 'usbip')
            else:
                device['is_published'] = False
        
        # Добавляем виртуальные устройства в список локальных устройств
        virtual_devices = VirtualUsbDevice.query.filter_by(is_active=False).all()
        
        for device in virtual_devices:
            local_devices.append({
                'busid': f'v-{device.id}',
                'device_name': device.name,
                'idVendor': device.vendor_id,
                'idProduct': device.product_id,
                'is_virtual': True,
                'virtual_id': device.id,
                'is_published': False  # Виртуальные устройства не публикуются
            })
        
        # Запись в лог
        add_log_entry('INFO', f'USB device list refreshed via API, found {len(local_devices)} devices', 'system')
        
        return jsonify({
            'success': True,
            'devices': local_devices
        })
    except Exception as e:
        # Запись в лог
        add_log_entry('ERROR', f'Failed to get USB devices list: {str(e)}', 'system')
        return jsonify({
            'success': False,
            'message': str(e)
        }), 500

@app.route('/')
@login_required
def index():
    # Получаем реальные USB устройства через usbip
    local_devices = get_local_usb_devices()
    
    # Получаем список опубликованных устройств
    published_busids = get_published_devices()
    
    # Добавляем отладочное логирование
    add_log_entry('DEBUG', f'Published devices: {published_busids}', 'usbip')
    
    # Помечаем опубликованные устройства
    for device in local_devices:
        # Нормализуем busid устройства для правильного сравнения
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
            
    attached_devices = get_attached_devices()
    
    # Добавляем виртуальные устройства в список локальных устройств
    virtual_devices = VirtualUsbDevice.query.filter_by(is_active=False).all()
    for device in virtual_devices:
        local_devices.append({
            'busid': f'v-{device.id}',  # Добавляем префикс, чтобы отличать от реальных устройств
            'device_name': f'{device.name} (Виртуальное)',
            'vendor_id': device.vendor_id,
            'product_id': device.product_id,
            'is_virtual': True,
            'virtual_id': device.id
        })
    
    # Добавляем подключенные виртуальные устройства в список подключенных устройств
    connected_virtual_ports = VirtualUsbPort.query.filter_by(is_connected=True).all()
    for port in connected_virtual_ports:
        if port.device:
            attached_devices.append({
                'port': f'v-{port.port_number}',
                'device_name': f'{port.device.name} (Виртуальное)',
                'remote_busid': f'{port.device.vendor_id}:{port.device.product_id}',
                'remote_host': 'local-virtual',
                'is_virtual': True,
                'virtual_port_id': port.id,
                'virtual_device_id': port.device.id
            })
    
    # Получаем свободные виртуальные порты для модального окна подключения
    available_virtual_ports = VirtualUsbPort.query.filter_by(is_connected=False).all()
    
    # Получаем информацию о сетевых интерфейсах
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
    Новая упрощенная страница для отображения USB устройств.
    Используется более простой подход для минимизации ошибок.
    """
    # Получаем список локальных USB устройств
    local_devices = get_local_usb_devices()
    
    # Получаем список опубликованных устройств - с выводом подробной отладочной информации
    published_busids = get_published_devices()
    add_log_entry('DEBUG', f'Home2: Published devices: {published_busids}', 'usbip')
    
    # Помечаем опубликованные устройства с подробной отладкой
    for device in local_devices:
        # Нормализуем busid устройства для правильного сравнения
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
    
    # Получаем список подключенных устройств
    attached_devices = get_attached_devices()
    
    # Добавляем виртуальные устройства в список локальных устройств
    virtual_devices = VirtualUsbDevice.query.filter_by(is_active=False).all()
    
    for device in virtual_devices:
        local_devices.append({
            'busid': f'v-{device.id}',
            'device_name': device.name,
            'idVendor': device.vendor_id,
            'idProduct': device.product_id,
            'is_virtual': True,
            'virtual_id': device.id,
            'is_published': False  # Виртуальные устройства не публикуются
        })
    
    # Получаем алиасы устройств
    device_aliases = {alias.busid: alias.alias for alias in DeviceAlias.query.all()}
    
    # Применяем алиасы к списку устройств
    for device in local_devices:
        if 'busid' in device and device['busid'] in device_aliases:
            device['device_name'] = device_aliases[device['busid']]
    
    # Запись в лог
    add_log_entry('INFO', f'Home2: USB device list refreshed, found {len(local_devices)} devices', 'system')
    
    # Отладочная информация в консоль для проверки
    logger.debug(f"Home2: Local devices: {local_devices}")
    logger.debug(f"Home2: Attached devices: {attached_devices}")
    
    return render_template('home2.html',
                           local_devices=local_devices,
                           attached_devices=attached_devices)


@app.route('/admin', methods=['GET', 'POST'])
@login_required
def admin():
    if not current_user.is_admin:
        flash('У вас нет прав доступа к админ-панели', 'danger')
        return redirect(url_for('index'))
    
    # Обработка формы смены пароля
    if request.method == 'POST':
        if 'change_password' in request.form:
            current_password = request.form.get('current_password')
            new_password = request.form.get('new_password')
            confirm_password = request.form.get('confirm_password')
            
            # Проверка текущего пароля
            if not current_user.check_password(current_password):
                flash('Текущий пароль указан неверно', 'danger')
            elif new_password != confirm_password:
                flash('Новый пароль и подтверждение не совпадают', 'danger')
            elif len(new_password) < 6:
                flash('Новый пароль должен содержать минимум 6 символов', 'danger')
            else:
                current_user.set_password(new_password)
                db.session.commit()
                
                # Запись в лог
                add_log_entry('INFO', f'User {current_user.username} changed password', 'auth')
                
                flash('Пароль успешно изменен', 'success')
                return redirect(url_for('admin'))
        
        # Обработка других форм админ-панели
        # ...
    
    # Получение различных данных для админ-панели
    usb_ports = UsbPort.query.all()
    device_aliases = DeviceAlias.query.all()
    
    # Получаем информацию о сетевых интерфейсах
    network_interfaces = get_network_interfaces()
    
    return render_template('admin.html', 
                          usb_ports=usb_ports,
                          device_aliases=device_aliases,
                          network_interfaces=network_interfaces)

@app.route('/logs')
@login_required
def logs():
    log_type = request.args.get('type', 'all')
    page = request.args.get('page', 1, type=int)
    per_page = 20
    
    # Базовый запрос логов с сортировкой по времени (новые сначала)
    query = LogEntry.query.order_by(LogEntry.timestamp.desc())
    
    # Фильтрация по типу лога
    if log_type != 'all':
        query = query.filter_by(level=log_type.upper())
    
    # Пагинация результатов
    logs = query.paginate(page=page, per_page=per_page, error_out=False)
    
    # Получаем информацию о сетевых интерфейсах
    network_interfaces = get_network_interfaces()
    
    return render_template('logs.html', 
                          logs=logs, 
                          current_type=log_type, 
                          network_interfaces=network_interfaces)

@app.route('/device_alias', methods=['POST'])
@login_required
def device_alias():
    busid = request.form.get('busid')
    alias = request.form.get('alias')
    device_info = request.form.get('device_info', '')
    
    if not busid or not alias:
        flash('Не указан идентификатор устройства или псевдоним', 'danger')
        return redirect(url_for('index'))
    
    # Проверяем, существует ли уже такой алиас
    existing_alias = DeviceAlias.query.filter_by(busid=busid).first()
    if existing_alias:
        existing_alias.alias = alias
        existing_alias.device_info = device_info
        db.session.commit()
        flash(f'Псевдоним для устройства {busid} обновлен', 'success')
    else:
        new_alias = DeviceAlias(busid=busid, alias=alias, device_info=device_info)
        db.session.add(new_alias)
        db.session.commit()
        flash(f'Псевдоним для устройства {busid} добавлен', 'success')
    
    return redirect(url_for('index'))

@app.route('/port_name', methods=['POST'])
@login_required
def port_name():
    port_number = request.form.get('port_number')
    custom_name = request.form.get('custom_name')
    
    if not port_number or not custom_name:
        flash('Не указан номер порта или пользовательское имя', 'danger')
        return redirect(url_for('index'))
    
    # Проверяем, существует ли уже такое имя порта
    existing_port = UsbPort.query.filter_by(port_number=port_number).first()
    if existing_port:
        existing_port.custom_name = custom_name
        db.session.commit()
        flash(f'Имя для порта {port_number} обновлено', 'success')
    else:
        new_port = UsbPort(port_number=port_number, custom_name=custom_name)
        db.session.add(new_port)
        db.session.commit()
        flash(f'Имя для порта {port_number} добавлено', 'success')
    
    return redirect(url_for('index'))



@app.route('/bind-device', methods=['POST'])
@login_required
def bind_device_route():
    # Получаем данные из JSON (не из form)
    data = request.get_json()
    busid = data.get('busid') if data else None
    if not busid:
        return jsonify({'success': False, 'message': 'Не указан busid устройства'}), 400
    
    success, message = bind_device(busid)
    
    # Запись в лог
    level = 'INFO' if success else 'ERROR'
    add_log_entry(level, f'Published device {busid}: {message}', 'usbip')
    
    return jsonify({'success': success, 'message': message})

@app.route('/remote')
@login_required
def remote():
    # Получаем информацию о сетевых интерфейсах
    network_interfaces = get_network_interfaces()
    
    return render_template('remote.html', network_interfaces=network_interfaces)

@app.route('/get_remote_devices', methods=['POST'])
@login_required
def get_remote_devices_route():
    ip = request.form.get('ip')
    if not ip:
        return jsonify({'success': False, 'message': 'IP-адрес не указан'}), 400
    
    devices, error = get_remote_usb_devices(ip)
    
    # Запись в лог
    if error:
        add_log_entry(
            'ERROR', 
            f'Error getting device list from {ip}: {error}', 
            'usbip'
        )
        return jsonify({'success': False, 'message': error})
    else:
        add_log_entry(
            'INFO', 
            f'Got device list from server {ip} ({len(devices)} devices)', 
            'usbip'
        )
    
    # Добавляем алиасы к устройствам, если они есть
    for device in devices:
        if 'busid' in device:
            alias = DeviceAlias.query.filter_by(busid=device['busid']).first()
            if alias:
                device['alias'] = alias.alias
    
    return jsonify({'success': True, 'devices': devices})

@app.route('/attach_device', methods=['POST'])
@login_required
def attach_device_route():
    ip = request.form.get('ip')
    busid = request.form.get('busid')
    if not ip or not busid:
        return jsonify({'success': False, 'message': 'Не указан IP или busid устройства'}), 400
    
    success, message = attach_device(ip, busid)
    
    # Запись в лог
    level = 'INFO' if success else 'ERROR'
    add_log_entry(
        level, 
        f'Attached device {busid} from server {ip}: {message}', 
        'usbip'
    )
    
    return jsonify({'success': success, 'message': message})

@app.route('/detach_device', methods=['POST'])
@login_required
def detach_device_route():
    port = request.form.get('port')
    if not port:
        return jsonify({'success': False, 'message': 'Не указан порт устройства'}), 400
    
    success, message = detach_device(port)
    
    # Запись в лог
    level = 'INFO' if success else 'ERROR'
    add_log_entry(
        level, 
        f'Detached device from port {port}: {message}', 
        'usbip'
    )
    
    return jsonify({'success': success, 'message': message})

@app.route('/virtual_devices')
@login_required
def virtual_devices():
    virtual_devices = VirtualUsbDevice.query.all()
    virtual_ports = VirtualUsbPort.query.all()
    
    # Форматируем для шаблона
    # Используем переводы для типов устройств
    current_language = get_current_language()
    device_types = [
        {'id': 'storage', 'name': get_translation('storage_device', current_language)},
        {'id': 'hid', 'name': get_translation('hid_device', current_language)},
        {'id': 'serial', 'name': get_translation('serial_device', current_language)},
        {'id': 'ethernet', 'name': get_translation('ethernet_device', current_language)},
        {'id': 'audio', 'name': get_translation('audio_device', current_language)},
        {'id': 'printer', 'name': get_translation('printer_device', current_language)},
        {'id': 'camera', 'name': get_translation('camera_device', current_language)},
        {'id': 'custom', 'name': get_translation('custom_device', current_language)}
    ]
    
    # Получаем информацию о сетевых интерфейсах
    network_interfaces = get_network_interfaces()
    
    return render_template('virtual_devices.html', 
                          virtual_devices=virtual_devices,
                          virtual_ports=virtual_ports,
                          device_types=device_types,
                          network_interfaces=network_interfaces)

@app.route('/create_virtual_device', methods=['POST'])
@login_required
def create_virtual_device():
    name = request.form.get('name')
    device_type = request.form.get('device_type')
    vendor_id = request.form.get('vendor_id', '1a2b').lower()
    product_id = request.form.get('product_id', '3c4d').lower()
    serial_number = request.form.get('serial_number', '')
    config_json = request.form.get('config_json', '{}')
    
    # Для устройств типа storage получаем размер хранилища
    storage_size = 1024  # Значение по умолчанию 1 ГБ
    if device_type == 'storage':
        try:
            storage_size = int(request.form.get('storage_size', 1024))
            # Проверяем диапазон допустимых значений
            if storage_size < 1 or storage_size > 16384:
                flash('Размер хранилища должен быть от 1 МБ до 16 ГБ', 'warning')
                storage_size = 1024  # Устанавливаем значение по умолчанию
        except ValueError:
            flash('Указан некорректный размер хранилища, используется размер по умолчанию (1 ГБ)', 'warning')
    
    # Базовая валидация
    if not name or not device_type:
        flash('Имя и тип устройства обязательны', 'danger')
        return redirect(url_for('virtual_devices'))
    
    # Проверка формата VID/PID
    vid_pattern = re.compile(r'^[0-9a-f]{4}$')
    if not vid_pattern.match(vendor_id) or not vid_pattern.match(product_id):
        flash('Vendor ID и Product ID должны быть в формате 4 символа (0-9, a-f)', 'danger')
        return redirect(url_for('virtual_devices'))
    
    # Создаем виртуальное устройство
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
    db.session.commit()  # Сначала коммитим, чтобы получить ID устройства
    
    # Если это устройство хранения, создаем хранилище
    if device_type == 'storage':
        # Проверяем, используется ли системная папка
        use_system_folder = 'use_system_folder' in request.form
        
        if use_system_folder:
            # Получаем путь к системной папке
            system_path = request.form.get('system_path', '').strip()
            
            # Получаем размер из формы для системной папки
            try:
                system_storage_size = int(request.form.get('system_storage_size', 1024))
                if system_storage_size < 1 or system_storage_size > 16384:
                    system_storage_size = 1024
            except ValueError:
                system_storage_size = 1024
                
            # Проверяем, указан ли путь
            if not system_path:
                flash('Необходимо указать путь к системной папке', 'danger')
                db.session.delete(device)
                db.session.commit()
                return redirect(url_for('virtual_devices'))
                
            # Создаем хранилище с системной папкой
            if not create_device_storage(device, system_storage_size, system_path):
                flash('Не удалось создать хранилище с указанной системной папкой', 'danger')
                db.session.delete(device)
                db.session.commit()
                return redirect(url_for('virtual_devices'))
        else:
            # Создаем обычное виртуальное хранилище
            create_device_storage(device, storage_size)
    
    # Запись в лог
    log_message = f'Created virtual device: {name} ({vendor_id}:{product_id})'
    
    if device_type == 'storage':
        if 'use_system_folder' in request.form:
            system_path = request.form.get('system_path', '').strip()
            system_storage_size = int(request.form.get('system_storage_size', 1024))
            log_message += f' with system folder {system_path} ({system_storage_size} MB)'
        else:
            log_message += f' with virtual storage {storage_size} MB'
    
    add_log_entry('INFO', log_message, 'virtual')
    
    flash(f'Виртуальное устройство "{name}" создано', 'success')
    return redirect(url_for('virtual_devices'))

@app.route('/create_virtual_port', methods=['POST'])
@login_required
def create_virtual_port():
    name = request.form.get('name')
    port_number = request.form.get('port_number', f'vp{random.randint(0, 9999):04d}')
    device_id = request.form.get('device_id')
    
    # Базовая валидация
    if not name:
        flash('Имя порта обязательно', 'danger')
        return redirect(url_for('virtual_devices'))
    
    # Создаем виртуальный порт
    port = VirtualUsbPort(
        name=name,
        port_number=port_number,
        device_id=device_id if device_id else None
    )
    db.session.add(port)
    
    # Запись в лог
    add_log_entry(
        'INFO',
        f'Created virtual port: {name} ({port_number})',
        'virtual'
    )
    
    flash(f'Виртуальный порт "{name}" создан', 'success')
    return redirect(url_for('virtual_devices'))

@app.route('/connect_virtual_device', methods=['POST'])
@login_required
def connect_virtual_device():
    port_id = request.form.get('port_id')
    device_id = request.form.get('device_id')
    
    # Проверка наличия порта и устройства
    port = VirtualUsbPort.query.get(port_id)
    device = VirtualUsbDevice.query.get(device_id)
    
    if not port or not device:
        flash('Порт или устройство не найдены', 'danger')
        return redirect(url_for('virtual_devices'))
    
    # Подключаем устройство к порту
    port.device_id = device.id
    port.is_connected = True
    device.is_active = True
    
    # Запись в лог
    add_log_entry(
        'INFO',
        f'Device {device.name} connected to port {port.name}',
        'virtual'
    )
    
    flash(f'Устройство {device.name} успешно подключено к порту {port.name}', 'success')
    return redirect(url_for('virtual_devices'))

@app.route('/disconnect_virtual_device', methods=['POST'])
@login_required
def disconnect_virtual_device():
    port_id = request.form.get('port_id')
    
    # Проверка наличия порта
    port = VirtualUsbPort.query.get(port_id)
    
    if not port:
        flash('Порт не найден', 'danger')
        return redirect(url_for('virtual_devices'))
    
    # Сохраняем имя устройства для лога
    device_name = "Нет устройства"
    if port.device:
        device_name = port.device.name
        port.device.is_active = False
    
    # Отключаем устройство от порта
    port.device_id = None
    port.is_connected = False
    
    # Запись в лог
    add_log_entry(
        'INFO',
        f'Device {device_name} disconnected from port {port.name}',
        'virtual'
    )
    
    flash(f'Устройство отключено от порта {port.name}', 'success')
    return redirect(url_for('virtual_devices'))

@app.route('/delete_virtual_device', methods=['POST'])
@login_required
def delete_virtual_device():
    device_id = request.form.get('device_id')
    
    # Проверка наличия устройства
    device = VirtualUsbDevice.query.get(device_id)
    
    if not device:
        flash('Устройство не найдено', 'danger')
        return redirect(url_for('virtual_devices'))
    
    # Сначала отключаем устройство от всех портов
    for port in VirtualUsbPort.query.filter_by(device_id=device.id).all():
        port.device_id = None
        port.is_connected = False
    
    # Если это устройство хранения, удаляем его хранилище
    if device.device_type == 'storage' and device.storage_path:
        delete_device_storage(device)
    
    # Удаляем устройство
    device_name = device.name
    db.session.delete(device)
    
    # Запись в лог
    add_log_entry(
        'INFO',
        f'Virtual device {device_name} deleted',
        'virtual'
    )
    
    flash(f'Виртуальное устройство "{device_name}" удалено', 'success')
    return redirect(url_for('virtual_devices'))

@app.route('/delete_virtual_port', methods=['POST'])
@login_required
def delete_virtual_port():
    port_id = request.form.get('port_id')
    
    # Проверка наличия порта
    port = VirtualUsbPort.query.get(port_id)
    
    if not port:
        flash('Порт не найден', 'danger')
        return redirect(url_for('virtual_devices'))
    
    # Удаляем порт
    port_name = port.name
    db.session.delete(port)
    
    # Запись в лог
    add_log_entry(
        'INFO',
        f'Virtual port {port_name} deleted',
        'virtual'
    )
    
    flash(f'Виртуальный порт "{port_name}" удален', 'success')
    return redirect(url_for('virtual_devices'))

# Маршруты для управления хранилищем виртуальных USB устройств
# Маршруты для управления хранилищем виртуальных USB устройств добавлены через Blueprint
# app.register_blueprint(storage_bp)

@app.route('/get_system_directories', methods=['GET'])
@login_required
def get_system_directories():
    """
    API для получения списка директорий на сервере
    """
    base_path = request.args.get('path', '/')
    
    # Базовая защита - запрещаем подниматься выше корня
    base_path = os.path.normpath(base_path)
    if base_path.startswith('..'):
        base_path = '/'
    
    try:
        # Получаем список папок
        dirs = []
        files = []
        
        for item in os.listdir(base_path):
            full_path = os.path.join(base_path, item)
            
            # Пропускаем скрытые файлы и папки
            if item.startswith('.'):
                continue
                
            if os.path.isdir(full_path):
                # Проверяем, есть ли права на запись
                writable = os.access(full_path, os.W_OK)
                dirs.append({
                    'name': item,
                    'path': full_path,
                    'writable': writable
                })
            else:
                # Для полноты информации добавляем и файлы
                size = os.path.getsize(full_path)
                files.append({
                    'name': item,
                    'path': full_path,
                    'size': size
                })
        
        # Собираем информацию о текущей директории
        parent_dir = os.path.dirname(base_path) if base_path != '/' else '/'
        
        # Проверяем права на запись
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

# Обработчики ошибок с пользовательскими страницами
@app.errorhandler(400)
def bad_request(error):
    return render_template('error.html', 
                          error_code="400",
                          error_title="Некорректный запрос",
                          error_description="Сервер не смог обработать ваш запрос из-за некорректных данных. Пожалуйста, проверьте введенные данные и попробуйте снова."), 400

@app.errorhandler(401)
def unauthorized(error):
    return render_template('error.html', 
                          error_code="401",
                          error_title="Не авторизован",
                          error_description="Для доступа к этой странице требуется авторизация. Пожалуйста, войдите в систему."), 401

@app.errorhandler(403)
def forbidden(error):
    return render_template('error.html', 
                          error_code="403",
                          error_title="Доступ запрещен",
                          error_description="У вас недостаточно прав для доступа к этой странице."), 403

@app.errorhandler(404)
def page_not_found(error):
    return render_template('error.html', 
                          error_code="404",
                          error_title="Страница не найдена",
                          error_description="Запрашиваемая страница не существует. Возможно, она была удалена или перемещена."), 404

@app.errorhandler(500)
def internal_server_error(error):
    return render_template('error.html', 
                          error_code="500",
                          error_title="Внутренняя ошибка сервера",
                          error_description="На сервере произошла непредвиденная ошибка. Наши специалисты уже работают над её устранением."), 500

@app.errorhandler(503)
def service_unavailable(error):
    return render_template('error.html', 
                          error_code="503",
                          error_title="Сервис недоступен",
                          error_description="Сервис временно недоступен. Пожалуйста, попробуйте позже."), 503

# Общий обработчик для неопределенных ошибок
@app.errorhandler(Exception)
def handle_exception(error):
    # Если исключение имеет код HTTP
    if hasattr(error, 'code'):
        code = error.code
    else:
        code = 500
    
    app.logger.error(f"Unhandled error: {error}")
    
    return render_template('error.html', 
                          error_code=str(code),
                          error_title="Ошибка сервера",
                          error_description="Произошла неожиданная ошибка. Пожалуйста, попробуйте позже или обратитесь к администратору."), code

@app.route('/api/run_doctor', methods=['POST'])
@login_required
def run_doctor():
    """
    API для запуска скрипта doctor.sh и получения результатов диагностики
    """
    try:
        # Проверяем, что скрипт существует
        if not os.path.exists('./doctor.sh'):
            return jsonify({
                'success': False,
                'message': 'Скрипт doctor.sh не найден'
            }), 404
        
        # Делаем скрипт исполняемым, если он еще не такой
        os.chmod('./doctor.sh', 0o755)
        
        # Запускаем скрипт doctor.sh и получаем вывод
        process = subprocess.Popen(
            ['sudo', './doctor.sh'], 
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            universal_newlines=True
        )
        
        stdout, stderr = process.communicate()
        
        # Записываем результаты в лог
        if process.returncode == 0:
            add_log_entry('INFO', 'Скрипт doctor.sh успешно выполнен', 'system')
        else:
            add_log_entry('ERROR', f'Ошибка при выполнении doctor.sh: {stderr}', 'system')
        
        # Форматируем вывод для отображения в веб-интерфейсе
        output = stdout if stdout else "Нет вывода"
        if stderr:
            output += f"\n\nОшибки:\n{stderr}"
        
        return jsonify({
            'success': process.returncode == 0,
            'output': output,
            'message': 'Диагностика выполнена успешно' if process.returncode == 0 else 'Ошибка при выполнении диагностики'
        })
    except Exception as e:
        # Записываем ошибку в лог
        add_log_entry('ERROR', f'Исключение при запуске doctor.sh: {str(e)}', 'system')
        return jsonify({
            'success': False,
            'message': f'Ошибка: {str(e)}'
        }), 500


# ============== TERMINAL ROUTES ==============

@app.route('/terminal')
@login_required
def terminal():
    """
    Страница веб-терминала с кнопками команд
    """
    # Получаем команды пользователя
    user_commands = TerminalCommand.query.filter_by(user_id=current_user.id).order_by(TerminalCommand.created_at.desc()).all()
    
    return render_template('terminal.html', user_commands=user_commands)


@app.route('/terminal/execute', methods=['POST'])
@login_required
def execute_terminal_command():
    """
    API для выполнения команд в терминале
    """
    try:
        data = request.get_json()
        command = data.get('command', '').strip()
        
        if not command:
            return jsonify({
                'success': False,
                'message': 'Команда не может быть пустой'
            }), 400
        
        # Запись в лог
        add_log_entry('INFO', f'Terminal command executed: {command}', 'terminal')
        
        # Выполнение команды
        try:
            result = subprocess.run(
                command,
                shell=True,
                capture_output=True,
                text=True,
                timeout=30,  # Таймаут 30 секунд
                cwd=os.getcwd()
            )
            
            output = result.stdout
            error = result.stderr
            return_code = result.returncode
            
            # Формируем ответ
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
                'message': 'Команда выполнялась слишком долго (таймаут 30 секунд)',
                'command': command
            }), 408
            
        except Exception as e:
            return jsonify({
                'success': False,
                'message': f'Ошибка выполнения команды: {str(e)}',
                'command': command
            }), 500
            
    except Exception as e:
        add_log_entry('ERROR', f'Terminal API error: {str(e)}', 'terminal')
        return jsonify({
            'success': False,
            'message': f'Ошибка сервера: {str(e)}'
        }), 500


@app.route('/terminal/commands', methods=['POST'])
@login_required
def create_terminal_command():
    """
    Создание новой кнопки команды
    """
    try:
        name = request.form.get('name', '').strip()
        command = request.form.get('command', '').strip()
        description = request.form.get('description', '').strip()
        
        if not name or not command:
            flash('Название и команда обязательны для заполнения', 'danger')
            return redirect(url_for('terminal'))
        
        # Проверяем, не существует ли уже команда с таким именем у пользователя
        existing_command = TerminalCommand.query.filter_by(
            user_id=current_user.id,
            name=name
        ).first()
        
        if existing_command:
            flash('Команда с таким названием уже существует', 'warning')
            return redirect(url_for('terminal'))
        
        # Создаем новую команду
        new_command = TerminalCommand(
            name=name,
            command=command,
            description=description,
            user_id=current_user.id
        )
        
        db.session.add(new_command)
        db.session.commit()
        
        flash(f'Команда "{name}" успешно создана', 'success')
        add_log_entry('INFO', f'Terminal command created: {name}', 'terminal')
        
        return redirect(url_for('terminal'))
        
    except Exception as e:
        db.session.rollback()
        add_log_entry('ERROR', f'Error creating terminal command: {str(e)}', 'terminal')
        flash(f'Ошибка при создании команды: {str(e)}', 'danger')
        return redirect(url_for('terminal'))


@app.route('/terminal/commands/<int:command_id>', methods=['POST'])
@login_required
def update_terminal_command(command_id):
    """
    Редактирование кнопки команды
    """
    try:
        command_obj = TerminalCommand.query.filter_by(
            id=command_id,
            user_id=current_user.id
        ).first()
        
        if not command_obj:
            flash('Команда не найдена', 'danger')
            return redirect(url_for('terminal'))
        
        name = request.form.get('name', '').strip()
        command = request.form.get('command', '').strip()
        description = request.form.get('description', '').strip()
        
        if not name or not command:
            flash('Название и команда обязательны для заполнения', 'danger')
            return redirect(url_for('terminal'))
        
        # Проверяем, не существует ли уже другая команда с таким именем у пользователя
        existing_command = TerminalCommand.query.filter_by(
            user_id=current_user.id,
            name=name
        ).filter(TerminalCommand.id != command_id).first()
        
        if existing_command:
            flash('Команда с таким названием уже существует', 'warning')
            return redirect(url_for('terminal'))
        
        # Обновляем команду
        command_obj.name = name
        command_obj.command = command
        command_obj.description = description
        command_obj.updated_at = datetime.utcnow()
        
        db.session.commit()
        
        flash(f'Команда "{name}" успешно обновлена', 'success')
        add_log_entry('INFO', f'Terminal command updated: {name}', 'terminal')
        
        return redirect(url_for('terminal'))
        
    except Exception as e:
        db.session.rollback()
        add_log_entry('ERROR', f'Error updating terminal command: {str(e)}', 'terminal')
        flash(f'Ошибка при обновлении команды: {str(e)}', 'danger')
        return redirect(url_for('terminal'))


@app.route('/terminal/commands/<int:command_id>/delete', methods=['POST'])
@login_required
def delete_terminal_command(command_id):
    """
    Удаление кнопки команды
    """
    try:
        command_obj = TerminalCommand.query.filter_by(
            id=command_id,
            user_id=current_user.id
        ).first()
        
        if not command_obj:
            flash('Команда не найдена', 'danger')
            return redirect(url_for('terminal'))
        
        command_name = command_obj.name
        db.session.delete(command_obj)
        db.session.commit()
        
        flash(f'Команда "{command_name}" успешно удалена', 'success')
        add_log_entry('INFO', f'Terminal command deleted: {command_name}', 'terminal')
        
        return redirect(url_for('terminal'))
        
    except Exception as e:
        db.session.rollback()
        add_log_entry('ERROR', f'Error deleting terminal command: {str(e)}', 'terminal')
        flash(f'Ошибка при удалении команды: {str(e)}', 'danger')
        return redirect(url_for('terminal'))


if __name__ == '__main__':
    app.run(host="0.0.0.0", port=5000, debug=True)
