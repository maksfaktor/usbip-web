import os
import logging
from flask import Flask, render_template, redirect, url_for, request, flash, jsonify
from flask_login import LoginManager, login_user, logout_user, login_required, current_user
from werkzeug.security import check_password_hash, generate_password_hash
from werkzeug.middleware.proxy_fix import ProxyFix

# Настройка логгирования
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

# Создание Flask-приложения
app = Flask(__name__)
app.secret_key = os.environ.get("SESSION_SECRET", "default_secret_key_for_development")
app.wsgi_app = ProxyFix(app.wsgi_app, x_proto=1, x_host=1)

# Настройка Flask-Login
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = "login"

# Импортирование моделей и утилит
from models import User
from usbip_utils import get_local_usb_devices, bind_device, get_remote_usb_devices, attach_device, detach_device, get_attached_devices

@login_manager.user_loader
def load_user(user_id):
    # Простая реализация загрузки пользователя
    # В реальном приложении это должно быть связано с базой данных
    if user_id == '1':
        return User(1, 'admin')
    return None

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        
        # Проверка пароля (в реальном приложении используйте БД)
        if username == 'admin' and password == 'admin':
            user = User(1, 'admin')
            login_user(user)
            flash('Вход выполнен успешно!', 'success')
            return redirect(url_for('index'))
        else:
            flash('Неверное имя пользователя или пароль', 'danger')
    
    return render_template('login.html')

@app.route('/logout')
@login_required
def logout():
    logout_user()
    flash('Вы вышли из системы', 'info')
    return redirect(url_for('login'))

@app.route('/')
@login_required
def index():
    local_devices = get_local_usb_devices()
    attached_devices = get_attached_devices()
    return render_template('index.html', local_devices=local_devices, attached_devices=attached_devices)

@app.route('/bind_device', methods=['POST'])
@login_required
def bind_device_route():
    busid = request.form.get('busid')
    if not busid:
        return jsonify({'success': False, 'message': 'Не указан busid устройства'}), 400
    
    success, message = bind_device(busid)
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
