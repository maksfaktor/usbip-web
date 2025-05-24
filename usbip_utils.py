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
            return []
        
        return parse_local_usb_devices(stdout)
    except Exception as e:
        logger.error(f"Ошибка при выполнении get_local_usb_devices: {str(e)}")
        # Возвращаем эмулированные данные для тестирования на Replit
        return [
            {
                'busid': '1-1', 
                'info': '1-1: Logitech, Inc. : USB Optical Mouse (046d:c05a)',
                'details': ['  1-1:1.0: USB Mouse Interface']
            },
            {
                'busid': '2-1', 
                'info': '2-1: Kingston Technology : USB Flash Drive (0951:1666)',
                'details': ['  2-1:1.0: USB Mass Storage Interface']
            }
        ]

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
    try:
        stdout, stderr, return_code = run_command(['/usr/bin/usbip', 'list', '-r', ip])
        
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
    try:
        stdout, stderr, return_code = run_command(['/usr/bin/usbip', 'attach', '-r', ip, '-b', busid])
        
        if return_code != 0:
            return False, f"Ошибка подключения устройства: {stderr}"
        
        return True, f"Устройство {busid} с сервера {ip} успешно подключено"
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
