# 🍊 Orange USB/IP Web Interface

<div align="center">

**Modern web-based management interface for USB/IP devices**

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Platform](https://img.shields.io/badge/platform-Linux-blue.svg)](https://www.linux.org/)
[![Python](https://img.shields.io/badge/python-3.8+-blue.svg)](https://www.python.org/)
[![Flask](https://img.shields.io/badge/flask-2.0+-green.svg)](https://flask.palletsprojects.com/)

[English](#english) | [Русский](#russian)

</div>

---

## <a name="english"></a>🌐 English

### Overview

Orange USB/IP Web Interface is a comprehensive solution for managing USB devices over IP networks. Built with Flask and modern web technologies, it provides an intuitive interface for sharing USB devices across your network infrastructure.

### ✨ Key Features

- **🔌 Device Management**
  - Publish local USB devices to network
  - Attach remote USB devices
  - Real-time device status monitoring
  - One-click bind/unbind operations

- **🖥️ Modern Web Interface**
  - Responsive Bootstrap 5 design
  - Dark theme optimized for Orange Pi
  - Real-time updates without page refresh
  - Mobile-friendly responsive layout

- **🌍 Internationalization**
  - Full Russian/English language support
  - Easy to add new languages
  - Context-aware translations

- **🔐 Security**
  - User authentication system
  - Session management
  - Password hashing (Werkzeug)
  - HTTPS support via reverse proxy

- **🛠️ Advanced Tools**
  - Built-in diagnostic system (`doctor.sh`)
  - Web-based terminal
  - Virtual USB device support
  - Comprehensive logging

- **📊 Monitoring**
  - Device connection history
  - System health checks
  - Error tracking and reporting

### 🚀 Quick Start

#### Installation on Debian/Ubuntu

```bash
curl -fsSL https://raw.githubusercontent.com/maksfaktor/usbip-web/main/install_debian.sh -o install_debian.sh
chmod +x install_debian.sh
sudo ./install_debian.sh
```

#### Installation on ARM (Orange Pi, Raspberry Pi)

```bash
curl -fsSL https://raw.githubusercontent.com/maksfaktor/usbip-web/main/install_arm.sh -o install_arm.sh
chmod +x install_arm.sh
sudo ./install_arm.sh
```

#### Access the Interface

After installation, open your browser and navigate to:
```
http://your-server-ip:5000
```

Default credentials:
- Username: `admin`
- Password: `admin123`

> ⚠️ **Security Notice**: Change the default password immediately after first login!

### 📖 Documentation

#### Publishing a USB Device

1. Navigate to **Local USB Devices**
2. Locate your device in the list
3. Click **Publish Device** button
4. Device is now available on the network

#### Attaching a Remote Device

1. Go to **Remote USB Devices**
2. Enter the remote server IP address
3. Click **Show Devices**
4. Select device and click **Attach**

#### Unbinding a Device

1. Find the published device (marked with green status)
2. Click the yellow **Cancel** button
3. Device will be unbound from USB/IP

### 🏗️ Architecture

```
orange-usbip/
├── app.py                    # Main Flask application
├── models.py                 # Database models (SQLAlchemy)
├── usbip_utils.py           # USB/IP core utilities
├── virtual_storage_utils.py # Virtual device management
├── translations.py          # i18n support
├── templates/               # Jinja2 templates
│   ├── base.html
│   ├── login.html
│   ├── index.html
│   └── ...
├── static/                  # Static assets
│   ├── orange-icon.svg
│   └── ...
└── scripts/
    ├── install_debian.sh
    ├── doctor.sh
    └── uninstall.sh
```

### 🔧 System Requirements

- **OS**: Linux with USB/IP kernel modules
- **Python**: 3.8 or higher
- **Database**: PostgreSQL or SQLite
- **Memory**: 512MB RAM minimum
- **Storage**: 100MB free space

### 🐛 Troubleshooting

Run the diagnostic tool to check system status:

```bash
sudo ./doctor.sh
```

The script checks:
- USB/IP kernel modules status
- Service status (usbipd, orange-usbip)
- Connected USB devices
- Published devices
- System logs

### 🗑️ Uninstallation

#### Interactive Removal

```bash
curl -fsSL https://raw.githubusercontent.com/maksfaktor/usbip-web/main/check_and_remove.sh -o check_and_remove.sh
chmod +x check_and_remove.sh
sudo ./check_and_remove.sh
```

#### Complete Removal

```bash
sudo ./uninstall.sh
```

### 🤝 Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

### 📝 License

This project is licensed under the MIT License - see the LICENSE file for details.

### 🙏 Acknowledgments

- Built for Orange Pi and ARM platforms
- Inspired by the Linux USB/IP project
- Community contributions and feedback

---

## <a name="russian"></a>🇷🇺 Русский

### Описание

Orange USB/IP Web Interface - это комплексное решение для управления USB устройствами по IP сети. Построено на Flask и современных веб-технологиях, предоставляет интуитивный интерфейс для совместного использования USB устройств в вашей сетевой инфраструктуре.

### ✨ Основные возможности

- **🔌 Управление устройствами**
  - Публикация локальных USB устройств в сеть
  - Подключение удаленных USB устройств
  - Мониторинг статуса устройств в реальном времени
  - Подключение/отключение одним кликом

- **🖥️ Современный веб-интерфейс**
  - Адаптивный дизайн на Bootstrap 5
  - Темная тема, оптимизированная для Orange Pi
  - Обновления в реальном времени без перезагрузки страницы
  - Мобильная версия интерфейса

- **🌍 Интернационализация**
  - Полная поддержка русского и английского языков
  - Легко добавить новые языки
  - Контекстно-зависимые переводы

- **🔐 Безопасность**
  - Система аутентификации пользователей
  - Управление сессиями
  - Хеширование паролей (Werkzeug)
  - Поддержка HTTPS через обратный прокси

### 🚀 Быстрый старт

Смотрите [раздел на английском](#quick-start) для инструкций по установке.

### 📞 Поддержка

- **GitHub**: https://github.com/maksfaktor/usbip-web
- **Issues**: https://github.com/maksfaktor/usbip-web/issues

---

<div align="center">

**Сделано с ❤️ для Orange Pi и Linux сообщества**

[⬆ Наверх](#-orange-usbip-web-interface)

</div>
