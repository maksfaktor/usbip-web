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
    
    # Нормализуем путь используя общую функцию (она уже включает декодирование URL)
    path = normalize_path(path)
    
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
    
    # Определяем родительскую директорию для навигации "вверх"
    # Используем надежный способ с использованием os.path
    if path == '/' or path == '':
        # Мы в корне, родителя нет
        parent_path = '/'
    else:
        # Нормализуем путь и используем os.path.dirname для получения родительского пути
        parent_path = os.path.dirname(path)
        
        # Дополнительная проверка для пустого результата
        if not parent_path:
            parent_path = '/'
        else:
            # Убеждаемся, что родительский путь нормализован
            parent_path = normalize_path(parent_path)
            
    # Логируем информацию о путях для отладки
    logger.debug(f"Текущий путь: {path}, Родительский путь: {parent_path}")
    
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
    
    # Нормализуем текущий путь
    current_path = normalize_path(current_path)
    
    # Получаем и обрабатываем имя директории
    directory_name = request.form.get('directory_name', '').strip()
    
    if not directory_name:
        flash('Необходимо указать имя директории', 'warning')
        return redirect(url_for('storage.manage_storage', device_id=device_id, path=current_path))
    
    # Проверяем, что имя директории безопасно (расширенная проверка)
    if '/' in directory_name or '\\' in directory_name or '..' in directory_name or directory_name.startswith('.'):
        flash('Имя директории содержит недопустимые символы', 'danger')
        return redirect(url_for('storage.manage_storage', device_id=device_id, path=current_path))
    
    # Проверка на пробелы в конце имени и запрещенные символы Windows
    directory_name = directory_name.strip()
    forbidden_chars = '<>:"|?*'
    if any(c in directory_name for c in forbidden_chars):
        flash(f'Имя директории содержит недопустимые символы: {forbidden_chars}', 'danger')
        return redirect(url_for('storage.manage_storage', device_id=device_id, path=current_path))
    
    # Формируем полный путь к новой директории
    if current_path == '/':
        new_dir_path = directory_name
    else:
        # Обеспечиваем корректный путь без двойных слешей
        current_path_clean = current_path.strip('/')
        new_dir_path = f"{current_path_clean}/{directory_name}"
    
    # Логируем для отладки
    logger.debug(f"Создание директории: текущий путь={current_path}, имя директории={directory_name}, полный путь={new_dir_path}")
    
    try:
        # Создаем директорию
        success, error_message = create_directory(device, new_dir_path)
        
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
            
            # Пауза перед перенаправлением для гарантированного завершения операций
            import time
            time.sleep(0.5)
            
            # Перенаправляем в созданную директорию (если нужно открыть новую папку)
            if current_path == '/':
                redirect_path = f"/{new_dir_path}"
            else:
                redirect_path = f"{current_path}/{directory_name}"
            
            # Перенаправляем в текущую директорию (если нужно остаться в текущей)
            # redirect_path = current_path
            
            return redirect(url_for('storage.manage_storage', device_id=device_id, path=normalize_path(redirect_path)))
        else:
            # Используем конкретное сообщение об ошибке, если оно есть
            flash(error_message or 'Не удалось создать директорию', 'danger')
    except Exception as e:
        # В случае необработанной ошибки
        logger.error(f"Ошибка при создании директории {new_dir_path}: {str(e)}")
        flash(f'Произошла ошибка: {str(e)}', 'danger')
    
    # Перенаправляем в текущую директорию в случае ошибки
    return redirect(url_for('storage.manage_storage', device_id=device_id, path=current_path))

# Функция для стандартизированной нормализации пути
def normalize_path(path):
    """
    Нормализует путь для единообразного использования
    """
    if path is None:
        return '/'
    
    # Пытаемся декодировать URL-encoded символы, если они есть
    if '%' in path:
        try:
            from urllib.parse import unquote
            path = unquote(path)
        except Exception as e:
            logger.error(f"Ошибка при декодировании пути: {str(e)}")
    
    # Заменяем обратные слэши
    path = path.replace('\\', '/')
    
    # Убеждаемся, что путь начинается с "/"
    if not path.startswith('/'):
        path = '/' + path
        
    # Удаляем двойные слэши
    while '//' in path:
        path = path.replace('//', '/')
        
    # Удаляем конечный слэш (кроме корневого пути)
    if path != '/' and path.endswith('/'):
        path = path[:-1]
    
    # Очистка путей от возможных последовательностей ".." для безопасности
    parts = []
    for part in path.split('/'):
        if part == '..':
            if parts and parts[-1] != '':
                parts.pop()
        elif part and part != '.':
            parts.append(part)
    
    # Собираем путь обратно с начальным слешем
    clean_path = '/' + '/'.join(parts)
    
    return clean_path

@storage_bp.route('/storage/<int:device_id>/upload', methods=['POST'])
@login_required
def upload_storage_file(device_id):
    """
    Загрузка файла в хранилище
    """
    device = VirtualUsbDevice.query.get_or_404(device_id)
    
    # Получаем текущий путь
    current_path = request.form.get('current_path', '/')
    
    # Нормализуем текущий путь единой функцией
    current_path = normalize_path(current_path)
    
    # Проверяем, есть ли файл в запросе
    if 'file' not in request.files:
        flash('Не выбран файл для загрузки', 'warning')
        return redirect(url_for('storage.manage_storage', device_id=device_id, path=current_path))
    
    file = request.files['file']
    
    # Если пользователь не выбрал файл
    if file.filename == '':
        flash('Не выбран файл для загрузки', 'warning')
        return redirect(url_for('storage.manage_storage', device_id=device_id, path=current_path))
    
    # Логируем для отладки
    logger.debug(f"Загрузка файла: текущий путь={current_path}, имя файла={file.filename}")
    
    try:
        # Проверяем безопасность имени файла
        filename = secure_filename(file.filename)
        if not filename:
            flash('Недопустимое имя файла', 'danger')
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
            
            # Пауза перед перенаправлением для гарантированного завершения операций
            import time
            time.sleep(0.5)
            
            flash(f'Файл "{file_entry.filename}" успешно загружен', 'success')
        else:
            flash('Не удалось загрузить файл', 'danger')
    except Exception as e:
        logger.error(f"Ошибка при загрузке файла {file.filename}: {str(e)}")
        flash(f'Произошла ошибка при загрузке файла: {str(e)}', 'danger')
    
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
    
    # Нормализуем пути используя общую функцию (она уже включает декодирование URL)
    current_path = normalize_path(current_path)
    
    if item_path:
        item_path = normalize_path(item_path)
    
    # Логируем для отладки
    logger.debug(f"Удаление элемента: текущий путь={current_path}, путь элемента={item_path}")
    
    if not item_path:
        flash('Не указан путь к файлу или директории', 'warning')
        return redirect(url_for('storage.manage_storage', device_id=device_id, path=current_path))
    
    # Проверяем попытку удаления корневой директории
    if item_path == '/':
        flash('Невозможно удалить корневую директорию', 'danger')
        return redirect(url_for('storage.manage_storage', device_id=device_id, path=current_path))
    
    try:
        # Определяем тип элемента для логирования
        is_dir = False
        item_path_stripped = item_path.lstrip('/')
        
        # Проверяем признаки директории
        if item_path.endswith('/'):
            # Если путь заканчивается на '/', это директория
            is_dir = True
        elif device.storage_path and os.path.exists(device.storage_path):
            # Проверяем физический файл, если хранилище доступно
            full_path = os.path.join(device.storage_path, item_path_stripped)
            if os.path.exists(full_path) and os.path.isdir(full_path):
                is_dir = True
                
        element_type = 'директория' if is_dir else 'файл'
        logger.debug(f"Определен тип элемента: {element_type}")
        
        # Удаляем элемент
        success = delete_item(device, item_path)
        
        if success:
            # Записываем лог
            log_entry = LogEntry(
                level='INFO',
                message=f'Удален {element_type} {item_path} для устройства {device.name}',
                source='system'
            )
            db.session.add(log_entry)
            db.session.commit()
            
            flash(f'{element_type.capitalize()} успешно удален(а)', 'success')
            
            # Пауза перед перенаправлением для гарантированного завершения операций
            import time
            time.sleep(0.5)
            
            # Особая обработка при удалении директории
            if is_dir:
                # Проверяем текущую директорию - если она удалена, нужно перейти наверх
                if current_path == item_path or current_path.startswith(item_path + '/'):
                    # Получаем родительскую директорию с помощью os.path
                    parent_path = os.path.dirname(item_path)
                    
                    # Дополнительная проверка для пустого результата
                    if not parent_path or parent_path == '/':
                        parent_path = '/'
                        logger.debug(f"Переход в корневую директорию")
                        return redirect(url_for('storage.manage_storage', device_id=device_id))
                    else:
                        parent_path = normalize_path(parent_path)  # Нормализуем
                        logger.debug(f"Переход в родительскую директорию: {parent_path}")
                        return redirect(url_for('storage.manage_storage', device_id=device_id, path=parent_path))
        else:
            flash('Не удалось удалить элемент', 'danger')
    except Exception as e:
        # Логируем ошибку и показываем пользователю сообщение
        logger.error(f"Ошибка при удалении элемента {item_path}: {str(e)}")
        flash(f'Произошла ошибка при удалении: {str(e)}', 'danger')
    
    # В случае успешного удаления обычного файла или другой ошибки, остаемся в текущей директории
    return redirect(url_for('storage.manage_storage', device_id=device_id, path=current_path))

@storage_bp.route('/storage/<int:device_id>/download/<path:file_path>', methods=['GET'])
@login_required
def download_storage_file(device_id, file_path):
    """
    Скачивание файла из хранилища
    """
    device = VirtualUsbDevice.query.get_or_404(device_id)
    
    # Нормализуем путь к файлу используя единую функцию
    file_path = normalize_path(file_path)
    
    # Логируем для отладки
    logger.debug(f"Скачивание файла: устройство_id={device_id}, путь файла={file_path}")
    
    try:
        # Получаем путь к файлу для скачивания
        full_path, filename = download_file(device, file_path)
        
        if not full_path or not filename:
            flash('Файл не найден', 'warning')
            return redirect(url_for('storage.manage_storage', device_id=device_id))
        
        # Проверяем существование файла
        if not os.path.exists(full_path):
            flash('Файл не найден на физическом диске', 'warning')
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
    except Exception as e:
        # В случае ошибки
        logger.error(f"Ошибка при скачивании файла {file_path}: {str(e)}")
        flash(f'Произошла ошибка при скачивании файла: {str(e)}', 'danger')
        return redirect(url_for('storage.manage_storage', device_id=device_id))