import os
import logging
from flask import Flask, render_template, redirect, url_for, request, flash, jsonify
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
app.config["SQLALCHEMY_DATABASE_URI"] = os.environ.get("DATABASE_URL")
app.config["SQLALCHEMY_ENGINE_OPTIONS"] = {
    "pool_recycle": 300,
    "pool_pre_ping": True,
}
db.init_app(app)

# Настройка Flask-Login
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = "login"

# Импортирование утилит
from usbip_utils import get_local_usb_devices, bind_device, get_remote_usb_devices, attach_device, detach_device, get_attached_devices

# Импортирование моделей (после настройки db)
from models import User, DeviceAlias, UsbPort, LogEntry

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
    
    return render_template('login.html')

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
    local_devices = get_local_usb_devices()
    attached_devices = get_attached_devices()
    return render_template('index.html', local_devices=local_devices, attached_devices=attached_devices)

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
    
    return render_template('admin.html', 
                          usb_ports=usb_ports,
                          device_aliases=device_aliases)

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
    
    return render_template('logs.html', logs=logs, current_type=log_type)

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
    return render_template('remote.html')

@app.route('/get_remote_devices', methods=['POST'])
@login_required
def get_remote_devices_route():
    ip = request.form.get('ip')
    if not ip:
        return jsonify({'success': False, 'message': 'IP-адрес не указан'}), 400
    
    devices, error = get_remote_usb_devices(ip)
    if error:
        return jsonify({'success': False, 'message': error})
    
    return jsonify({'success': True, 'devices': devices})

@app.route('/attach_device', methods=['POST'])
@login_required
def attach_device_route():
    ip = request.form.get('ip')
    busid = request.form.get('busid')
    if not ip or not busid:
        return jsonify({'success': False, 'message': 'Не указан IP или busid устройства'}), 400
    
    success, message = attach_device(ip, busid)
    return jsonify({'success': success, 'message': message})

@app.route('/detach_device', methods=['POST'])
@login_required
def detach_device_route():
    port = request.form.get('port')
    if not port:
        return jsonify({'success': False, 'message': 'Не указан порт устройства'}), 400
    
    success, message = detach_device(port)
    return jsonify({'success': success, 'message': message})

if __name__ == '__main__':
    app.run(host="0.0.0.0", port=5000, debug=True)
