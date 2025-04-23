import os
import re
import json
import random
import logging
import socket
import netifaces
from flask import Flask, render_template, redirect, url_for, request, flash, jsonify, send_file
from flask_login import LoginManager, login_user, logout_user, login_required, current_user
from werkzeug.security import check_password_hash, generate_password_hash
from werkzeug.middleware.proxy_fix import ProxyFix
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy.orm import DeclarativeBase
from datetime import datetime
import trafilatura

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
class Base(DeclarativeBase):
    pass

# Инициализация SQLAlchemy с базовым классом
db = SQLAlchemy(model_class=Base)

# Создание Flask-приложения
app = Flask(__name__)
app.secret_key = os.environ.get("SESSION_SECRET", "default_secret_key_for_development")
app.wsgi_app = ProxyFix(app.wsgi_app, x_proto=1, x_host=1)

# Настройка базы данных
database_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'usbip_web.db')
database_uri = os.environ.get("DATABASE_URL")

# Проверяем, используется ли SQLite или PostgreSQL
if database_uri and database_uri.startswith('postgresql'):
    app.config["SQLALCHEMY_DATABASE_URI"] = database_uri
    app.config["SQLALCHEMY_ENGINE_OPTIONS"] = {
        "pool_recycle": 300,
        "pool_pre_ping": True,
    }
else:
    # Используем SQLite по умолчанию
    app.config["SQLALCHEMY_DATABASE_URI"] = f"sqlite:///{database_path}"
    app.config["SQLALCHEMY_ENGINE_OPTIONS"] = {}
    # Для SQLite добавляем специальные настройки
    if app.config["SQLALCHEMY_DATABASE_URI"].startswith('sqlite'):
        app.config["SQLALCHEMY_ENGINE_OPTIONS"]["connect_args"] = {"check_same_thread": False}
db.init_app(app)

# Настройка Flask-Login
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = "login"

# Импортирование утилит
from usbip_utils import get_local_usb_devices, bind_device, get_remote_usb_devices, attach_device, detach_device, get_attached_devices

# Импортирование моделей (после настройки db)
from models import User, DeviceAlias, UsbPort, LogEntry, VirtualUsbDevice, VirtualUsbPort, VirtualUsbFile

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
            log_entry = LogEntry(level='INFO', message=f'Пользователь {username} вошел в систему', source='auth')
            db.session.add(log_entry)
            db.session.commit()
            
            flash('Вход выполнен успешно!', 'success')
            return redirect(url_for('index'))
        else:
            # Запись в лог о неудачной попытке
            if username:
                log_entry = LogEntry(level='WARNING', message=f'Неудачная попытка входа для пользователя {username}', source='auth')
                db.session.add(log_entry)
                db.session.commit()
                
            flash('Неверное имя пользователя или пароль', 'danger')
    
    # Получаем информацию о сетевых интерфейсах
    network_interfaces = get_network_interfaces()
    return render_template('login.html', network_interfaces=network_interfaces)

@app.route('/logout')
@login_required
def logout():
    username = current_user.username
    logout_user()
    
    # Запись в лог
    log_entry = LogEntry(level='INFO', message=f'Пользователь {username} вышел из системы', source='auth')
    db.session.add(log_entry)
    db.session.commit()
    
    flash('Вы вышли из системы', 'info')
    return redirect(url_for('login'))

@app.route('/')
@login_required
def index():
    # Получаем реальные USB устройства через usbip
    local_devices = get_local_usb_devices()
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
                log_entry = LogEntry(level='INFO', message=f'Пользователь {current_user.username} сменил пароль', source='auth')
                db.session.add(log_entry)
                db.session.commit()
                
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

@app.route('/search_device_info', methods=['POST'])
@login_required
def search_device_info():
    device_id = request.form.get('device_id')
    if not device_id:
        return jsonify({'success': False, 'message': 'Не указан идентификатор устройства'})
    
    try:
        # Используем trafilatura для поиска информации об устройстве
        # (это пример, в реальном случае нужно использовать специализированные API)
        search_url = f"https://www.google.com/search?q=usb+device+{device_id}+specifications"
        downloaded = trafilatura.fetch_url(search_url)
        text = trafilatura.extract(downloaded)
        
        if text:
            # Записываем в лог результат поиска
            log_entry = LogEntry(
                level='INFO', 
                message=f'Поиск информации для устройства {device_id}', 
                source='search'
            )
            db.session.add(log_entry)
            db.session.commit()
            
            return jsonify({
                'success': True, 
                'message': 'Информация найдена', 
                'data': text[:500] + '...' if len(text) > 500 else text
            })
        else:
            return jsonify({
                'success': False, 
                'message': 'Информация не найдена для данного устройства'
            })
    except Exception as e:
        return jsonify({
            'success': False, 
            'message': f'Ошибка при поиске информации: {str(e)}'
        })

@app.route('/bind_device', methods=['POST'])
@login_required
def bind_device_route():
    busid = request.form.get('busid')
    if not busid:
        return jsonify({'success': False, 'message': 'Не указан busid устройства'}), 400
    
    success, message = bind_device(busid)
    
    # Запись в лог
    level = 'INFO' if success else 'ERROR'
    log_entry = LogEntry(
        level=level, 
        message=f'Публикация устройства {busid}: {message}', 
        source='usbip'
    )
    db.session.add(log_entry)
    db.session.commit()
    
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
        log_entry = LogEntry(
            level='ERROR', 
            message=f'Ошибка при получении списка устройств с {ip}: {error}', 
            source='usbip'
        )
        db.session.add(log_entry)
        db.session.commit()
        return jsonify({'success': False, 'message': error})
    else:
        log_entry = LogEntry(
            level='INFO', 
            message=f'Получен список устройств с сервера {ip} ({len(devices)} устройств)', 
            source='usbip'
        )
        db.session.add(log_entry)
        db.session.commit()
    
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
    log_entry = LogEntry(
        level=level, 
        message=f'Подключение устройства {busid} с сервера {ip}: {message}', 
        source='usbip'
    )
    db.session.add(log_entry)
    db.session.commit()
    
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
    log_entry = LogEntry(
        level=level, 
        message=f'Отключение устройства с порта {port}: {message}', 
        source='usbip'
    )
    db.session.add(log_entry)
    db.session.commit()
    
    return jsonify({'success': success, 'message': message})

@app.route('/virtual_devices')
@login_required
def virtual_devices():
    virtual_devices = VirtualUsbDevice.query.all()
    virtual_ports = VirtualUsbPort.query.all()
    
    # Форматируем для шаблона
    device_types = [
        {'id': 'hid', 'name': 'HID (мышь, клавиатура)'},
        {'id': 'storage', 'name': 'Устройство хранения (флешка)'},
        {'id': 'serial', 'name': 'Последовательный порт'},
        {'id': 'ethernet', 'name': 'Сетевой адаптер'},
        {'id': 'audio', 'name': 'Аудио устройство'},
        {'id': 'printer', 'name': 'Принтер'},
        {'id': 'camera', 'name': 'Веб-камера'},
        {'id': 'custom', 'name': 'Другое (своя конфигурация)'}
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
        config_json=config_json
    )
    db.session.add(device)
    
    # Запись в лог
    log_entry = LogEntry(
        level='INFO',
        message=f'Создано виртуальное устройство: {name} ({vendor_id}:{product_id})',
        source='virtual'
    )
    db.session.add(log_entry)
    db.session.commit()
    
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
    log_entry = LogEntry(
        level='INFO',
        message=f'Создан виртуальный порт: {name} ({port_number})',
        source='virtual'
    )
    db.session.add(log_entry)
    db.session.commit()
    
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
    log_entry = LogEntry(
        level='INFO',
        message=f'Устройство {device.name} подключено к порту {port.name}',
        source='virtual'
    )
    db.session.add(log_entry)
    db.session.commit()
    
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
    log_entry = LogEntry(
        level='INFO',
        message=f'Устройство {device_name} отключено от порта {port.name}',
        source='virtual'
    )
    db.session.add(log_entry)
    db.session.commit()
    
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
    
    # Удаляем устройство
    device_name = device.name
    db.session.delete(device)
    
    # Запись в лог
    log_entry = LogEntry(
        level='INFO',
        message=f'Виртуальное устройство {device_name} удалено',
        source='virtual'
    )
    db.session.add(log_entry)
    db.session.commit()
    
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
    log_entry = LogEntry(
        level='INFO',
        message=f'Виртуальный порт {port_name} удален',
        source='virtual'
    )
    db.session.add(log_entry)
    db.session.commit()
    
    flash(f'Виртуальный порт "{port_name}" удален', 'success')
    return redirect(url_for('virtual_devices'))

if __name__ == '__main__':
    app.run(host="0.0.0.0", port=5000, debug=True)
