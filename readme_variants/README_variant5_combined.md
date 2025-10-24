# 🍊 Orange USB/IP Web Interface

<div align="center">

**Комплексный веб-интерфейс для управления USB/IP устройствами**

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Platform](https://img.shields.io/badge/platform-Linux-blue.svg)](https://www.linux.org/)
[![Python](https://img.shields.io/badge/python-3.8+-blue.svg)](https://www.python.org/)
[![Flask](https://img.shields.io/badge/flask-2.0+-green.svg)](https://flask.palletsprojects.com/)

[English](#english) | [Русский](#russian)

</div>

---

## <a name="russian"></a>🇷🇺 Русский

### 📋 Описание проекта

Комплексный веб-интерфейс для управления USB/IP устройствами, разработанный для надежной конфигурации, мониторинга и расширенной системной диагностики на Linux платформах. Построено на Flask и современных веб-технологиях, предоставляет интуитивный интерфейс для совместного использования USB устройств в вашей сетевой инфраструктуре.

### ✨ Ключевые возможности

- **🔌 Управление USB устройствами**
  - Публикация локальных USB устройств в сеть через USB/IP протокол
  - Подключение удаленных USB устройств
  - Мониторинг локальных и удаленных USB устройств в реальном времени
  - Подключение/отключение устройств одним кликом
  - Интеллектуальное обнаружение и восстановление от ошибок

- **🖥️ Современный веб-интерфейс**
  - Адаптивный дизайн на базе Bootstrap 5
  - Темная тема, оптимизированная для Orange Pi
  - Обновления в реальном времени без перезагрузки страницы
  - Мобильная версия интерфейса
  - Красивый, функциональный дизайн production-уровня

- **🌍 Интернационализация**
  - Полная поддержка русского и английского языков
  - Легко добавить новые языки
  - Контекстно-зависимые переводы
  - Многоязычный пользовательский интерфейс

- **🔐 Безопасность**
  - Система аутентификации и управления пользователями (Flask-Login)
  - Управление сессиями
  - Хеширование паролей (Werkzeug)
  - Поддержка HTTPS через обратный прокси (ProxyFix)
  - Изоляция прав доступа через systemd

- **🛠️ Расширенные инструменты**
  - Встроенная система диагностики (`doctor.sh`)
  - Веб-терминал с выполнением команд
  - Поддержка виртуальных USB устройств
  - Управление файлами виртуальных устройств
  - Комплексная система логирования

- **📊 Мониторинг и диагностика**
  - История подключения устройств
  - Проверка состояния системы
  - Отслеживание и отчетность об ошибках
  - Совместимость устройств на разных платформах
  - Детальные диагностические инструменты

### 🏗️ Архитектура проекта

#### Основные компоненты

- **Flask Application** (`app.py`)  
  Основное веб-приложение с аутентификацией, маршрутизацией и бизнес-логикой

- **Database Models** (`models.py`)  
  SQLAlchemy модели для пользователей, устройств, логов и терминальных команд

- **USB/IP Utilities** (`usbip_utils.py`)  
  Функции управления USB/IP устройствами - публикация, подключение, мониторинг

- **Virtual Storage** (`virtual_storage_utils.py`)  
  Управление файлами виртуальных USB устройств

- **Translation System** (`translations.py`)  
  Система многоязычной поддержки с функциями перевода

#### Технологический стек

- **Backend**: Flask, Flask-Login, Flask-SQLAlchemy, Werkzeug
- **Frontend**: Bootstrap 5, JavaScript (vanilla JS, без фреймворков)
- **Database**: PostgreSQL / SQLite (с поддержкой обеих СУБД)
- **Icons**: Font Awesome, Feather Icons, кастомные SVG иконки
- **USB/IP**: Linux kernel USB/IP drivers (usbip-host, vhci-hcd)
- **Server**: Gunicorn WSGI server

#### Структура базы данных

- **User**: Пользователи системы (id, username, email, password_hash)
- **Device**: USB устройства (busid, vendor, product, status)
- **DeviceLog**: Логи операций с устройствами (device_id, action, timestamp)
- **TerminalCommand**: Команды для веб-терминала (name, command, description)

### 🚀 Установка

#### Debian/Ubuntu (x86_64 и ARM)

```bash
curl -fsSL https://raw.githubusercontent.com/maksfaktor/usbip-web/main/install_debian.sh -o install_debian.sh
chmod +x install_debian.sh
sudo ./install_debian.sh
```

**Возможности установочного скрипта:**
- Автоматическая проверка системных требований
- Управление зависимостями
- Интеллектуальная очистка предыдущих установок
- Профессиональная настройка сервисов с усилением безопасности
- Надежная обработка ошибок с защитой от таймаутов
- Визуальное отслеживание прогресса
- Полная справочная система (опция `--help`)

#### ARM платформы (Orange Pi, Raspberry Pi)

```bash
curl -fsSL https://raw.githubusercontent.com/maksfaktor/usbip-web/main/install_arm.sh -o install_arm.sh
chmod +x install_arm.sh
sudo ./install_arm.sh
```

### 🎯 Использование

#### Доступ к веб-интерфейсу

После установки откройте браузер и перейдите по адресу:
```
http://ваш-ip:5000
```

Данные для входа по умолчанию:
- **Логин**: admin
- **Пароль**: admin123

> ⚠️ **Важно безопасности**: Измените пароль администратора сразу после первого входа!

#### Публикация USB устройства

1. Откройте раздел **Local USB Devices** (Локальные устройства)
2. Найдите нужное устройство в списке
3. Нажмите зеленую кнопку **"Publish Device"**
4. Устройство станет доступно для удаленного подключения по сети

#### Отмена публикации устройства

1. Найдите опубликованное устройство (помечено зеленым статусом "Published")
2. Нажмите желтую кнопку **"Cancel"**
3. Устройство будет отключено от USB/IP и снова станет локальным

#### Подключение к удаленным устройствам

1. Перейдите на страницу **Remote USB Devices** (Удаленные устройства)
2. Введите IP адрес удаленного сервера, где опубликовано устройство
3. Нажмите кнопку **"Show Devices"** (Показать устройства)
4. Выберите нужное устройство из списка
5. Нажмите кнопку **"Attach Device"** (Подключить)

### 🔧 Диагностика и устранение неполадок

#### Запуск диагностического скрипта

Для проверки состояния системы используйте встроенный диагностический инструмент:

```bash
sudo ./doctor.sh
```

**Скрипт проверяет:**
- Статус USB/IP модулей ядра (usbip-host, vhci-hcd)
- Состояние служб usbipd и orange-usbip
- Список подключенных USB устройств
- Опубликованные устройства
- Логи системы и сервисов
- Конфигурацию сети

### 🗑️ Удаление

#### Интерактивное удаление с проверками

```bash
curl -fsSL https://raw.githubusercontent.com/maksfaktor/usbip-web/main/check_and_remove.sh -o check_and_remove.sh
chmod +x check_and_remove.sh
sudo ./check_and_remove.sh
```

**Возможности скрипта удаления:**
- Обнаружение и удаление служб orange-usbip и usbipd
- Проверка директорий приложения с отчетом о размере
- Завершение запущенных процессов
- Подробный отчет о статусе
- Финальная проверка системы

#### Полное удаление

```bash
sudo ./uninstall.sh
```

### 📁 Структура файлов

```
orange-usbip/
├── app.py                      # Главное Flask приложение
├── main.py                     # Точка входа (импортирует app)
├── models.py                   # Модели базы данных (SQLAlchemy)
├── usbip_utils.py             # Утилиты USB/IP управления
├── virtual_storage_utils.py   # Управление виртуальными устройствами
├── translations.py            # Система переводов (i18n)
├── storage_routes.py          # Маршруты для виртуальных устройств
├── templates/                 # Jinja2 HTML шаблоны
│   ├── base.html             # Базовый шаблон с навигацией
│   ├── login.html            # Страница входа
│   ├── index.html            # Главная страница (Dashboard)
│   ├── local_devices.html    # Локальные USB устройства
│   ├── remote_devices.html   # Удаленные USB устройства
│   ├── terminal.html         # Веб-терминал
│   └── ...                   # Другие страницы
├── static/                    # Статические файлы
│   ├── orange-icon.svg       # Иконка приложения (оранжевый фрукт)
│   └── ...                   # CSS, JS, изображения
├── virtual_storage/          # Хранилище файлов виртуальных устройств
├── scripts/                  # Установочные и утилитарные скрипты
│   ├── install_debian.sh    # Установка для Debian/Ubuntu
│   ├── install_arm.sh       # Установка для ARM платформ
│   ├── uninstall.sh        # Полное удаление
│   ├── doctor.sh           # Диагностика системы
│   └── check_and_remove.sh # Интерактивное удаление
├── requirements-deploy.txt   # Python зависимости
├── pyproject.toml           # Конфигурация проекта
└── usbip_web.db            # SQLite база данных (при использовании SQLite)
```

### 💻 Разработка

#### Установка зависимостей для разработки

```bash
pip install -r requirements-deploy.txt
```

#### Необходимые пакеты Python

- `flask` - Веб-фреймворк
- `flask-login` - Управление аутентификацией
- `flask-sqlalchemy` - ORM для работы с БД
- `flask-wtf` - Формы и CSRF защита
- `werkzeug` - Утилиты (хеширование паролей)
- `gunicorn` - WSGI сервер для production
- `sqlalchemy` - SQL toolkit
- `requests` - HTTP библиотека
- `trafilatura` - Парсинг и обработка текста
- `email-validator` - Валидация email
- `netifaces` - Работа с сетевыми интерфейсами

#### Запуск в режиме разработки

```bash
export DATABASE_URL="sqlite:///usbip_web.db"
export SESSION_SECRET="your-secret-key-here"
python main.py
```

Или с PostgreSQL:
```bash
export DATABASE_URL="postgresql://user:password@localhost/usbip_web"
export SESSION_SECRET="your-secret-key-here"
python main.py
```

#### Запуск в production режиме

```bash
gunicorn --bind 0.0.0.0:5000 --reuse-port --reload main:app
```

### 🔒 Безопасность

- **Аутентификация**: Flask-Login для управления сессиями
- **Пароли**: Хешируются с использованием Werkzeug (без указания метода, используется по умолчанию)
- **HTTPS**: Поддержка через ProxyFix для работы с reverse proxy
- **Изоляция**: Systemd сервис с ограниченными правами
- **CSRF защита**: Flask-WTF для защиты форм
- **Session Secret**: Конфигурируемый секретный ключ через переменные окружения

> ⚠️ **Важно**: Никогда не храните секретные ключи в коде! Используйте переменные окружения.

### 🔧 Системные требования

- **ОС**: Linux с поддержкой USB/IP модулей ядра
- **Python**: 3.8 или выше
- **База данных**: PostgreSQL или SQLite
- **Память**: Минимум 512MB RAM
- **Дисковое пространство**: 100MB свободного места
- **Сеть**: Открытый порт 5000 (или настраиваемый)

### 🐛 Известные проблемы и решения

**Проблема**: Устройство не отображается в списке  
**Решение**: Запустите `sudo ./doctor.sh` для диагностики. Возможно, нужно перезагрузить USB/IP модули.

**Проблема**: Устройство не публикуется  
**Решение**: Убедитесь, что устройство не используется другими программами. Закройте все программы, работающие с этим устройством.

**Проблема**: Ошибка "already bound to usbip-host"  
**Решение**: Устройство уже опубликовано. Используйте кнопку "Cancel" для отмены публикации перед повторной попыткой.

**Проблема**: После установки сервис не запускается  
**Решение**: Проверьте логи: `sudo journalctl -u orange-usbip -n 50`

### 🤝 Разработка и вклад в проект

Вклад в проект приветствуется! Пожалуйста, следуйте этим рекомендациям:

1. Fork репозитория
2. Создайте ветку для вашей функции (`git checkout -b feature/AmazingFeature`)
3. Commit ваших изменений (`git commit -m 'Add some AmazingFeature'`)
4. Push в ветку (`git push origin feature/AmazingFeature`)
5. Откройте Pull Request

**Правила разработки:**
- Следуйте PEP 8 для Python кода
- Добавляйте комментарии для сложной логики
- Обновляйте документацию при изменении функционала
- Тестируйте перед отправкой Pull Request

### 📝 Лицензия

Этот проект распространяется под лицензией MIT License - см. файл LICENSE для деталей.

### 🙏 Благодарности

- Разработано для Orange Pi и других ARM платформ
- Вдохновлено Linux USB/IP проектом
- Благодарность сообществу за вклад и обратную связь
- Особая благодарность контрибьюторам и тестировщикам

### 📞 Поддержка и связь

- **GitHub репозиторий**: https://github.com/maksfaktor/usbip-web
- **Сообщить о проблеме**: https://github.com/maksfaktor/usbip-web/issues
- **Документация**: В процессе разработки
- **Wiki**: https://github.com/maksfaktor/usbip-web/wiki

---

## <a name="english"></a>🌐 English

### 📋 Project Overview

A comprehensive USB/IP device management web interface designed for robust device configuration, monitoring, and advanced system diagnostics across Linux architectures. Built with Flask and modern web technologies, it provides an intuitive interface for sharing USB devices across your network infrastructure.

### ✨ Key Features

- **🔌 USB Device Management**
  - Publish local USB devices to network via USB/IP protocol
  - Attach remote USB devices
  - Real-time monitoring for local and remote USB devices
  - One-click bind/unbind operations
  - Intelligent error detection and recovery mechanisms

- **🖥️ Modern Web Interface**
  - Responsive Bootstrap 5 design
  - Dark theme optimized for Orange Pi
  - Real-time updates without page refresh
  - Mobile-friendly responsive layout
  - Beautiful, functional, production-ready design

- **🌍 Internationalization**
  - Full Russian/English language support
  - Easy to add new languages
  - Context-aware translations
  - Internationalized user interface supporting multiple languages

- **🔐 Security**
  - User authentication system (Flask-Login)
  - Session management
  - Password hashing (Werkzeug)
  - HTTPS support via reverse proxy (ProxyFix)
  - Permission isolation through systemd

- **🛠️ Advanced Tools**
  - Built-in diagnostic system (`doctor.sh`)
  - Web-based terminal with command execution
  - Virtual USB device support
  - Virtual device file management
  - Comprehensive logging system

- **📊 Monitoring & Diagnostics**
  - Device connection history
  - System health checks
  - Error tracking and reporting
  - Cross-platform device compatibility
  - Detailed diagnostic tools

### 🏗️ Architecture

#### Core Components

- **Flask Application** (`app.py`)  
  Main web interface with authentication, routing, and business logic

- **Database Models** (`models.py`)  
  SQLAlchemy models for users, devices, logs, and terminal commands

- **USB/IP Utilities** (`usbip_utils.py`)  
  Core device management functions - publishing, attaching, monitoring

- **Virtual Storage** (`virtual_storage_utils.py`)  
  Virtual USB device file management

- **Translation System** (`translations.py`)  
  Multilingual support system with translation functions

#### Technology Stack

- **Backend**: Flask, Flask-Login, Flask-SQLAlchemy, Werkzeug
- **Frontend**: Bootstrap 5, JavaScript (vanilla JS, no frameworks)
- **Database**: PostgreSQL / SQLite (supports both)
- **Icons**: Font Awesome, Feather Icons, custom SVG icons
- **USB/IP**: Linux kernel USB/IP drivers (usbip-host, vhci-hcd)
- **Server**: Gunicorn WSGI server

#### Database Structure

- **User**: System users (id, username, email, password_hash)
- **Device**: USB devices (busid, vendor, product, status)
- **DeviceLog**: Device operation logs (device_id, action, timestamp)
- **TerminalCommand**: Web terminal commands (name, command, description)

### 🚀 Quick Start

#### Installation on Debian/Ubuntu (x86_64 and ARM)

```bash
curl -fsSL https://raw.githubusercontent.com/maksfaktor/usbip-web/main/install_debian.sh -o install_debian.sh
chmod +x install_debian.sh
sudo ./install_debian.sh
```

**Installation script features:**
- Automatic system requirement validation
- Dependency management
- Intelligent cleanup of previous installations
- Professional-grade service configuration with security hardening
- Robust error handling with timeout protection
- Visual progress tracking
- Complete help system (`--help` option)

#### Installation on ARM (Orange Pi, Raspberry Pi)

```bash
curl -fsSL https://raw.githubusercontent.com/maksfaktor/usbip-web/main/install_arm.sh -o install_arm.sh
chmod +x install_arm.sh
sudo ./install_arm.sh
```

### 🎯 Usage

#### Access the Web Interface

After installation, open your browser and navigate to:
```
http://your-server-ip:5000
```

Default credentials:
- **Username**: admin
- **Password**: admin123

> ⚠️ **Security Notice**: Change the default password immediately after first login!

#### Publishing a USB Device

1. Navigate to **Local USB Devices**
2. Locate your device in the list
3. Click the green **"Publish Device"** button
4. Device is now available on the network

#### Unbinding a Device

1. Find the published device (marked with green "Published" status)
2. Click the yellow **"Cancel"** button
3. Device will be unbound from USB/IP

#### Attaching a Remote Device

1. Go to **Remote USB Devices**
2. Enter the remote server IP address
3. Click **"Show Devices"**
4. Select device and click **"Attach Device"**

### 🔧 Diagnostics & Troubleshooting

#### Run the Diagnostic Script

To check system status:

```bash
sudo ./doctor.sh
```

**The script checks:**
- USB/IP kernel modules status (usbip-host, vhci-hcd)
- Service status (usbipd, orange-usbip)
- Connected USB devices
- Published devices
- System and service logs
- Network configuration

### 🗑️ Uninstallation

#### Interactive Removal

```bash
curl -fsSL https://raw.githubusercontent.com/maksfaktor/usbip-web/main/check_and_remove.sh -o check_and_remove.sh
chmod +x check_and_remove.sh
sudo ./check_and_remove.sh
```

**Removal script features:**
- Detects and removes orange-usbip and usbipd services
- Checks application directories with size reporting
- Terminates running processes
- Detailed status reporting
- Final system verification

#### Complete Removal

```bash
sudo ./uninstall.sh
```

### 📁 File Structure

```
orange-usbip/
├── app.py                      # Main Flask application
├── main.py                     # Entry point (imports app)
├── models.py                   # Database models (SQLAlchemy)
├── usbip_utils.py             # USB/IP management utilities
├── virtual_storage_utils.py   # Virtual device management
├── translations.py            # Translation system (i18n)
├── storage_routes.py          # Virtual device routes
├── templates/                 # Jinja2 HTML templates
│   ├── base.html             # Base template with navigation
│   ├── login.html            # Login page
│   ├── index.html            # Main page (Dashboard)
│   ├── local_devices.html    # Local USB devices
│   ├── remote_devices.html   # Remote USB devices
│   ├── terminal.html         # Web terminal
│   └── ...                   # Other pages
├── static/                    # Static files
│   ├── orange-icon.svg       # Application icon (orange fruit)
│   └── ...                   # CSS, JS, images
├── virtual_storage/          # Virtual device file storage
├── scripts/                  # Installation and utility scripts
│   ├── install_debian.sh    # Debian/Ubuntu installation
│   ├── install_arm.sh       # ARM platform installation
│   ├── uninstall.sh        # Complete removal
│   ├── doctor.sh           # System diagnostics
│   └── check_and_remove.sh # Interactive removal
├── requirements-deploy.txt   # Python dependencies
├── pyproject.toml           # Project configuration
└── usbip_web.db            # SQLite database (when using SQLite)
```

### 💻 Development

#### Install Development Dependencies

```bash
pip install -r requirements-deploy.txt
```

#### Required Python Packages

- `flask` - Web framework
- `flask-login` - Authentication management
- `flask-sqlalchemy` - ORM for database
- `flask-wtf` - Forms and CSRF protection
- `werkzeug` - Utilities (password hashing)
- `gunicorn` - WSGI server for production
- `sqlalchemy` - SQL toolkit
- `requests` - HTTP library
- `trafilatura` - Text parsing and processing
- `email-validator` - Email validation
- `netifaces` - Network interface operations

#### Run in Development Mode

```bash
export DATABASE_URL="sqlite:///usbip_web.db"
export SESSION_SECRET="your-secret-key-here"
python main.py
```

Or with PostgreSQL:
```bash
export DATABASE_URL="postgresql://user:password@localhost/usbip_web"
export SESSION_SECRET="your-secret-key-here"
python main.py
```

#### Run in Production Mode

```bash
gunicorn --bind 0.0.0.0:5000 --reuse-port --reload main:app
```

### 🔒 Security

- **Authentication**: Flask-Login for session management
- **Passwords**: Hashed using Werkzeug (default method)
- **HTTPS**: Support via ProxyFix for reverse proxy
- **Isolation**: Systemd service with limited permissions
- **CSRF Protection**: Flask-WTF for form protection
- **Session Secret**: Configurable secret key via environment variables

> ⚠️ **Important**: Never store secret keys in code! Use environment variables.

### 🔧 System Requirements

- **OS**: Linux with USB/IP kernel modules
- **Python**: 3.8 or higher
- **Database**: PostgreSQL or SQLite
- **Memory**: 512MB RAM minimum
- **Storage**: 100MB free space
- **Network**: Open port 5000 (or configurable)

### 🐛 Known Issues and Solutions

**Issue**: Device not showing in list  
**Solution**: Run `sudo ./doctor.sh` for diagnostics. May need to reload USB/IP modules.

**Issue**: Device won't publish  
**Solution**: Ensure device is not used by other programs. Close all programs using the device.

**Issue**: Error "already bound to usbip-host"  
**Solution**: Device is already published. Use "Cancel" button to unbind before republishing.

**Issue**: Service doesn't start after installation  
**Solution**: Check logs: `sudo journalctl -u orange-usbip -n 50`

### 🤝 Contributing

Contributions are welcome! Please follow these guidelines:

1. Fork the repository
2. Create your feature branch (`git checkout -b feature/AmazingFeature`)
3. Commit your changes (`git commit -m 'Add some AmazingFeature'`)
4. Push to the branch (`git push origin feature/AmazingFeature`)
5. Open a Pull Request

**Development guidelines:**
- Follow PEP 8 for Python code
- Add comments for complex logic
- Update documentation when changing functionality
- Test before submitting Pull Request

### 📝 License

This project is licensed under the MIT License - see the LICENSE file for details.

### 🙏 Acknowledgments

- Built for Orange Pi and other ARM platforms
- Inspired by the Linux USB/IP project
- Thanks to the community for contributions and feedback
- Special thanks to contributors and testers

### 📞 Support

- **GitHub Repository**: https://github.com/maksfaktor/usbip-web
- **Report Issues**: https://github.com/maksfaktor/usbip-web/issues
- **Documentation**: In development
- **Wiki**: https://github.com/maksfaktor/usbip-web/wiki

---

<div align="center">

**Сделано с ❤️ для Orange Pi и Linux сообщества**  
**Made with ❤️ for Orange Pi and Linux community**

[⬆ Наверх / Back to Top](#-orange-usbip-web-interface)

</div>
