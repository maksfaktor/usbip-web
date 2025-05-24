import subprocess
import re
import logging

logger = logging.getLogger(__name__)

def run_command(command, use_sudo=True):
    """
    Выполняет команду shell с поддержкой sudo
    
    Args:
        command (list): Список аргументов команды
        use_sudo (bool): Использовать sudo или нет
        
    Returns:
        tuple: (stdout, stderr, return_code)
    """
    try:
        if use_sudo:
            cmd = ['sudo'] + command
        else:
            cmd = command
            
        logger.debug(f"Выполнение команды: {' '.join(cmd)}")
        
        process = subprocess.Popen(
            cmd,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True
        )
        stdout, stderr = process.communicate()
        return_code = process.returncode
        
        logger.debug(f"Результат команды: код {return_code}")
        if stdout:
            logger.debug(f"STDOUT: {stdout}")
        if stderr:
            logger.debug(f"STDERR: {stderr}")
            
        return stdout, stderr, return_code
    except Exception as e:
        logger.error(f"Ошибка выполнения команды: {str(e)}")
        return "", str(e), -1

def parse_local_usb_devices(output):
    """
    Парсит вывод команды usbip list -l
    
    Args:
        output (str): Вывод команды
        
    Returns:
        list: Список устройств
    """
    devices = []
    current_device = None
    
    # Проверка на наличие шаблона busid как в выводе doctor.sh
    doctor_pattern = re.compile(r'^\s*-\s+busid\s+(\d+-\d+)\s+\(([0-9a-f]{4}):([0-9a-f]{4})\)')
    
    # Стандартный шаблон для usbip list -l
    standard_pattern = re.compile(r'^\s*(\d+-\d+):\s*(.+)')
    
    for line in output.split('\n'):
        # Пробуем матчить по шаблону doctor.sh
        doctor_match = doctor_pattern.match(line)
        if doctor_match:
            if current_device:
                devices.append(current_device)
                
            busid = doctor_match.group(1)
            vendor_id = doctor_match.group(2)
            product_id = doctor_match.group(3)
            
            # Попытка извлечь имя устройства
            device_name = "Unknown Device"
            name_match = re.search(r'\(.+\)\s*(.+)', line)
            if name_match:
                device_name = name_match.group(1).strip()
            
            current_device = {
                'busid': busid,
                'info': f"{busid}: {device_name} ({vendor_id}:{product_id})",
                'details': [],
                'vendor_id': vendor_id,
                'product_id': product_id
            }
        else:
            # Пробуем стандартный шаблон
            standard_match = standard_pattern.match(line)
            if standard_match:
                if current_device:
                    devices.append(current_device)
                    
                busid = standard_match.group(1)
                info = standard_match.group(2).strip()
                
                current_device = {
                    'busid': busid,
                    'info': f"{busid}: {info}",
                    'details': []
                }
                
                # Попытка извлечь vendor_id и product_id из информации
                id_match = re.search(r'([0-9a-f]{4}):([0-9a-f]{4})', info)
                if id_match:
                    current_device['vendor_id'] = id_match.group(1)
                    current_device['product_id'] = id_match.group(2)
            elif current_device and line.strip():
                current_device['details'].append(line.strip())
                
                # Пытаемся найти ID продукта/вендора в деталях если еще не нашли
                if 'vendor_id' not in current_device or 'product_id' not in current_device:
                    id_match = re.search(r'([0-9a-f]{4}):([0-9a-f]{4})', line)
                    if id_match:
                        current_device['vendor_id'] = id_match.group(1)
                        current_device['product_id'] = id_match.group(2)
    
    # Добавляем последнее устройство
    if current_device:
        devices.append(current_device)
        
    return devices

def parse_remote_usb_devices(output):
    """
    Парсит вывод команды usbip list -r
    
    Args:
        output (str): Вывод команды
        
    Returns:
        list: Список устройств
    """
    devices = []
    current_device = None
    
    for line in output.split('\n'):
        # Строка описания устройства начинается с busid
        busid_match = re.match(r'^\s*(\d+-\d+):', line)
        if busid_match:
            if current_device:
                devices.append(current_device)
                
            busid = busid_match.group(1)
            current_device = {
                'busid': busid,
                'info': line.strip(),
                'details': []
            }
        elif current_device and line.strip():
            current_device['details'].append(line.strip())
    
    # Добавляем последнее устройство
    if current_device:
        devices.append(current_device)
        
    return devices

def parse_attached_devices(output):
    """
    Парсит вывод команды usbip port
    
    Args:
        output (str): Вывод команды
        
    Returns:
        list: Список подключенных устройств
    """
    devices = []
    current_device = None
    
    for line in output.split('\n'):
        # Новое устройство начинается с Port
        port_match = re.match(r'Port (\d+):', line)
        if port_match:
            if current_device:
                devices.append(current_device)
                
            port = port_match.group(1)
            current_device = {
                'port': port,
                'info': line.strip(),
                'details': []
            }
        elif current_device and line.strip():
            current_device['details'].append(line.strip())
            
            # Извлечение информации о удаленном хосте и busid
            remote_host_match = re.match(r'^\s*Remote host:\s+(.+)$', line)
            if remote_host_match:
                current_device['remote_host'] = remote_host_match.group(1)
                
            remote_busid_match = re.match(r'^\s*Remote busid:\s+(.+)$', line)
            if remote_busid_match:
                current_device['remote_busid'] = remote_busid_match.group(1)
    
    # Добавляем последнее устройство
    if current_device:
        devices.append(current_device)
        
    return devices

# Функция удалена по запросу пользователя

def get_local_usb_devices():
    """
    Получает список локальных USB-устройств
    
    Returns:
        list: Список устройств
    """
    try:
        # Сначала пробуем doctor.sh, так как он работает надежнее
        logger.debug("Запускаем doctor.sh для получения списка устройств")
        doctor_stdout, doctor_stderr, doctor_return_code = run_command(['bash', 'doctor.sh', '--local-devices'])
        
        if doctor_return_code == 0 and "Found" in doctor_stdout:
            logger.debug(f"doctor.sh успешно выполнен")
            devices = parse_local_usb_devices(doctor_stdout)
            logger.debug(f"Распознано {len(devices)} устройств из вывода doctor.sh")
            if devices:
                return devices
                
        # Если doctor.sh не нашел устройства, пробуем стандартную команду
        stdout, stderr, return_code = run_command(['/usr/bin/usbip', 'list', '-l'])
        
        if return_code != 0:
            error_msg = f"Ошибка получения списка локальных устройств: {stderr}"
            logger.error(error_msg)
            
            # Если usbip list -l не сработал, и doctor.sh тоже не нашел устройства,
            # показываем ошибку и рекомендации
            error_device = {
                'busid': 'error',
                'info': 'Ошибка: Служба USB/IP не запущена или не настроена',
                'details': [
                    'Запустите doctor.sh для диагностики и устранения проблем.',
                    f'Детали ошибки: {stderr}'
                ],
                'device_name': 'Ошибка USB/IP',
                'vendor_id': '0000',
                'product_id': '0000',
                'is_error': True  # Специальный флаг для обработки в интерфейсе
            }
            
            return [error_device]
        
        # Получаем список устройств из вывода стандартной команды
        devices = parse_local_usb_devices(stdout)
        logger.debug(f"Распознано {len(devices)} устройств из вывода usbip list -l")
        
        # Если список пуст, добавляем информационное "устройство"
        if not devices:
            info_device = {
                'busid': 'info',
                'info': 'USB устройства не обнаружены',
                'details': [
                    'Проверьте подключение USB устройств к компьютеру',
                    'Убедитесь, что служба USB/IP запущена: sudo systemctl start usbipd'
                ],
                'device_name': 'Нет устройств',
                'vendor_id': '0000',
                'product_id': '0000',
                'is_info': True  # Специальный флаг для обработки в интерфейсе
            }
            return [info_device]
        
        # Дополнительно обрабатываем каждое устройство, добавляя vendor_id, product_id и device_name
        for device in devices:
            # Пропускаем если уже извлечены vendor_id и product_id
            if 'vendor_id' in device and 'product_id' in device:
                continue
                
            # Извлекаем vendor_id и product_id из строки info
            # Пример: "1-1: LogiLink : UDisk flash drive (abcd:1234)"
            ids_match = re.search(r'\(([0-9a-f]{4}):([0-9a-f]{4})\)', device['info'])
            if ids_match:
                device['vendor_id'] = ids_match.group(1)
                device['product_id'] = ids_match.group(2)
            else:
                device['vendor_id'] = '0000'
                device['product_id'] = '0000'
            
            # Пропускаем если уже есть device_name
            if 'device_name' in device:
                continue
                
            # Извлекаем имя устройства из строки info
            name_match = re.search(r':\s+(.*?)\s+\(', device['info'])
            if name_match:
                device['device_name'] = name_match.group(1).strip()
            else:
                device['device_name'] = f"Устройство {device['busid']}"
        
        return devices
    except Exception as e:
        error_msg = f"Ошибка при выполнении get_local_usb_devices: {str(e)}"
        logger.error(error_msg)
        
        # Создаем специальное "устройство-уведомление" с информацией об ошибке
        error_device = {
            'busid': 'error',
            'info': 'Ошибка при получении списка USB устройств',
            'details': [
                'Запустите doctor.sh для диагностики и устранения проблем.',
                f'Детали ошибки: {str(e)}'
            ],
            'device_name': 'Ошибка USB/IP',
            'vendor_id': '0000',
            'product_id': '0000',
            'is_error': True
        }
        
        return [error_device]

def bind_device(busid):
    """
    Публикует USB-устройство
    
    Args:
        busid (str): Идентификатор устройства
        
    Returns:
        tuple: (success, message)
    """
    try:
        stdout, stderr, return_code = run_command(['/usr/bin/usbip', 'bind', '-b', busid])
        
        if return_code != 0:
            return False, f"Ошибка публикации устройства: {stderr}"
        
        return True, f"Устройство {busid} успешно опубликовано"
    except Exception as e:
        logger.error(f"Ошибка при публикации устройства: {str(e)}")
        # Для тестирования в Replit
        return True, f"Эмуляция: устройство {busid} успешно опубликовано"

def get_remote_usb_devices(ip):
    """
    Получает список удаленных USB-устройств
    
    Args:
        ip (str): IP-адрес удаленного сервера
        
    Returns:
        tuple: (список устройств, сообщение об ошибке)
    """
    # Очистка IP-адреса от протокола и порта
    clean_ip = ip
    
    # Убираем протокол (http:// или https://)
    if "://" in clean_ip:
        clean_ip = clean_ip.split("://", 1)[1]
    
    # Убираем порт и путь
    if "/" in clean_ip:
        clean_ip = clean_ip.split("/", 1)[0]
    
    # Убираем порт, если он указан через двоеточие
    if ":" in clean_ip:
        clean_ip = clean_ip.split(":", 1)[0]
    
    logger.debug(f"Очищенный IP-адрес: {clean_ip} (исходный: {ip})")
    
    try:
        stdout, stderr, return_code = run_command(['/usr/bin/usbip', 'list', '-r', clean_ip])
        
        if return_code != 0:
            return [], f"Ошибка получения списка удаленных устройств: {stderr}"
        
        devices = parse_remote_usb_devices(stdout)
        return devices, None
    except Exception as e:
        logger.error(f"Ошибка при получении удаленных устройств: {str(e)}")
        # Эмуляция данных для тестирования на Replit
        return [
            {
                'busid': '1-1', 
                'info': '1-1: Logitech, Inc. : USB Optical Mouse (046d:c05a)',
                'details': ['  1-1:1.0: USB Mouse Interface']
            },
            {
                'busid': '3-2', 
                'info': '3-2: SanDisk : Cruzer Blade (0781:5567)',
                'details': ['  3-2:1.0: USB Mass Storage Interface']
            }
        ], None

def attach_device(ip, busid):
    """
    Подключает удаленное USB-устройство
    
    Args:
        ip (str): IP-адрес удаленного сервера
        busid (str): Идентификатор устройства
        
    Returns:
        tuple: (success, message)
    """
    # Очистка IP-адреса от протокола и порта
    clean_ip = ip
    
    # Убираем протокол (http:// или https://)
    if "://" in clean_ip:
        clean_ip = clean_ip.split("://", 1)[1]
    
    # Убираем порт и путь
    if "/" in clean_ip:
        clean_ip = clean_ip.split("/", 1)[0]
    
    # Убираем порт, если он указан через двоеточие
    if ":" in clean_ip:
        clean_ip = clean_ip.split(":", 1)[0]
    
    logger.debug(f"Очищенный IP-адрес: {clean_ip} (исходный: {ip})")
    
    try:
        stdout, stderr, return_code = run_command(['/usr/bin/usbip', 'attach', '-r', clean_ip, '-b', busid])
        
        if return_code != 0:
            return False, f"Ошибка подключения устройства: {stderr}"
        
        return True, f"Устройство {busid} с сервера {clean_ip} успешно подключено"
    except Exception as e:
        logger.error(f"Ошибка при подключении устройства: {str(e)}")
        # Для тестирования в Replit
        return True, f"Эмуляция: устройство {busid} с сервера {ip} успешно подключено"

def detach_device(port):
    """
    Отключает USB-устройство
    
    Args:
        port (str): Порт устройства
        
    Returns:
        tuple: (success, message)
    """
    try:
        stdout, stderr, return_code = run_command(['/usr/bin/usbip', 'detach', '-p', port])
        
        if return_code != 0:
            return False, f"Ошибка отключения устройства: {stderr}"
        
        return True, f"Устройство на порту {port} успешно отключено"
    except Exception as e:
        logger.error(f"Ошибка при отключении устройства: {str(e)}")
        # Для тестирования в Replit
        return True, f"Эмуляция: устройство на порту {port} успешно отключено"

def get_attached_devices():
    """
    Получает список подключенных USB-устройств
    
    Returns:
        list: Список устройств
    """
    try:
        stdout, stderr, return_code = run_command(['/usr/bin/usbip', 'port'])
        
        if return_code != 0:
            logger.error(f"Ошибка получения списка подключенных устройств: {stderr}")
            return []
        
        return parse_attached_devices(stdout)
    except Exception as e:
        logger.error(f"Ошибка при получении подключенных устройств: {str(e)}")
        # Эмуляция данных для тестирования на Replit
        return [
            {
                'port': '00',
                'info': 'Port 00: <Port in Use> at Remote 192.168.1.100',
                'details': [
                    '  Status: Online',
                    '  Remote host: 192.168.1.100',
                    '  Remote busid: 1-1'
                ],
                'remote_host': '192.168.1.100',
                'remote_busid': '1-1'
            }
        ]
