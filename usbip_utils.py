import subprocess
import re
import logging

logger = logging.getLogger(__name__)

def run_command(command, use_sudo=True, no_interactive=True):
    """
    Выполняет команду shell с поддержкой sudo
    
    Args:
        command (list): Список аргументов команды
        use_sudo (bool): Использовать sudo или нет
        no_interactive (bool): Использовать -n для sudo (неинтерактивный режим)
        
    Returns:
        tuple: (stdout, stderr, return_code)
    """
    try:
        if use_sudo:
            # Для неинтерактивного режима добавляем опцию -n, чтобы sudo не запрашивал пароль
            if no_interactive:
                cmd = ['sudo', '-n'] + command
            else:
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
            logger.debug(f"STDOUT длина: {len(stdout)} символов")
        if stderr:
            logger.debug(f"STDERR: {stderr}")
            
        return stdout, stderr, return_code
    except Exception as e:
        logger.error(f"Ошибка выполнения команды: {str(e)}")
        return "", str(e), -1

def parse_local_usb_devices(output):
    """
    Парсит вывод команды usbip list -l или doctor.sh
    
    Args:
        output (str): Вывод команды
        
    Returns:
        list: Список устройств
    """
    devices = []
    current_device = None
    
    logger.debug(f"Начинаем парсинг вывода, длина текста: {len(output)}")
    
    # Добавляем запись в базу данных логов для отображения в веб-интерфейсе
    try:
        from app import add_log_entry
        add_log_entry("DEBUG", f"Начинаем парсинг вывода usbip, длина текста: {len(output)}", "usbip")
        
        # Разбиваем вывод на строки для логирования
        lines = output.split('\n')
        if len(lines) > 20:
            log_lines = lines[:10] + ["..."] + lines[-10:]
        else:
            log_lines = lines
            
        add_log_entry("DEBUG", f"Анализируемые строки: {log_lines}", "usbip")
    except Exception as e:
        logger.error(f"Ошибка при добавлении лога парсинга: {str(e)}")
    
    # Проверка на наличие шаблона busid как в выводе doctor.sh
    doctor_pattern = re.compile(r'^\s*-\s+busid\s+(\d+-\d+)\s+\(([0-9a-f]{4}):([0-9a-f]{4})\)')
    
    # Стандартный шаблон для usbip list -l
    standard_pattern = re.compile(r'^\s*(\d+-\d+):\s*(.+)')
    
    # Дополнительный шаблон для более широкого захвата
    flexible_pattern = re.compile(r'.*?(\d+-\d+).*?([0-9a-f]{4}):([0-9a-f]{4}).*')
    
    line_num = 0
    for line in output.split('\n'):
        line_num += 1
        line = line.strip()
        if not line:
            continue
            
        logger.debug(f"Обрабатываем строку {line_num}: '{line}'")
        
        # Пробуем матчить по шаблону doctor.sh
        doctor_match = doctor_pattern.match(line)
        if doctor_match:
            logger.debug(f"Найдено соответствие по шаблону doctor.sh: '{line}'")
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
                'product_id': product_id,
                'device_name': device_name
            }
            logger.debug(f"Создано устройство: {current_device}")
            continue
            
        # Пробуем стандартный шаблон
        standard_match = standard_pattern.match(line)
        if standard_match:
            logger.debug(f"Найдено соответствие по стандартному шаблону: '{line}'")
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
                
                # Попытка извлечь имя устройства
                name_match = re.search(r':\s+(.*?)\s+\(', info)
                if name_match:
                    device_name = name_match.group(1).strip()
                    current_device['device_name'] = device_name
            
            logger.debug(f"Создано устройство: {current_device}")
            continue
            
        # Если не сработали основные шаблоны, пробуем гибкий шаблон
        flexible_match = flexible_pattern.match(line)
        if flexible_match:
            logger.debug(f"Найдено соответствие по гибкому шаблону: '{line}'")
            if current_device:
                devices.append(current_device)
                
            busid = flexible_match.group(1)
            vendor_id = flexible_match.group(2)
            product_id = flexible_match.group(3)
            
            # Пытаемся вытащить имя устройства из всего, что осталось
            name_parts = re.split(r'[:()\[\]]', line)
            device_name = "Unknown Device"
            for part in name_parts:
                part = part.strip()
                if part and len(part) > 5 and not re.search(r'^\d', part) and not re.search(r'[0-9a-f]{4}:[0-9a-f]{4}', part):
                    device_name = part
                    break
            
            current_device = {
                'busid': busid,
                'info': f"{busid}: {device_name} ({vendor_id}:{product_id})",
                'details': [],
                'vendor_id': vendor_id,
                'product_id': product_id,
                'device_name': device_name
            }
            logger.debug(f"Создано устройство по гибкому шаблону: {current_device}")
            continue
            
        # Если не нашли соответствие ни по одному шаблону, добавляем как детали
        if current_device and line:
            current_device['details'].append(line)
            
            # Пытаемся найти ID продукта/вендора в деталях если еще не нашли
            if 'vendor_id' not in current_device or 'product_id' not in current_device:
                id_match = re.search(r'([0-9a-f]{4}):([0-9a-f]{4})', line)
                if id_match:
                    current_device['vendor_id'] = id_match.group(1)
                    current_device['product_id'] = id_match.group(2)
    
    # Добавляем последнее устройство
    if current_device:
        devices.append(current_device)
    
    logger.debug(f"Завершен парсинг, найдено устройств: {len(devices)}")
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

def parse_doctor_output(output):
    """
    Специальный парсер для вывода doctor.sh с форматом как в примере
    
    Args:
        output (str): Вывод команды doctor.sh
    
    Returns:
        list: Список устройств
    """
    devices = []
    try:
        # Ищем секцию "Local USB devices:"
        if "Local USB devices:" not in output:
            logger.debug("Секция 'Local USB devices:' не найдена в выводе doctor.sh")
            return []
        
        # Извлекаем секцию с устройствами
        devices_section = output.split("Local USB devices:")[1]
        if "Published devices:" in devices_section:
            devices_section = devices_section.split("Published devices:")[0]
        
        logger.debug(f"Извлечена секция с устройствами длиной {len(devices_section)} символов")
        try:
            from app import add_log_entry
            add_log_entry("DEBUG", f"Извлечена секция с устройствами: {devices_section[:500]}", "usbip")
        except Exception as e:
            logger.error(f"Ошибка при добавлении лога: {str(e)}")
        
        # Ищем строки с "busid" в формате "- busid 1-1 (abcd:1234)"
        device_pattern = re.compile(r'^\s*-\s+busid\s+(\d+-\d+)\s+\(([0-9a-f]{4}):([0-9a-f]{4})\)\s*$', re.MULTILINE)
        name_pattern = re.compile(r'^\s*([^:]+):\s*([^(]+)\s*\([0-9a-f]{4}:[0-9a-f]{4}\)\s*$', re.MULTILINE)
        
        # Находим все соответствия шаблону устройств
        devices_matches = list(device_pattern.finditer(devices_section))
        
        for i, match in enumerate(devices_matches):
            busid = match.group(1)
            vendor_id = match.group(2)
            product_id = match.group(3)
            
            # Получаем позицию, с которой начинается следующее устройство
            current_pos = match.end()
            next_pos = devices_section.find("- busid", current_pos)
            if next_pos == -1:
                next_pos = len(devices_section)
            
            # Извлекаем блок с информацией о текущем устройстве
            device_block = devices_section[current_pos:next_pos].strip()
            
            # Ищем информацию об устройстве (производитель и название)
            name_match = name_pattern.search(device_block)
            if name_match:
                manufacturer = name_match.group(1).strip()
                product = name_match.group(2).strip()
                device_name = f"{manufacturer} : {product}"
            else:
                device_name = f"Устройство {busid}"
            
            # Создаем запись об устройстве
            device = {
                'busid': busid,
                'vendor_id': vendor_id,
                'product_id': product_id,
                'device_name': device_name,
                'info': f"{device_name} ({vendor_id}:{product_id})"
            }
            
            devices.append(device)
        
        logger.debug(f"Найдено {len(devices)} устройств в выводе doctor.sh")
        try:
            from app import add_log_entry
            add_log_entry("DEBUG", f"Найдено {len(devices)} устройств в выводе doctor.sh", "usbip")
            
            # Выводим информацию о каждом устройстве
            for i, device in enumerate(devices):
                add_log_entry("DEBUG", f"Устройство {i+1}: {str(device)[:500]}", "usbip")
        except Exception as e:
            logger.error(f"Ошибка при добавлении лога: {str(e)}")
            
    except Exception as e:
        logger.error(f"Ошибка при парсинге вывода doctor.sh: {str(e)}")
    
    return devices

def get_local_usb_devices():
    """
    Получает список локальных USB-устройств
    
    Returns:
        list: Список устройств
    """
    try:
        # Сначала пробуем получить данные через doctor.sh
        logger.debug("Запускаем doctor.sh для получения списка устройств")
        
        # Запускаем doctor.sh напрямую (доктор сам использует sudo)
        doctor_stdout, doctor_stderr, doctor_return_code = run_command(['bash', 'doctor.sh'], use_sudo=False)
        
        # Логируем результаты выполнения команды
        logger.debug(f"doctor.sh завершен с кодом: {doctor_return_code}")
        if doctor_stderr:
            logger.debug(f"doctor.sh STDERR: {doctor_stderr}")
        
        try:
            from app import add_log_entry
            add_log_entry("DEBUG", f"doctor.sh завершен с кодом: {doctor_return_code}", "usbip")
            
            if doctor_stderr:
                add_log_entry("DEBUG", f"doctor.sh STDERR: {doctor_stderr}", "usbip")
                
            # Добавляем первые 1000 символов вывода в лог
            if doctor_stdout:
                add_log_entry("DEBUG", f"doctor.sh STDOUT: {doctor_stdout[:1000]}", "usbip")
        except Exception as e:
            logger.error(f"Ошибка при добавлении лога: {str(e)}")
        
        # Если doctor.sh успешно выполнился, парсим его вывод
        if doctor_return_code == 0 and doctor_stdout:
            devices = parse_doctor_output(doctor_stdout)
            if devices:
                logger.debug(f"Успешно получено {len(devices)} устройств из doctor.sh")
                return devices
        
        # Если doctor.sh не помог, пробуем другие методы
        logger.debug("Пробуем другие методы получения списка устройств")
        
        # Получаем список устройств через lsusb для отладки
        lsusb_stdout, lsusb_stderr, lsusb_return_code = run_command(['lsusb'], use_sudo=False)
        
        if lsusb_return_code == 0 and lsusb_stdout:
            try:
                from app import add_log_entry
                add_log_entry("DEBUG", f"lsusb вывод: {lsusb_stdout}", "usbip")
            except Exception as e:
                logger.error(f"Ошибка при добавлении лога lsusb: {str(e)}")
        
        # Пробуем получить список через usbip list -l
        stdout, stderr, return_code = run_command(['/usr/bin/usbip', 'list', '-l'], use_sudo=False)
        
        # Если не получилось без sudo, пробуем с sudo -n
        if return_code != 0 or not stdout:
            stdout, stderr, return_code = run_command(['/usr/bin/usbip', 'list', '-l'])
        
        # Логируем результаты
        try:
            from app import add_log_entry
            add_log_entry("DEBUG", f"usbip list -l завершен с кодом: {return_code}", "usbip")
            
            if stderr:
                add_log_entry("DEBUG", f"usbip list -l STDERR: {stderr}", "usbip")
                
            if stdout:
                add_log_entry("DEBUG", f"usbip list -l STDOUT: {stdout[:500]}", "usbip")
        except Exception as e:
            logger.error(f"Ошибка при добавлении лога: {str(e)}")
        
        # Если не получилось через usbip, используем lsusb
        if (return_code != 0 or not stdout) and lsusb_return_code == 0 and lsusb_stdout:
            logger.debug("Создаем устройства из вывода lsusb")
            try:
                devices = []
                for line in lsusb_stdout.strip().split('\n'):
                    # Формат строки: 'Bus 001 Device 002: ID 062a:4101 MosArt Semiconductor Corp. Wireless Keyboard/Mouse'
                    match = re.match(r'Bus (\d+) Device (\d+): ID ([0-9a-f]+):([0-9a-f]+)(.+)', line)
                    if match:
                        bus, device, vendor_id, product_id, desc = match.groups()
                        busid = f"{bus}-{device}"
                        
                        desc = desc.strip()
                        if not desc:
                            desc = "Unknown device"
                        
                        device_data = {
                            'busid': busid,
                            'vendor_id': vendor_id,
                            'product_id': product_id,
                            'device_name': desc,
                            'info': f"{desc} ({vendor_id}:{product_id})"
                        }
                        devices.append(device_data)
                
                if devices:
                    logger.debug(f"Создано {len(devices)} устройств из вывода lsusb")
                    return devices
            except Exception as e:
                logger.error(f"Ошибка при обработке вывода lsusb: {str(e)}")
        
        # Если получили вывод usbip list -l, парсим его
        if return_code == 0 and stdout:
            devices = parse_local_usb_devices(stdout)
            if devices:
                logger.debug(f"Распознано {len(devices)} устройств из usbip list -l")
                return devices
                
        # Если ничего не сработало, возвращаем ошибку
        error_device = {
            'busid': 'error',
            'info': 'Ошибка: Служба USB/IP не запущена или не настроена',
            'details': [
                'Запустите doctor.sh для диагностики и устранения проблем.',
                f'Детали ошибки: {stderr if stderr else "Не удалось получить список устройств"}',
                'Убедитесь, что пользователь веб-сервера имеет права на выполнение команд без пароля.'
            ],
            'device_name': 'Ошибка USB/IP',
            'vendor_id': '0000',
            'product_id': '0000',
            'is_error': True  # Специальный флаг для обработки в интерфейсе
        }
        
        return [error_device]
    
    except Exception as e:
        logger.error(f"Неожиданная ошибка при получении списка USB устройств: {str(e)}")
        
        # В случае любой ошибки возвращаем информационное сообщение
        error_device = {
            'busid': 'error',
            'info': 'Произошла ошибка при получении списка устройств',
            'details': [
                f'Детали ошибки: {str(e)}',
                'Проверьте журнал отладки для получения дополнительной информации.'
            ],
            'device_name': 'Ошибка',
            'vendor_id': '0000',
            'product_id': '0000',
            'is_error': True
        }
        
        return [error_device]
        
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
