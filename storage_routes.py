import os
import logging
from flask import Blueprint, render_template, redirect, url_for, request, flash, send_file, abort
from flask_login import login_required, current_user
from werkzeug.utils import secure_filename
from models import db, VirtualUsbDevice, VirtualUsbFile, LogEntry
from virtual_storage_utils import (
    create_device_storage, delete_device_storage, resize_device_storage,
    get_device_storage_usage, list_device_files, create_directory,
    delete_item, upload_file, get_storage_stats, download_file
)

# Настройка логгирования
logger = logging.getLogger(__name__)

# Создаем Blueprint для роутов управления хранилищем
storage_bp = Blueprint('storage', __name__)

@storage_bp.route('/storage/<int:device_id>', methods=['GET'])
@storage_bp.route('/storage/<int:device_id>/<path:path>', methods=['GET'])
@login_required
def manage_storage(device_id, path=None):
    """
    Страница управления файлами виртуального USB-устройства
    """
    # Получаем информацию об устройстве
    device = VirtualUsbDevice.query.get_or_404(device_id)
    
    # Проверяем, что устройство имеет тип storage
    if device.device_type != 'storage':
        flash('Управление файлами доступно только для устройств типа "storage"', 'warning')
        return redirect(url_for('virtual_devices'))
    
    # Если путь не указан, используем корневую директорию
    if path is None:
        path = '/'
    else:
        # Нормализуем путь
        if not path.startswith('/'):
            path = '/' + path
    
    # Если хранилище еще не создано, создаем его
    if not device.storage_path or not os.path.exists(device.storage_path):
        # Если размер не указан, используем значение по умолчанию (1 ГБ)
        storage_size = device.storage_size or 1024
        success = create_device_storage(device, storage_size)
        if not success:
            flash('Не удалось создать хранилище для устройства', 'danger')
            return redirect(url_for('virtual_devices'))
        
        # Записываем лог
        log_entry = LogEntry(
            level='INFO',
            message=f'Создано хранилище для устройства {device.name} размером {storage_size} МБ',
            source='system'
        )
        db.session.add(log_entry)
        db.session.commit()
    
    # Получаем список файлов и директорий
    files = list_device_files(device, path)
    
    # Получаем статистику использования хранилища
    stats = get_storage_stats(device)
    
    # Определяем родительскую директорию для навигации "назад"
    parent_path = os.path.dirname(path.rstrip('/'))
    if not parent_path:
        parent_path = '/'
    
    return render_template(
        'storage_manager.html',
        device=device,
        files=files,
        stats=stats,
        current_path=path,
        parent_path=parent_path
    )

@storage_bp.route('/storage/<int:device_id>/resize', methods=['POST'])
@login_required
def resize_storage(device_id):
    """
    Изменение размера хранилища
    """
    device = VirtualUsbDevice.query.get_or_404(device_id)
    
    # Проверяем, что устройство имеет тип storage
    if device.device_type != 'storage':
        flash('Изменение размера доступно только для устройств типа "storage"', 'warning')
        return redirect(url_for('virtual_devices'))
    
    # Получаем новый размер из формы
    try:
        new_size = int(request.form.get('storage_size', 1024))
    except ValueError:
        flash('Некорректный размер хранилища', 'danger')
        return redirect(url_for('storage.manage_storage', device_id=device_id))
    
    # Проверяем диапазон размера
    if new_size < 1 or new_size > 16384:
        flash('Размер хранилища должен быть от 1 МБ до 16 ГБ', 'warning')
        return redirect(url_for('storage.manage_storage', device_id=device_id))
    
    # Изменяем размер хранилища
    success = resize_device_storage(device, new_size)
    
    if success:
        # Записываем лог
        log_entry = LogEntry(
            level='INFO',
            message=f'Изменен размер хранилища для устройства {device.name} на {new_size} МБ',
            source='system'
        )
        db.session.add(log_entry)
        db.session.commit()
        
        flash(f'Размер хранилища успешно изменен на {new_size} МБ', 'success')
    else:
        flash('Не удалось изменить размер хранилища', 'danger')
    
    return redirect(url_for('storage.manage_storage', device_id=device_id))

@storage_bp.route('/storage/<int:device_id>/create_directory', methods=['POST'])
@login_required
def create_storage_directory(device_id):
    """
    Создание директории в хранилище
    """
    device = VirtualUsbDevice.query.get_or_404(device_id)
    
    # Получаем текущий путь и имя новой директории
    current_path = request.form.get('current_path', '/')
    directory_name = request.form.get('directory_name', '').strip()
    
    if not directory_name:
        flash('Необходимо указать имя директории', 'warning')
        return redirect(url_for('storage.manage_storage', device_id=device_id, path=current_path))
    
    # Проверяем, что имя директории безопасно
    if '/' in directory_name or '\\' in directory_name or '..' in directory_name:
        flash('Имя директории содержит недопустимые символы', 'danger')
        return redirect(url_for('storage.manage_storage', device_id=device_id, path=current_path))
    
    # Формируем полный путь к новой директории
    if current_path == '/':
        new_dir_path = directory_name
    else:
        new_dir_path = os.path.join(current_path.lstrip('/'), directory_name)
    
    # Создаем директорию
    success = create_directory(device, new_dir_path)
    
    if success:
        # Записываем лог
        log_entry = LogEntry(
            level='INFO',
            message=f'Создана директория {new_dir_path} для устройства {device.name}',
            source='system'
        )
        db.session.add(log_entry)
        db.session.commit()
        
        flash(f'Директория "{directory_name}" успешно создана', 'success')
    else:
        flash('Не удалось создать директорию', 'danger')
    
    return redirect(url_for('storage.manage_storage', device_id=device_id, path=current_path))

@storage_bp.route('/storage/<int:device_id>/upload', methods=['POST'])
@login_required
def upload_storage_file(device_id):
    """
    Загрузка файла в хранилище
    """
    device = VirtualUsbDevice.query.get_or_404(device_id)
    
    # Получаем текущий путь
    current_path = request.form.get('current_path', '/')
    
    # Проверяем, есть ли файл в запросе
    if 'file' not in request.files:
        flash('Не выбран файл для загрузки', 'warning')
        return redirect(url_for('storage.manage_storage', device_id=device_id, path=current_path))
    
    file = request.files['file']
    
    # Если пользователь не выбрал файл
    if file.filename == '':
        flash('Не выбран файл для загрузки', 'warning')
        return redirect(url_for('storage.manage_storage', device_id=device_id, path=current_path))
    
    # Загружаем файл
    file_entry = upload_file(device, file, current_path)
    
    if file_entry:
        # Записываем лог
        log_entry = LogEntry(
            level='INFO',
            message=f'Загружен файл {file_entry.filename} для устройства {device.name}',
            source='system'
        )
        db.session.add(log_entry)
        db.session.commit()
        
        flash(f'Файл "{file_entry.filename}" успешно загружен', 'success')
    else:
        flash('Не удалось загрузить файл', 'danger')
    
    return redirect(url_for('storage.manage_storage', device_id=device_id, path=current_path))

@storage_bp.route('/storage/<int:device_id>/delete_item', methods=['POST'])
@login_required
def delete_storage_item(device_id):
    """
    Удаление файла или директории из хранилища
    """
    device = VirtualUsbDevice.query.get_or_404(device_id)
    
    # Получаем путь к элементу и текущий путь
    item_path = request.form.get('item_path', '')
    current_path = request.form.get('current_path', '/')
    
    if not item_path:
        flash('Не указан путь к файлу или директории', 'warning')
        return redirect(url_for('storage.manage_storage', device_id=device_id, path=current_path))
    
    # Удаляем элемент
    success = delete_item(device, item_path)
    
    if success:
        # Определяем тип элемента для логирования
        is_dir = '/.' not in item_path and item_path.endswith('/')
        element_type = 'директория' if is_dir else 'файл'
        
        # Записываем лог
        log_entry = LogEntry(
            level='INFO',
            message=f'Удален {element_type} {item_path} для устройства {device.name}',
            source='system'
        )
        db.session.add(log_entry)
        db.session.commit()
        
        flash(f'{element_type.capitalize()} успешно удален(а)', 'success')
    else:
        flash('Не удалось удалить элемент', 'danger')
    
    return redirect(url_for('storage.manage_storage', device_id=device_id, path=current_path))

@storage_bp.route('/storage/<int:device_id>/download/<path:file_path>', methods=['GET'])
@login_required
def download_storage_file(device_id, file_path):
    """
    Скачивание файла из хранилища
    """
    device = VirtualUsbDevice.query.get_or_404(device_id)
    
    # Получаем путь к файлу для скачивания
    full_path, filename = download_file(device, file_path)
    
    if not full_path or not filename:
        flash('Файл не найден', 'warning')
        return redirect(url_for('storage.manage_storage', device_id=device_id))
    
    # Записываем лог
    log_entry = LogEntry(
        level='INFO',
        message=f'Скачан файл {file_path} для устройства {device.name}',
        source='system'
    )
    db.session.add(log_entry)
    db.session.commit()
    
    # Отправляем файл пользователю
    return send_file(full_path, download_name=filename, as_attachment=True)