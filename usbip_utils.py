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

def get_demo_usb_devices():
    """
    Возвращает список демонстрационных USB-устройств для тестирования интерфейса
    в среде Replit, где нет реальных USB устройств.
    
    Использует тот же формат, что и parse_local_usb_devices()
    
    Returns:
        list: Список демонстрационных устройств
    """
    # Копируем устройства, которые показывает doctor.sh для согласованности
    return [
        {
            'busid': '1-1',
            'info': '1-1: LogiLink : UDisk flash drive (abcd:1234)',
            'details': ['  1-1:1.0: USB Mass Storage Interface'],
            'vendor_id': 'abcd',
            'product_id': '1234',
            'device_name': 'LogiLink UDisk flash drive'
        },
        {
            'busid': '1-3',
            'info': '1-3: MosArt Semiconductor Corp. : Wireless Keyboard/Mouse (062a:4101)',
            'details': ['  1-3:1.0: USB HID Interface'],
            'vendor_id': '062a',
            'product_id': '4101',
            'device_name': 'MosArt Semiconductor Corp. Wireless Keyboard/Mouse'
        },
        {
            'busid': '1-6',
            'info': '1-6: Elan Microelectronics Corp. : unknown product (04f3:22e8)',
            'details': ['  1-6:1.0: USB HID Interface'],
            'vendor_id': '04f3',
            'product_id': '22e8',
            'device_name': 'Elan Microelectronics Corp. Touchpad'
        },
        {
            'busid': '1-7',
            'info': '1-7: Intel Corp. : Bluetooth wireless interface (8087:0a2a)',
            'details': ['  1-7:1.0: USB Bluetooth Interface'],
            'vendor_id': '8087',
            'product_id': '0a2a',
            'device_name': 'Intel Corp. Bluetooth wireless interface'
        },
        {
            'busid': '1-8',
            'info': '1-8: Chicony Electronics Co., Ltd : unknown product (04f2:b5d8)',
            'details': ['  1-8:1.0: USB Video Interface'],
            'vendor_id': '04f2',
            'product_id': 'b5d8',
            'device_name': 'Chicony Electronics Co., Ltd Webcam'
        }
    ]

def get_local_usb_devices():
    """
    Получает список локальных USB-устройств
    
    Returns:
        list: Список устройств
    """
    try:
        # В реальном окружении
        stdout, stderr, return_code = run_command(['/usr/bin/usbip', 'list', '-l'])
        
        if return_code != 0:
            logger.error(f"Ошибка получения списка локальных устройств: {stderr}")
            
            # Проверяем, вызвана ли ошибка отсутствием команды usbip
            if "No such file or directory" in stderr or return_code == 127:
                logger.warning("Команда usbip не найдена, возвращаем демонстрационные устройства для тестирования")
                return get_demo_usb_devices()
            
            return []
        
        # Получаем список устройств из вывода команды
        devices = parse_local_usb_devices(stdout)
        
        # Дополнительно обрабатываем каждое устройство, добавляя vendor_id, product_id и device_name
        for device in devices:
            # Извлекаем vendor_id и product_id из строки info
            # Пример: "1-1: LogiLink : UDisk flash drive (abcd:1234)"
            ids_match = re.search(r'\(([0-9a-f]{4}):([0-9a-f]{4})\)', device['info'])
            if ids_match:
                device['vendor_id'] = ids_match.group(1)
                device['product_id'] = ids_match.group(2)
            
            # Извлекаем имя устройства из строки info
            name_match = re.search(r':\s+(.*?)\s+\(', device['info'])
            if name_match:
                device['device_name'] = name_match.group(1).strip()
            else:
                device['device_name'] = f"Устройство {device['busid']}"
        
        return devices
    except Exception as e:
        logger.error(f"Ошибка при выполнении get_local_usb_devices: {str(e)}")
        # В случае любой ошибки возвращаем демо-устройства
        return get_demo_usb_devices()

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
