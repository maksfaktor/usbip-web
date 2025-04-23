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
    # Предварительная нормализация пути: заменяем обратные слэши и удаляем двойные слэши
    directory = directory.replace("\\", "/")
    while "//" in directory:
        directory = directory.replace("//", "/")
        
    # Нормализуем путь для работы с директориями
    if directory == "/":
        directory = ""
    else:
        # Удаляем конечный слэш, если он есть
        directory = directory.rstrip("/")
        
    # Логируем для отладки
    logger.debug(f"Получение списка файлов: устройство={device.name}, директория='{directory}'")
    
    result = []
    
    # Проверяем существует ли хранилище
    storage_exists = device.storage_path and os.path.exists(device.storage_path)
    
    if storage_exists:
        # Полный путь к директории
        dir_path = os.path.join(device.storage_path, directory.lstrip("/"))
        
        # Логируем реальный путь в файловой системе
        logger.debug(f"Физический путь к директории: {dir_path}")
        
        if os.path.exists(dir_path) and os.path.isdir(dir_path):
            # Список директорий
            for dirname in os.listdir(dir_path):
                full_path = os.path.join(dir_path, dirname)
                if os.path.isdir(full_path):
                    # Формируем путь для URL с прямыми слэшами
                    path_for_url = directory + "/" + dirname if directory else "/" + dirname
                    path_for_url = path_for_url.replace("//", "/")
                    
                    result.append({
                        "name": dirname,
                        "type": "directory",
                        "size": 0,
                        "path": path_for_url,
                        "modified": os.path.getmtime(full_path)
                    })
    
    # Список файлов из базы данных (работает и при отключенном устройстве)
    for file_entry in VirtualUsbFile.query.filter_by(device_id=device.id).all():
        # Получаем только файлы в текущей директории
        file_path = file_entry.file_path.replace("\\", "/")
        file_dir = os.path.dirname(file_path)
        
        # Нормализуем пути для сравнения без начальных и конечных слэшей
        dir_path_norm = directory.strip("/")
        file_dir_norm = file_dir.strip("/")
        
        logger.debug(f"Сравнение путей: директория='{dir_path_norm}', файл в '{file_dir_norm}'")
        
        # Проверяем, совпадает ли директория файла с текущей директорией
        if file_dir_norm == dir_path_norm:
            # Добавляем информацию о доступности файла
            file_exists = storage_exists and os.path.exists(os.path.join(
                device.storage_path, file_entry.file_path.lstrip("/")))
            
            result.append({
                "name": os.path.basename(file_entry.filename),
                "type": "file",
                "size": file_entry.file_size,
                "path": file_path,
                "modified": file_entry.updated_at.timestamp() if file_entry.updated_at else 0,
                "available": file_exists
            })
    
    return result

def create_directory(device: VirtualUsbDevice, directory_path: str) -> Tuple[bool, Optional[str]]:
    """
    Создать директорию в хранилище виртуального USB-устройства
    
    Args:
        device: Модель виртуального устройства
        directory_path: Путь к новой директории
        
    Returns:
        Tuple[bool, Optional[str]]: (успешность создания директории, сообщение об ошибке)
    """
    # Валидация имени директории
    # Нормализуем входной путь
    directory_path = normalize_path(directory_path)
    
    # Извлекаем конечное имя директории из пути
    dir_name = os.path.basename(directory_path)
    
    # Проверка на допустимые символы
    if not dir_name or dir_name == '..' or dir_name == '.' or any(c in dir_name for c in ['<', '>', ':', '"', '/', '\\', '|', '?', '*']):
        return False, "Имя директории содержит недопустимые символы"
    
    # Обрабатываем случай, когда создаваемая директория содержит пробелы или имеет непечатаемые символы
    if dir_name.strip() != dir_name:
        return False, "Имя директории не должно начинаться или заканчиваться пробелами"
    
    # Удаляем начальный слэш для работы с файловой системой
    clean_path = directory_path.lstrip("/")
    
    # Логируем для отладки
    logger.debug(f"Создание директории: устройство={device.name}, путь='{clean_path}'")
    
    # Проверяем, существует ли физическое хранилище
    storage_exists = device.storage_path and os.path.exists(device.storage_path)
    
    # Если создаваемая директория - корень, то считаем, что она уже существует
    if not clean_path or clean_path == '.' or clean_path == '/':
        logger.warning(f"Попытка создать корневую директорию для устройства {device.name}")
        return False, "Невозможно создать корневую директорию"
    
    # Проверяем, существует ли родительская директория
    parent_dir = os.path.dirname(clean_path)
    
    # Создаем директорию в физическом хранилище, если оно доступно
    if storage_exists:
        # Полный путь к директории
        dir_path = os.path.join(device.storage_path, clean_path)
        parent_path = os.path.join(device.storage_path, parent_dir) if parent_dir else device.storage_path
        
        # Проверяем существование родительской директории
        if parent_dir and not os.path.exists(parent_path):
            logger.warning(f"Родительская директория {parent_dir} не существует для устройства {device.name}")
            return False, "Родительская директория не существует"
        
        # Проверяем, существует ли уже директория с таким именем
        if os.path.exists(dir_path):
            # Проверяем, является ли существующий путь файлом
            if os.path.isfile(dir_path):
                logger.warning(f"Путь {clean_path} уже существует как файл для устройства {device.name}")
                return False, "По указанному пути уже существует файл"
                
            logger.warning(f"Директория {clean_path} уже существует для устройства {device.name}")
            return False, "Директория с таким именем уже существует"
        
        try:
            # Создаем директорию, используя exist_ok=False для явного контроля ошибок
            os.makedirs(dir_path, exist_ok=False)
            logger.info(f"Создана директория {clean_path} для устройства {device.name}")
            
            # Небольшая задержка для синхронизации файловой системы
            import time
            time.sleep(0.1)
            
            return True, None
        except FileExistsError:
            logger.warning(f"Директория {clean_path} уже существует для устройства {device.name}")
            return False, "Директория с таким именем уже существует"
        except PermissionError:
            logger.error(f"Недостаточно прав для создания директории {clean_path}")
            return False, "Недостаточно прав для создания директории"
        except Exception as e:
            error_msg = f"Ошибка при создании директории: {str(e)}"
            logger.error(f"{error_msg}")
            return False, error_msg
    else:
        # Если хранилище не доступно, просто регистрируем создание директории в логах
        logger.info(f"Зарегистрировано создание директории {clean_path} для устройства {device.name} (физическое хранилище недоступно)")
        return True, None


def normalize_path(path: str) -> str:
    """
    Нормализует путь для единообразного использования
    
    Args:
        path: Исходный путь
        
    Returns:
        str: Нормализованный путь
    """
    if path is None:
        return '/'
        
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
        
    return path

def delete_item(device: VirtualUsbDevice, item_path: str) -> bool:
    """
    Удалить файл или директорию из хранилища виртуального USB-устройства
    
    Args:
        device: Модель виртуального устройства
        item_path: Путь к файлу или директории
        
    Returns:
        bool: Успешность удаления
    """
    # Нормализуем путь используя единую функцию
    item_path = normalize_path(item_path)
    
    # Проверка на попытку удаления корневой директории
    if item_path == '/':
        logger.error(f"Попытка удалить корневую директорию устройства {device.name}")
        return False
    
    # Удаляем начальный слэш для работы с файловой системой
    clean_path = item_path.lstrip("/")
    
    # Логируем для отладки
    logger.debug(f"Удаление элемента: устройство={device.name}, путь='{clean_path}'")
    
    # Проверяем, существует ли физическое хранилище
    storage_exists = device.storage_path and os.path.exists(device.storage_path)
    
    # Флаг для определения того, является ли элемент директорией
    is_directory = False
    
    # Удаляем физический файл или директорию, если хранилище доступно
    if storage_exists:
        # Полный путь к элементу
        full_path = os.path.join(device.storage_path, clean_path)
        logger.debug(f"Физический путь к удаляемому элементу: {full_path}")
        
        if os.path.exists(full_path):
            try:
                if os.path.isdir(full_path):
                    # Это директория
                    is_directory = True
                    
                    # Проверяем, пуста ли директория
                    if not os.listdir(full_path):
                        # Если директория пуста, можно использовать os.rmdir
                        os.rmdir(full_path)
                    else:
                        # Удаляем директорию и все её содержимое
                        shutil.rmtree(full_path)
                    
                    logger.debug(f"Успешно удалена директория {full_path}")
                else:
                    # Удаляем файл
                    os.remove(full_path)
                    logger.debug(f"Успешно удален файл {full_path}")
                
                # Небольшая задержка для синхронизации файловой системы
                import time
                time.sleep(0.1)
            except PermissionError:
                logger.error(f"Недостаточно прав для удаления элемента {full_path}")
                return False
            except Exception as e:
                logger.error(f"Ошибка при удалении элемента в физическом хранилище: {e}")
                # В случае серьезной ошибки, прерываем операцию
                return False
    
    try:
        # Определяем, является ли элемент директорией, если мы еще не знаем
        if not is_directory and item_path.endswith('/'):
            is_directory = True
            
        logger.debug(f"Элемент определен как {'директория' if is_directory else 'файл'}")
        
        # Удаляем записи из базы данных
        if is_directory:
            # Нормализуем путь для сравнения с путями в БД
            norm_path = clean_path
            if not norm_path.endswith('/'):
                norm_path += '/'
                
            # Удаляем все файлы внутри директории
            deleted_count = 0
            for file_entry in VirtualUsbFile.query.filter_by(device_id=device.id).all():
                # Нормализуем путь файла
                file_path = file_entry.file_path.replace("\\", "/")
                file_path = '/' + file_path.lstrip('/')
                
                # Проверяем, что файл находится в удаляемой директории или это она сама
                if file_path.startswith(item_path + '/') or file_path == item_path:
                    logger.debug(f"Удаление файла из БД: {file_path}")
                    db.session.delete(file_entry)
                    deleted_count += 1
                    
            if deleted_count == 0 and not storage_exists:
                # Если не найдено файлов для удаления и физическое хранилище недоступно,
                # проверяем существование самой директории в другой логике
                logger.warning(f"Не найдено файлов для удаления в директории {item_path}")
        else:
            # Удаляем запись о файле из базы данных
            file_entry = VirtualUsbFile.query.filter_by(
                device_id=device.id, 
                file_path=clean_path
            ).first()
            
            if file_entry:
                logger.debug(f"Удаление файла из БД: {file_entry.file_path}")
                db.session.delete(file_entry)
            else:
                # Попытаемся найти файл, игнорируя начальные слэши
                file_entry = VirtualUsbFile.query.filter(
                    VirtualUsbFile.device_id == device.id,
                    VirtualUsbFile.file_path.like(f"%{clean_path}")
                ).first()
                
                if file_entry:
                    logger.debug(f"Удаление файла из БД (альтернативный поиск): {file_entry.file_path}")
                    db.session.delete(file_entry)
                elif not storage_exists:
                    # Если запись не найдена и хранилище не существует, считаем ошибкой
                    logger.warning(f"Элемент {clean_path} не найден в базе данных и физическое хранилище недоступно")
                    return False
        
        db.session.commit()
        
        # Еще одна маленькая задержка после коммита
        import time
        time.sleep(0.1)
        
        logger.info(f"Удален элемент {item_path} для устройства {device.name}")
        return True
    except Exception as e:
        logger.error(f"Ошибка при удалении записей в базе данных: {e}")
        db.session.rollback()  # Откатываем транзакцию при ошибке
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
    # Нормализуем путь назначения с использованием единой функции
    destination_path = normalize_path(destination_path)
    
    # Логируем для отладки
    logger.debug(f"Загрузка файла: устройство={device.name}, путь='{destination_path}', файл='{file.filename}'")
    
    # Проверяем имя файла
    if not file.filename:
        logger.error("Невозможно загрузить файл: пустое имя файла")
        return None
    
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
    
    # Безопасное имя файла (удаляем небезопасные символы)
    filename = secure_filename(file.filename)
    
    if not filename:
        logger.error(f"Невозможно загрузить файл: небезопасное имя файла '{file.filename}'")
        return None
    
    # Проверка на пустое имя файла после очистки
    if not filename.strip():
        logger.error("Невозможно загрузить файл: имя файла содержит только недопустимые символы")
        return None
    
    # Преобразуем путь назначения для работы с файловой системой
    dest_dir = destination_path.lstrip("/")
    if dest_dir == "":
        # Корневая директория
        clean_dest_path = ""
    else:
        # Удаляем конечный слэш, но сохраняем путь
        clean_dest_path = dest_dir
    
    try:
        # Создаем директории, если нужно
        if clean_dest_path:
            dir_path = os.path.join(device.storage_path, clean_dest_path)
            
            # Проверяем, существует ли директория
            if not os.path.exists(dir_path):
                # Если директория не существует, создаем её
                os.makedirs(dir_path, exist_ok=True)
                logger.debug(f"Создана директория для загрузки: {dir_path}")
            elif not os.path.isdir(dir_path):
                # Если путь существует, но это не директория
                logger.error(f"Путь назначения {clean_dest_path} не является директорией")
                return None
        
        # Путь к файлу относительно хранилища
        if clean_dest_path:
            rel_file_path = os.path.join(clean_dest_path, filename).replace("\\", "/")
        else:
            rel_file_path = filename
        
        # Полный путь для сохранения файла
        full_path = os.path.join(device.storage_path, rel_file_path)
        logger.debug(f"Полный путь для сохранения файла: {full_path}")
        
        # Проверяем, существует ли уже файл с таким именем
        if os.path.exists(full_path):
            # Если это директория, а не файл, возвращаем ошибку
            if os.path.isdir(full_path):
                logger.error(f"По указанному пути {rel_file_path} уже существует директория")
                return None
            
            # Если это файл, перезаписываем его
            logger.debug(f"Файл {rel_file_path} уже существует, будет перезаписан")
        
        # Сохраняем файл
        file.save(full_path)
        
        # Небольшая задержка для синхронизации файловой системы
        import time
        time.sleep(0.1)
        
        # Проверяем, что файл действительно сохранился
        if not os.path.exists(full_path):
            logger.error(f"Не удалось сохранить файл {full_path}")
            return None
            
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
            
            # Еще одна маленькая задержка после коммита
            time.sleep(0.1)
            
            logger.info(f"Загружен файл {rel_file_path} для устройства {device.name}")
            return new_file
    except PermissionError:
        logger.error(f"Недостаточно прав для сохранения файла в {clean_dest_path}")
        db.session.rollback()
        return None
    except Exception as e:
        logger.error(f"Ошибка при загрузке файла: {e}")
        # Откатываем транзакцию при ошибке
        db.session.rollback()
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
    # Нормализуем путь с использованием единой функции
    file_path = normalize_path(file_path)
    
    # Логируем для отладки
    logger.debug(f"Получение файла для скачивания: устройство={device.name}, путь='{file_path}'")
    
    # Проверяем существование хранилища
    if not device.storage_path or not os.path.exists(device.storage_path):
        logger.error(f"Хранилище для устройства {device.name} не существует")
        return None, None
    
    # Удаляем начальный слэш для работы с файловой системой
    file_path_fs = file_path.lstrip("/")
    
    if not file_path_fs:
        logger.error(f"Невозможно скачать корневую директорию")
        return None, None
    
    # Полный путь к файлу
    full_path = os.path.join(device.storage_path, file_path_fs)
    logger.debug(f"Полный путь к файлу для скачивания: {full_path}")
    
    # Проверяем существование файла и что это не директория
    if not os.path.exists(full_path):
        logger.error(f"Файл {file_path} не существует")
        return None, None
    
    if not os.path.isfile(full_path):
        logger.error(f"Путь {file_path} указывает на директорию, а не на файл")
        return None, None
    
    # Получаем имя файла из пути
    filename = os.path.basename(file_path)
    
    # Проверяем, что имя файла не пустое
    if not filename:
        filename = "downloaded_file"
        logger.warning(f"Имя файла не определено, используется имя по умолчанию: {filename}")
    
    # Еще одна проверка, что файл доступен для чтения
    try:
        with open(full_path, 'rb') as f:
            # Просто пытаемся прочитать первый байт файла
            f.read(1)
        
        return full_path, filename
    except Exception as e:
        logger.error(f"Не удалось получить доступ к файлу {file_path}: {e}")
        return None, None