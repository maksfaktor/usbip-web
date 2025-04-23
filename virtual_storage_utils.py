import os
import shutil
import json
import logging
from typing import List, Dict, Any, Optional, Tuple
from werkzeug.utils import secure_filename
from models import VirtualUsbDevice, VirtualUsbFile, db

# Настройка логгера
logger = logging.getLogger(__name__)

# Базовая директория для хранения файлов виртуальных устройств
VIRTUAL_STORAGE_BASE_DIR = "virtual_storage"

def ensure_storage_dir_exists() -> None:
    """
    Убедиться, что базовая директория для хранения файлов существует
    """
    if not os.path.exists(VIRTUAL_STORAGE_BASE_DIR):
        os.makedirs(VIRTUAL_STORAGE_BASE_DIR, exist_ok=True)
        logger.info(f"Создана базовая директория для виртуальных устройств: {VIRTUAL_STORAGE_BASE_DIR}")

def create_device_storage(device: VirtualUsbDevice, size_mb: int = 1024) -> bool:
    """
    Создать хранилище для виртуального USB-устройства
    
    Args:
        device: Модель виртуального устройства
        size_mb: Размер хранилища в МБ
        
    Returns:
        bool: Успешность создания хранилища
    """
    ensure_storage_dir_exists()
    
    # Создаем уникальный путь для устройства
    device_dir = os.path.join(VIRTUAL_STORAGE_BASE_DIR, f"device_{device.id}")
    
    # Если директория уже существует, очищаем её
    if os.path.exists(device_dir):
        try:
            shutil.rmtree(device_dir)
        except Exception as e:
            logger.error(f"Ошибка при очистке директории устройства: {e}")
            return False
    
    # Создаем директорию для устройства
    try:
        os.makedirs(device_dir, exist_ok=True)
        
        # Обновляем информацию об устройстве
        device.storage_path = device_dir
        device.storage_size = size_mb
        db.session.commit()
        
        logger.info(f"Создано хранилище для устройства {device.name} размером {size_mb} МБ")
        return True
    except Exception as e:
        logger.error(f"Ошибка при создании хранилища для устройства: {e}")
        return False

def delete_device_storage(device: VirtualUsbDevice) -> bool:
    """
    Удалить хранилище для виртуального USB-устройства
    
    Args:
        device: Модель виртуального устройства
        
    Returns:
        bool: Успешность удаления хранилища
    """
    if not device.storage_path or not os.path.exists(device.storage_path):
        logger.warning(f"Хранилище для устройства {device.name} не существует")
        return True
    
    try:
        shutil.rmtree(device.storage_path)
        
        # Удаляем записи о файлах из базы данных
        VirtualUsbFile.query.filter_by(device_id=device.id).delete()
        
        # Обновляем информацию об устройстве
        device.storage_path = None
        device.storage_size = 0
        db.session.commit()
        
        logger.info(f"Удалено хранилище для устройства {device.name}")
        return True
    except Exception as e:
        logger.error(f"Ошибка при удалении хранилища для устройства: {e}")
        return False

def resize_device_storage(device: VirtualUsbDevice, new_size_mb: int) -> bool:
    """
    Изменить размер хранилища для виртуального USB-устройства
    
    Args:
        device: Модель виртуального устройства
        new_size_mb: Новый размер хранилища в МБ
        
    Returns:
        bool: Успешность изменения размера хранилища
    """
    # Проверяем, что новый размер не меньше текущего использования
    used_space = get_device_storage_usage(device)
    if used_space > new_size_mb * 1024 * 1024:
        logger.error(f"Невозможно уменьшить размер хранилища: используется {used_space/(1024*1024):.2f} МБ")
        return False
    
    # Обновляем информацию об устройстве
    device.storage_size = new_size_mb
    db.session.commit()
    
    logger.info(f"Изменен размер хранилища для устройства {device.name} на {new_size_mb} МБ")
    return True

def get_device_storage_usage(device: VirtualUsbDevice) -> int:
    """
    Получить текущее использование хранилища для виртуального USB-устройства
    
    Args:
        device: Модель виртуального устройства
        
    Returns:
        int: Использование хранилища в байтах
    """
    if not device.storage_path or not os.path.exists(device.storage_path):
        return 0
    
    total_size = 0
    for dirpath, dirnames, filenames in os.walk(device.storage_path):
        for filename in filenames:
            file_path = os.path.join(dirpath, filename)
            total_size += os.path.getsize(file_path)
    
    return total_size

def list_device_files(device: VirtualUsbDevice, directory: str = "/") -> List[Dict[str, Any]]:
    """
    Получить список файлов в хранилище виртуального USB-устройства
    
    Args:
        device: Модель виртуального устройства
        directory: Путь внутри хранилища
        
    Returns:
        List[Dict[str, Any]]: Список файлов и директорий
    """
    # Нормализуем путь
    if directory == "/":
        directory = ""
    
    result = []
    
    # Проверяем существует ли хранилище
    storage_exists = device.storage_path and os.path.exists(device.storage_path)
    
    if storage_exists:
        # Полный путь к директории
        dir_path = os.path.join(device.storage_path, directory.lstrip("/"))
        
        if os.path.exists(dir_path) and os.path.isdir(dir_path):
            # Список директорий
            for dirname in os.listdir(dir_path):
                full_path = os.path.join(dir_path, dirname)
                if os.path.isdir(full_path):
                    result.append({
                        "name": dirname,
                        "type": "directory",
                        "size": 0,
                        "path": os.path.join(directory, dirname).replace("\\", "/"),
                        "modified": os.path.getmtime(full_path)
                    })
    
    # Список файлов из базы данных (работает и при отключенном устройстве)
    for file_entry in VirtualUsbFile.query.filter_by(device_id=device.id).all():
        # Получаем только файлы в текущей директории
        file_dir = os.path.dirname(file_entry.file_path)
        
        # Нормализуем пути для сравнения
        dir_path_norm = directory.strip("/")
        file_dir_norm = file_dir.strip("/")
        
        if file_dir_norm == dir_path_norm:
            # Добавляем информацию о доступности файла
            file_exists = storage_exists and os.path.exists(os.path.join(device.storage_path, file_entry.file_path.lstrip("/")))
            
            result.append({
                "name": os.path.basename(file_entry.filename),
                "type": "file",
                "size": file_entry.file_size,
                "path": file_entry.file_path,
                "modified": file_entry.updated_at.timestamp() if file_entry.updated_at else 0,
                "available": file_exists
            })
    
    return result

def create_directory(device: VirtualUsbDevice, directory_path: str) -> bool:
    """
    Создать директорию в хранилище виртуального USB-устройства
    
    Args:
        device: Модель виртуального устройства
        directory_path: Путь к новой директории
        
    Returns:
        bool: Успешность создания директории
    """
    # Нормализуем путь
    directory_path = directory_path.lstrip("/")
    
    # Проверяем, существует ли физическое хранилище
    storage_exists = device.storage_path and os.path.exists(device.storage_path)
    
    # Создаем директорию в физическом хранилище, если оно доступно
    if storage_exists:
        # Полный путь к директории
        dir_path = os.path.join(device.storage_path, directory_path)
        
        try:
            os.makedirs(dir_path, exist_ok=True)
            logger.info(f"Создана директория {directory_path} для устройства {device.name}")
            return True
        except Exception as e:
            logger.error(f"Ошибка при создании директории в физическом хранилище: {e}")
            return False
    else:
        # Если хранилище не доступно, просто регистрируем создание директории в логах
        logger.info(f"Зарегистрировано создание директории {directory_path} для устройства {device.name} (физическое хранилище недоступно)")
        return True

def delete_item(device: VirtualUsbDevice, item_path: str) -> bool:
    """
    Удалить файл или директорию из хранилища виртуального USB-устройства
    
    Args:
        device: Модель виртуального устройства
        item_path: Путь к файлу или директории
        
    Returns:
        bool: Успешность удаления
    """
    # Нормализуем путь
    item_path = item_path.lstrip("/")
    
    # Проверяем, существует ли физическое хранилище
    storage_exists = device.storage_path and os.path.exists(device.storage_path)
    
    # Флаг для определения того, является ли элемент директорией
    is_directory = False
    
    # Удаляем физический файл или директорию, если хранилище доступно
    if storage_exists:
        # Полный путь к элементу
        full_path = os.path.join(device.storage_path, item_path)
        
        if os.path.exists(full_path):
            try:
                if os.path.isdir(full_path):
                    # Это директория
                    is_directory = True
                    # Удаляем директорию и все её содержимое
                    shutil.rmtree(full_path)
                else:
                    # Удаляем файл
                    os.remove(full_path)
            except Exception as e:
                logger.error(f"Ошибка при удалении элемента в физическом хранилище: {e}")
                # Продолжаем, чтобы очистить записи в базе данных
    
    try:
        # Удаляем записи из базы данных
        if is_directory or item_path.endswith('/'):
            # Удаляем все файлы внутри директории
            for file_entry in VirtualUsbFile.query.filter_by(device_id=device.id).all():
                if file_entry.file_path.startswith(item_path):
                    db.session.delete(file_entry)
        else:
            # Удаляем запись о файле из базы данных
            file_entry = VirtualUsbFile.query.filter_by(
                device_id=device.id, 
                file_path=item_path
            ).first()
            
            if file_entry:
                db.session.delete(file_entry)
            else:
                # Если запись не найдена и хранилище не существует, считаем ошибкой
                if not storage_exists:
                    logger.warning(f"Элемент {item_path} не найден в базе данных и физическое хранилище недоступно")
                    return False
        
        db.session.commit()
        logger.info(f"Удален элемент {item_path} для устройства {device.name}")
        return True
    except Exception as e:
        logger.error(f"Ошибка при удалении записей в базе данных: {e}")
        return False

def upload_file(device: VirtualUsbDevice, file, destination_path: str = "/") -> Optional[VirtualUsbFile]:
    """
    Загрузить файл в хранилище виртуального USB-устройства
    
    Args:
        device: Модель виртуального устройства
        file: Файловый объект из request.files
        destination_path: Путь для сохранения файла
        
    Returns:
        Optional[VirtualUsbFile]: Созданная запись о файле или None при ошибке
    """
    # Проверяем, существует ли физическое хранилище
    storage_exists = device.storage_path and os.path.exists(device.storage_path)
    
    # Если хранилище недоступно, возвращаем ошибку
    if not storage_exists:
        logger.error(f"Невозможно загрузить файл: хранилище для устройства {device.name} недоступно")
        return None
    
    # Проверяем доступное место
    used_space = get_device_storage_usage(device)
    max_space = device.storage_size * 1024 * 1024  # Переводим МБ в байты
    
    if file.content_length and used_space + file.content_length > max_space:
        logger.error(f"Недостаточно места в хранилище: используется {used_space/(1024*1024):.2f} МБ из {device.storage_size} МБ")
        return None
    
    # Безопасное имя файла
    filename = secure_filename(file.filename)
    
    # Нормализуем путь назначения
    if destination_path == "/":
        destination_path = ""
    else:
        destination_path = destination_path.lstrip("/").rstrip("/")
    
    # Создаем директории, если нужно
    if destination_path:
        dir_path = os.path.join(device.storage_path, destination_path)
        os.makedirs(dir_path, exist_ok=True)
    
    # Путь к файлу относительно хранилища
    rel_file_path = os.path.join(destination_path, filename).replace("\\", "/")
    
    # Полный путь для сохранения файла
    full_path = os.path.join(device.storage_path, rel_file_path)
    
    try:
        # Сохраняем файл
        file.save(full_path)
        
        # Получаем размер файла
        file_size = os.path.getsize(full_path)
        
        # Определяем тип файла по расширению
        _, file_extension = os.path.splitext(filename)
        file_type = file_extension.lower().lstrip('.') if file_extension else 'unknown'
        
        # Проверяем, существует ли уже запись о файле
        existing_file = VirtualUsbFile.query.filter_by(
            device_id=device.id,
            file_path=rel_file_path
        ).first()
        
        if existing_file:
            # Обновляем существующую запись
            existing_file.file_size = file_size
            existing_file.file_type = file_type
            db.session.commit()
            logger.info(f"Обновлен файл {rel_file_path} для устройства {device.name}")
            return existing_file
        else:
            # Создаем новую запись о файле
            new_file = VirtualUsbFile(
                device_id=device.id,
                filename=filename,
                file_path=rel_file_path,
                file_size=file_size,
                file_type=file_type
            )
            
            db.session.add(new_file)
            db.session.commit()
            
            logger.info(f"Загружен файл {rel_file_path} для устройства {device.name}")
            return new_file
    except Exception as e:
        logger.error(f"Ошибка при загрузке файла: {e}")
        return None

def get_storage_stats(device: VirtualUsbDevice) -> Dict[str, Any]:
    """
    Получить статистику использования хранилища
    
    Args:
        device: Модель виртуального устройства
        
    Returns:
        Dict[str, Any]: Статистика использования хранилища
    """
    # Проверяем, существует ли физическое хранилище
    storage_exists = device.storage_path and os.path.exists(device.storage_path)
    
    # Определяем размер устройства (в МБ)
    storage_size = device.storage_size or 1024  # По умолчанию 1 ГБ
    
    # Получаем количество файлов из БД
    file_count = VirtualUsbFile.query.filter_by(device_id=device.id).count()
    
    # Оцениваем использованное пространство
    if storage_exists:
        # Если хранилище доступно, получаем точную информацию
        used_space = get_device_storage_usage(device)
        
        # Подсчитываем количество директорий
        dir_count = 0
        for _, dirnames, _ in os.walk(device.storage_path):
            dir_count += len(dirnames)
    else:
        # Если хранилище недоступно, оцениваем использованное место по файлам в БД
        used_space = 0
        for file_entry in VirtualUsbFile.query.filter_by(device_id=device.id).all():
            used_space += file_entry.file_size
        
        # Предполагаем, что директорий нет, когда хранилище недоступно
        dir_count = 0
    
    # Вычисляем максимальный размер в байтах
    max_space = storage_size * 1024 * 1024  # Переводим МБ в байты
    
    # Формируем статистику
    return {
        "total_size_mb": storage_size,
        "used_space_bytes": used_space,
        "used_space_mb": used_space / (1024 * 1024),
        "free_space_bytes": max(0, max_space - used_space),
        "free_space_mb": max(0, (max_space - used_space) / (1024 * 1024)),
        "usage_percent": (used_space / max_space * 100) if max_space > 0 else 0,
        "file_count": file_count,
        "directory_count": dir_count,
        "storage_available": storage_exists
    }

def download_file(device: VirtualUsbDevice, file_path: str) -> Tuple[Optional[str], Optional[str]]:
    """
    Получить путь к файлу для скачивания
    
    Args:
        device: Модель виртуального устройства
        file_path: Путь к файлу относительно хранилища
        
    Returns:
        Tuple[Optional[str], Optional[str]]: (полный путь к файлу, имя файла) или (None, None) при ошибке
    """
    if not device.storage_path or not os.path.exists(device.storage_path):
        logger.error(f"Хранилище для устройства {device.name} не существует")
        return None, None
    
    # Нормализуем путь
    file_path = file_path.lstrip("/")
    
    # Полный путь к файлу
    full_path = os.path.join(device.storage_path, file_path)
    
    if not os.path.exists(full_path) or not os.path.isfile(full_path):
        logger.error(f"Файл {file_path} не существует")
        return None, None
    
    # Получаем имя файла
    filename = os.path.basename(file_path)
    
    return full_path, filename