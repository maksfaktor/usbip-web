# Virtual FIDO2 Integration Plan
# Orange USB/IP Web Interface - FIDO2 Device Support

**Date:** October 25, 2025  
**Project:** Orange USB/IP Web Interface  
**Integration:** virtual-fido (FIDO2/U2F Virtual USB Device)

---

## 📋 ПОШАГОВЫЙ ПЛАН ИНТЕГРАЦИИ

### Этап 1: Подготовка и установка (Tasks 1-2)
- [x] **Task 1:** Создание документации FIDO2_INTEGRATION.md
- [ ] **Task 2:** Установка Go и компиляция virtual-fido binary
  - Установить Go compiler
  - Клонировать репозиторий virtual-fido
  - Скомпилировать binary
  - Проверить работу командами

### Этап 2: Backend инфраструктура (Tasks 3-5)
- [ ] **Task 3:** Создать Python wrapper для virtual-fido CLI
  - Функции: start_fido_device(), stop_fido_device()
  - Функции: list_fido_credentials(), delete_fido_credential()
  - Функция: get_fido_status()
- [ ] **Task 4:** Создать модели БД для FIDO
  - FidoDevice (settings, status)
  - FidoCredential (metadata)
  - FidoLog (operations log)
- [ ] **Task 5:** Создать fido_routes.py Blueprint
  - Route: /fido_device (главная страница)
  - API: /fido/start, /fido/stop
  - API: /fido/status

### Этап 3: Базовый UI (Tasks 6-7) - ⚠️ TEST CHECKPOINT 1
- [ ] **Task 6:** Создать fido_device.html
  - Control Panel (Start/Stop buttons)
  - Status indicator
  - Basic styling
- [ ] **Task 7:** Добавить пункт меню в base.html
  - 🛑 **ОСТАНОВКА ДЛЯ ТЕСТИРОВАНИЯ**

### Этап 4: Управление Credentials (Tasks 8-9) - ⚠️ TEST CHECKPOINT 2
- [ ] **Task 8:** Реализовать список credentials
  - Backend: парсинг вывода CLI
  - Frontend: таблица с данными
- [ ] **Task 9:** Добавить удаление credentials
  - Modal confirmation
  - Delete API endpoint
  - 🛑 **ОСТАНОВКА ДЛЯ ТЕСТИРОВАНИЯ**

### Этап 5: Безопасность (Tasks 10-11)
- [ ] **Task 10:** Управление passphrase
  - Set passphrase UI
  - Change passphrase
  - Secure storage
- [ ] **Task 11:** Backup/Restore
  - Storage path config
  - Export credentials
  - Import backup

### Этап 6: Мониторинг (Tasks 12-13) - ⚠️ TEST CHECKPOINT 3
- [ ] **Task 12:** Logs viewer
  - FIDO operations log
  - Real-time updates
  - 🛑 **ОСТАНОВКА ДЛЯ ТЕСТИРОВАНИЯ**
- [ ] **Task 13:** Statistics dashboard
  - Credentials count
  - Last activity
  - Protocol info

### Этап 7: Дополнительные функции (Tasks 14-15) - ⚠️ FINAL TEST
- [ ] **Task 14:** Auto-start configuration
  - Systemd service
  - Boot configuration
- [ ] **Task 15:** Test device integration
  - Link to demo.yubico.com
  - Device info display
  - 🛑 **ФИНАЛЬНОЕ ТЕСТИРОВАНИЕ**

### Этап 8: Завершение (Tasks 16-17)
- [ ] **Task 16:** Финальное тестирование
  - Проверка всех функций
  - Обновление документации
- [ ] **Task 17:** Upload на GitHub
  - Синхронизация всех файлов
  - Commit message

---

## 🔍 ИССЛЕДОВАНИЕ ПРОЕКТА virtual-fido

### Обзор проекта

**GitHub:** https://github.com/bulwarkid/virtual-fido  
**Stars:** 1.3k ⭐  
**License:** MIT  
**Language:** Go (19.9%), C (77.1%)  

**Описание:**  
Virtual FIDO - это виртуальное USB-устройство, которое реализует протоколы FIDO2/U2F (как YubiKey) для поддержки двухфакторной аутентификации (2FA) и WebAuthn. Работает через USB/IP и эмулирует настоящий аппаратный токен безопасности.

### Основные возможности

#### 1. **Поддержка платформ**
- ✅ **Windows** - через USB/IP
- ✅ **Linux** - через vhci-hcd драйвер
- ⏳ **macOS** - в разработке

#### 2. **Протоколы**
- **U2F (CTAP1)** - Legacy протокол для 2FA
- **FIDO2 (CTAP2)** - Современный протокол для passwordless аутентификации
- **WebAuthn** - Web стандарт W3C для аутентификации

#### 3. **Хранение данных**
- Encrypted storage с passphrase
- Локальное хранение credentials в файле
- Возможность хранения где угодно (гибкая архитектура)

#### 4. **Механизм одобрения**
- Generic approval mechanism
- По умолчанию - terminal-based (консоль)
- Можно заменить на web-based для нашего проекта

### Как это работает

```
┌─────────────────────────────────────────────────┐
│  Browser/Application (WebAuthn API)            │
└──────────────────┬──────────────────────────────┘
                   │ CTAP2/U2F Protocol
                   ▼
┌─────────────────────────────────────────────────┐
│  Virtual USB Device (USB HID)                   │
│  - Emulates FIDO2 authenticator                 │
│  - Responds to CTAP commands                    │
└──────────────────┬──────────────────────────────┘
                   │ USB/IP Protocol
                   ▼
┌─────────────────────────────────────────────────┐
│  virtual-fido (Go application)                  │
│  - USB/IP server (local TCP)                    │
│  - CTAP protocol implementation                 │
│  - Credential storage & management              │
└─────────────────────────────────────────────────┘
```

**Процесс работы:**
1. virtual-fido создаёт USB/IP сервер на локальном TCP
2. Виртуальное USB-устройство подключается к системе
3. Устройство эмулирует USB/CTAP протоколы
4. Предоставляет FIDO2/U2F сервисы операционной системе
5. Credentials хранятся в зашифрованном файле
6. Одобрения (approvals) выполняются через терминал

### CLI Команды

```bash
# Запуск виртуального FIDO-устройства
go run ./cmd/demo start

# Список сохранённых credentials
go run ./cmd/demo list

# Удаление credential
go run ./cmd/demo delete [credential-id]

# Остановка устройства
go run ./cmd/demo stop

# Помощь и список команд
go run ./cmd/demo --help
```

### Демо и тестирование

**Тестовая страница YubiKey:**  
https://demo.yubico.com/webauthn-technical/registration

**Windows:**
```bash
go run ./cmd/demo start
```

**Linux:**
```bash
# 1. Загрузить драйвер
sudo modprobe vhci-hcd

# 2. Запустить устройство (требует sudo)
sudo go run ./cmd/demo start
```

---

## 🎯 СПИСОК ФУНКЦИЙ ДЛЯ ВЕБ-СТРАНИЦЫ

### 1. Управление устройством

#### Control Panel
- **🟢 Start Device** - запуск виртуального FIDO2-устройства
  - Кнопка с индикатором загрузки
  - Проверка прав sudo/admin
  - Отображение ошибок при запуске
  
- **🔴 Stop Device** - остановка устройства
  - Подтверждение перед остановкой
  - Graceful shutdown
  
- **📊 Device Status** - статус в реальном времени
  - Running (зелёный) / Stopped (красный)
  - Время работы (uptime)
  - PID процесса
  
- **🔄 Auto-start on Boot** - автозапуск
  - Toggle switch
  - Systemd service configuration

#### Device Information
- **Device Type:** FIDO2/U2F Authenticator
- **Protocol Support:** CTAP2, CTAP1/U2F
- **USB/IP Status:** Connected/Disconnected
- **Firmware Version:** (emulated)

### 2. Управление Credentials

#### Credentials Table
**Columns:**
- **Domain/RP ID** - сайт/сервис (example.com)
- **User ID** - идентификатор пользователя
- **Username** - имя пользователя (если есть)
- **Created** - дата создания
- **Last Used** - последнее использование
- **Actions** - кнопки действий

**Features:**
- 🔍 **Search/Filter** - поиск по domain/username
- 📄 **Pagination** - если credentials >50
- ✅ **Bulk Select** - выбор нескольких для удаления
- 🗑️ **Delete** - удаление с подтверждением
- 📋 **Export** - экспорт в JSON/CSV
- 🔄 **Refresh** - обновление списка

#### Credential Details (Modal)
- Full credential information
- Usage statistics
- Raw credential data (для debugging)

### 3. Настройки безопасности

#### Passphrase Management
- **🔐 Set Initial Passphrase**
  - При первом запуске
  - Strength indicator
  - Confirmation field
  
- **🔑 Change Passphrase**
  - Старый пароль
  - Новый пароль
  - Re-encryption credentials
  
- **👁️ Show/Hide Password** - toggle visibility

#### Storage Configuration
- **📁 Storage Path**
  - Путь к файлу credentials
  - Default: `~/.virtual-fido/credentials.enc`
  - Кнопка Browse (file picker)
  
- **💾 Backup Credentials**
  - Export encrypted file
  - Download button
  - Timestamp в имени файла
  
- **📥 Restore from Backup**
  - Upload encrypted file
  - Verify before restore
  - Warning about overwriting

### 4. Мониторинг и логи

#### Statistics Dashboard
```
┌─────────────────────────────────────────┐
│  Total Credentials: 15                  │
│  Active Sessions: 3                     │
│  Successful Auths (24h): 47             │
│  Failed Attempts (24h): 2               │
│  Last Activity: 5 minutes ago           │
│  Protocol Used: CTAP2 (92%) / U2F (8%)  │
└─────────────────────────────────────────┘
```

#### Real-time Activity Log
- **Timestamp** - дата/время операции
- **Event Type** - Registration / Authentication / Delete
- **Domain** - сайт/сервис
- **Status** - Success / Failed / Pending
- **Details** - дополнительная информация

**Filters:**
- By event type
- By domain
- By date range
- By status

#### System Logs
- virtual-fido process output
- USB/IP connection logs
- Error messages
- Debug information

### 5. Тестирование и диагностика

#### Quick Test
- **✅ Test Device** - быстрая проверка
  - Ссылка на demo.yubico.com
  - Встроенный iframe (опционально)
  - Статус проверки
  
- **🔍 Device Diagnostics**
  - Check USB/IP connection
  - Verify vhci-hcd driver (Linux)
  - Test CTAP2 response
  - Check file permissions

#### Help & Documentation
- **📖 User Guide** - как использовать
- **🔧 Troubleshooting** - решение проблем
- **🔗 Useful Links**
  - YubiKey demo
  - WebAuthn.io
  - FIDO Alliance docs

### 6. Дополнительные функции

#### Notifications
- Toast notifications для всех операций
- Success/Error/Warning/Info
- Auto-dismiss или manual close

#### Keyboard Shortcuts
- `Ctrl+S` - Start device
- `Ctrl+X` - Stop device
- `Ctrl+R` - Refresh credentials
- `Ctrl+F` - Focus search

#### Theme Integration
- Bootstrap Dark theme (как в основном проекте)
- Orange accent colors
- Consistent with existing UI

---

## 🛠️ АРХИТЕКТУРА ИНТЕГРАЦИИ

### Структура файлов

```
orange-usbip/
├── app.py                          # Главное приложение
├── fido_utils.py                   # NEW: Python wrapper для virtual-fido
├── fido_routes.py                  # NEW: Blueprint для FIDO функций
├── models.py                       # Обновлено: + FIDO модели
├── templates/
│   ├── base.html                   # Обновлено: + FIDO пункт меню
│   └── fido_device.html            # NEW: Главная страница FIDO
├── static/
│   ├── js/
│   │   └── fido_device.js          # NEW: Frontend логика
│   └── css/
│       └── fido_device.css         # NEW: Стили (если нужны)
├── virtual-fido/                   # NEW: Клон репозитория
│   ├── cmd/demo/                   # Исполняемый файл
│   └── ...
└── fido_data/                      # NEW: Данные FIDO
    ├── credentials.enc             # Зашифрованные credentials
    └── fido.log                    # Логи операций
```

### Database Models

```python
# models.py - дополнение

class FidoDevice(db.Model):
    """Настройки и статус FIDO-устройства"""
    id = db.Column(db.Integer, primary_key=True)
    is_running = db.Column(db.Boolean, default=False)
    pid = db.Column(db.Integer, nullable=True)
    started_at = db.Column(db.DateTime, nullable=True)
    auto_start = db.Column(db.Boolean, default=False)
    storage_path = db.Column(db.String(512), default='fido_data/credentials.enc')
    passphrase_hash = db.Column(db.String(256), nullable=True)
    last_error = db.Column(db.Text, nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

class FidoCredential(db.Model):
    """Метаданные credentials (не сами credentials!)"""
    id = db.Column(db.Integer, primary_key=True)
    credential_id = db.Column(db.String(128), unique=True, nullable=False)
    rp_id = db.Column(db.String(256), nullable=False)  # Domain
    user_id = db.Column(db.String(256), nullable=True)
    username = db.Column(db.String(256), nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    last_used = db.Column(db.DateTime, nullable=True)
    use_count = db.Column(db.Integer, default=0)

class FidoLog(db.Model):
    """Лог операций FIDO"""
    id = db.Column(db.Integer, primary_key=True)
    timestamp = db.Column(db.DateTime, default=datetime.utcnow)
    event_type = db.Column(db.String(64))  # registration, authentication, delete
    rp_id = db.Column(db.String(256), nullable=True)
    status = db.Column(db.String(32))  # success, failed, pending
    details = db.Column(db.Text, nullable=True)
    ip_address = db.Column(db.String(64), nullable=True)
```

### Python Wrapper Functions

```python
# fido_utils.py

import subprocess
import json
import os
from datetime import datetime

FIDO_BINARY = './virtual-fido/cmd/demo/demo'
FIDO_DATA_DIR = 'fido_data'

def start_fido_device(passphrase=None):
    """Запуск виртуального FIDO-устройства"""
    try:
        cmd = ['sudo', FIDO_BINARY, 'start']
        if passphrase:
            # Передача passphrase через stdin или env
            pass
        
        process = subprocess.Popen(
            cmd,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE
        )
        
        return {
            'success': True,
            'pid': process.pid,
            'message': 'FIDO device started successfully'
        }
    except Exception as e:
        return {
            'success': False,
            'error': str(e)
        }

def stop_fido_device():
    """Остановка FIDO-устройства"""
    try:
        cmd = ['sudo', FIDO_BINARY, 'stop']
        result = subprocess.run(cmd, capture_output=True, text=True)
        
        return {
            'success': result.returncode == 0,
            'message': result.stdout or 'Device stopped'
        }
    except Exception as e:
        return {
            'success': False,
            'error': str(e)
        }

def get_fido_status():
    """Получить статус устройства"""
    try:
        # Проверка запущен ли процесс
        cmd = ['pgrep', '-f', 'virtual-fido']
        result = subprocess.run(cmd, capture_output=True, text=True)
        
        is_running = result.returncode == 0
        pid = result.stdout.strip() if is_running else None
        
        return {
            'is_running': is_running,
            'pid': pid
        }
    except Exception as e:
        return {
            'is_running': False,
            'error': str(e)
        }

def list_fido_credentials():
    """Получить список credentials"""
    try:
        cmd = ['sudo', FIDO_BINARY, 'list']
        result = subprocess.run(cmd, capture_output=True, text=True)
        
        if result.returncode != 0:
            return {'success': False, 'error': result.stderr}
        
        # Парсинг вывода CLI
        credentials = parse_credential_list(result.stdout)
        
        return {
            'success': True,
            'credentials': credentials
        }
    except Exception as e:
        return {
            'success': False,
            'error': str(e)
        }

def delete_fido_credential(credential_id):
    """Удалить credential"""
    try:
        cmd = ['sudo', FIDO_BINARY, 'delete', credential_id]
        result = subprocess.run(cmd, capture_output=True, text=True)
        
        return {
            'success': result.returncode == 0,
            'message': result.stdout or 'Credential deleted'
        }
    except Exception as e:
        return {
            'success': False,
            'error': str(e)
        }

def parse_credential_list(output):
    """Парсинг вывода команды list"""
    # Реализация парсинга вывода CLI
    # TODO: адаптировать под реальный формат вывода
    credentials = []
    # ... parsing logic ...
    return credentials
```

### Flask Routes Blueprint

```python
# fido_routes.py

from flask import Blueprint, render_template, request, jsonify, flash
from flask_login import login_required, current_user
from fido_utils import (
    start_fido_device, stop_fido_device, get_fido_status,
    list_fido_credentials, delete_fido_credential
)
from models import FidoDevice, FidoCredential, FidoLog, db

fido_bp = Blueprint('fido', __name__, url_prefix='/fido')

@fido_bp.route('/device')
@login_required
def fido_device_page():
    """Главная страница FIDO-устройства"""
    device = FidoDevice.query.first()
    if not device:
        device = FidoDevice()
        db.session.add(device)
        db.session.commit()
    
    status = get_fido_status()
    credentials = FidoCredential.query.all()
    
    return render_template('fido_device.html',
                         device=device,
                         status=status,
                         credentials=credentials)

@fido_bp.route('/start', methods=['POST'])
@login_required
def start_device():
    """API: Запуск устройства"""
    passphrase = request.json.get('passphrase')
    
    result = start_fido_device(passphrase)
    
    if result['success']:
        device = FidoDevice.query.first()
        device.is_running = True
        device.pid = result['pid']
        device.started_at = datetime.utcnow()
        db.session.commit()
        
        # Логирование
        log = FidoLog(event_type='device_start', status='success')
        db.session.add(log)
        db.session.commit()
    
    return jsonify(result)

@fido_bp.route('/stop', methods=['POST'])
@login_required
def stop_device():
    """API: Остановка устройства"""
    result = stop_fido_device()
    
    if result['success']:
        device = FidoDevice.query.first()
        device.is_running = False
        device.pid = None
        db.session.commit()
        
        log = FidoLog(event_type='device_stop', status='success')
        db.session.add(log)
        db.session.commit()
    
    return jsonify(result)

@fido_bp.route('/status')
@login_required
def device_status():
    """API: Статус устройства"""
    status = get_fido_status()
    return jsonify(status)

@fido_bp.route('/credentials/list')
@login_required
def credentials_list():
    """API: Список credentials"""
    result = list_fido_credentials()
    return jsonify(result)

@fido_bp.route('/credentials/delete/<credential_id>', methods=['POST'])
@login_required
def credentials_delete(credential_id):
    """API: Удаление credential"""
    result = delete_fido_credential(credential_id)
    
    if result['success']:
        # Удаление из БД метаданных
        cred = FidoCredential.query.filter_by(
            credential_id=credential_id
        ).first()
        if cred:
            db.session.delete(cred)
            db.session.commit()
        
        log = FidoLog(
            event_type='credential_delete',
            status='success',
            details=credential_id
        )
        db.session.add(log)
        db.session.commit()
    
    return jsonify(result)
```

### Frontend Template

```html
<!-- templates/fido_device.html -->

{% extends 'base.html' %}

{% block title %}FIDO2 Device - OrangeUSB{% endblock %}

{% block content %}
<div class="container-fluid">
    <h1 class="mb-4">
        <i class="fas fa-key me-2"></i>FIDO2 Security Device
    </h1>

    <!-- Control Panel -->
    <div class="row mb-4">
        <div class="col-md-6">
            <div class="card">
                <div class="card-header">
                    <h5 class="mb-0">
                        <i class="fas fa-toggle-on me-2"></i>Device Control
                    </h5>
                </div>
                <div class="card-body">
                    <!-- Status Indicator -->
                    <div class="mb-3">
                        <h6>Status:</h6>
                        <span id="device-status" class="badge bg-secondary">
                            Checking...
                        </span>
                        <span id="device-uptime" class="ms-2 text-muted"></span>
                    </div>

                    <!-- Control Buttons -->
                    <div class="btn-group" role="group">
                        <button id="start-btn" class="btn btn-success">
                            <i class="fas fa-play me-1"></i>Start Device
                        </button>
                        <button id="stop-btn" class="btn btn-danger">
                            <i class="fas fa-stop me-1"></i>Stop Device
                        </button>
                        <button id="refresh-btn" class="btn btn-secondary">
                            <i class="fas fa-sync me-1"></i>Refresh
                        </button>
                    </div>

                    <!-- Auto-start -->
                    <div class="form-check form-switch mt-3">
                        <input class="form-check-input" type="checkbox" 
                               id="auto-start" {{ 'checked' if device.auto_start }}>
                        <label class="form-check-label" for="auto-start">
                            Auto-start on boot
                        </label>
                    </div>
                </div>
            </div>
        </div>

        <div class="col-md-6">
            <div class="card">
                <div class="card-header">
                    <h5 class="mb-0">
                        <i class="fas fa-chart-bar me-2"></i>Statistics
                    </h5>
                </div>
                <div class="card-body">
                    <div class="row text-center">
                        <div class="col-6">
                            <h3 id="total-credentials">{{ credentials|length }}</h3>
                            <small class="text-muted">Total Credentials</small>
                        </div>
                        <div class="col-6">
                            <h3 id="last-activity">-</h3>
                            <small class="text-muted">Last Activity</small>
                        </div>
                    </div>
                </div>
            </div>
        </div>
    </div>

    <!-- Credentials Table -->
    <div class="card">
        <div class="card-header d-flex justify-content-between align-items-center">
            <h5 class="mb-0">
                <i class="fas fa-list me-2"></i>Stored Credentials
            </h5>
            <button id="refresh-creds-btn" class="btn btn-sm btn-primary">
                <i class="fas fa-sync me-1"></i>Refresh
            </button>
        </div>
        <div class="card-body">
            <table class="table table-dark table-striped">
                <thead>
                    <tr>
                        <th>Domain</th>
                        <th>Username</th>
                        <th>Created</th>
                        <th>Last Used</th>
                        <th>Actions</th>
                    </tr>
                </thead>
                <tbody id="credentials-table">
                    {% for cred in credentials %}
                    <tr data-id="{{ cred.credential_id }}">
                        <td>{{ cred.rp_id }}</td>
                        <td>{{ cred.username or '-' }}</td>
                        <td>{{ cred.created_at.strftime('%Y-%m-%d %H:%M') }}</td>
                        <td>{{ cred.last_used.strftime('%Y-%m-%d %H:%M') if cred.last_used else 'Never' }}</td>
                        <td>
                            <button class="btn btn-sm btn-danger delete-cred" 
                                    data-id="{{ cred.credential_id }}">
                                <i class="fas fa-trash"></i>
                            </button>
                        </td>
                    </tr>
                    {% else %}
                    <tr>
                        <td colspan="5" class="text-center text-muted">
                            No credentials stored
                        </td>
                    </tr>
                    {% endfor %}
                </tbody>
            </table>
        </div>
    </div>

    <!-- Test Section -->
    <div class="card mt-4">
        <div class="card-header">
            <h5 class="mb-0">
                <i class="fas fa-vial me-2"></i>Test Device
            </h5>
        </div>
        <div class="card-body">
            <p>Test your virtual FIDO2 device with the YubiKey demo:</p>
            <a href="https://demo.yubico.com/webauthn-technical/registration" 
               target="_blank" class="btn btn-primary">
                <i class="fas fa-external-link-alt me-1"></i>
                Open YubiKey Demo
            </a>
        </div>
    </div>
</div>

<!-- Delete Confirmation Modal -->
<div class="modal fade" id="deleteModal" tabindex="-1">
    <div class="modal-dialog">
        <div class="modal-content">
            <div class="modal-header">
                <h5 class="modal-title">Confirm Delete</h5>
                <button type="button" class="btn-close" data-bs-dismiss="modal"></button>
            </div>
            <div class="modal-body">
                Are you sure you want to delete this credential?
            </div>
            <div class="modal-footer">
                <button type="button" class="btn btn-secondary" data-bs-dismiss="modal">
                    Cancel
                </button>
                <button type="button" class="btn btn-danger" id="confirm-delete">
                    Delete
                </button>
            </div>
        </div>
    </div>
</div>

<script src="{{ url_for('static', filename='js/fido_device.js') }}"></script>
{% endblock %}
```

---

## ⚠️ ТЕХНИЧЕСКИЕ ОСОБЕННОСТИ И РЕШЕНИЯ

### Проблема 1: Sudo/Admin права

**Проблема:**  
virtual-fido требует повышенных прав для создания USB/IP устройства.

**Решения:**

**Вариант A: Sudoers правило (рекомендуется)**
```bash
# /etc/sudoers.d/virtual-fido
www-data ALL=(ALL) NOPASSWD: /path/to/virtual-fido/demo start
www-data ALL=(ALL) NOPASSWD: /path/to/virtual-fido/demo stop
www-data ALL=(ALL) NOPASSWD: /path/to/virtual-fido/demo list
www-data ALL=(ALL) NOPASSWD: /path/to/virtual-fido/demo delete
```

**Вариант B: Systemd service**
```ini
# /etc/systemd/system/virtual-fido.service
[Unit]
Description=Virtual FIDO2 USB Device
After=network.target

[Service]
Type=simple
User=root
ExecStart=/path/to/virtual-fido/demo start
ExecStop=/path/to/virtual-fido/demo stop
Restart=on-failure

[Install]
WantedBy=multi-user.target
```

### Проблема 2: Passphrase management

**Проблема:**  
Passphrase нужен при каждом запуске для расшифровки credentials.

**Решения:**

**Вариант A: Временное хранение в памяти**
- Хранить в Flask session (encrypted)
- Очистка при logout
- Timeout после N минут без активности

**Вариант B: Системный keyring**
- Использовать Linux keyring
- Более безопасно
- Требует дополнительных библиотек

**Вариант C: Интерактивный ввод**
- Модальное окно при старте
- Пользователь вводит каждый раз
- Максимальная безопасность

### Проблема 3: Go binary компиляция

**Проблема:**  
Нужен скомпилированный Go binary для запуска.

**Решение:**
Добавить в `install_debian.sh`:

```bash
# Установка Go (если не установлен)
if ! command -v go &> /dev/null; then
    echo "Installing Go..."
    wget https://go.dev/dl/go1.21.0.linux-amd64.tar.gz
    sudo tar -C /usr/local -xzf go1.21.0.linux-amd64.tar.gz
    export PATH=$PATH:/usr/local/go/bin
fi

# Клонирование и компиляция virtual-fido
echo "Setting up virtual-fido..."
git clone https://github.com/bulwarkid/virtual-fido.git
cd virtual-fido
go build -o demo ./cmd/demo
cd ..
```

### Проблема 4: USB/IP драйверы

**Проблема:**  
Linux требует vhci-hcd модуль для USB/IP.

**Решение:**
Автоматическая проверка и загрузка:

```bash
# Проверка модуля
if ! lsmod | grep -q vhci_hcd; then
    echo "Loading vhci-hcd module..."
    sudo modprobe vhci-hcd
fi

# Добавление в автозагрузку
echo "vhci-hcd" | sudo tee -a /etc/modules
```

### Проблема 5: Concurrent access

**Проблема:**  
Несколько пользователей web-интерфейса одновременно.

**Решение:**
Mutex locking в Python:

```python
import threading

fido_lock = threading.Lock()

def start_fido_device(passphrase=None):
    with fido_lock:
        # Проверка, что не запущен
        if is_device_running():
            return {'success': False, 'error': 'Already running'}
        
        # Запуск...
        return {'success': True}
```

---

## 📚 ПОЛЕЗНЫЕ РЕСУРСЫ

### Документация FIDO/WebAuthn
- **FIDO Alliance Specs:** https://fidoalliance.org/specifications/
- **W3C WebAuthn:** https://www.w3.org/TR/webauthn/
- **Yubico Developer Guide:** https://developers.yubico.com/FIDO2/

### Тестирование
- **YubiKey Demo:** https://demo.yubico.com/webauthn-technical/registration
- **WebAuthn.io:** https://webauthn.io/
- **WebAuthn Guide:** https://webauthn.guide/

### Проекты и библиотеки
- **virtual-fido:** https://github.com/bulwarkid/virtual-fido
- **python-fido2:** https://github.com/Yubico/python-fido2
- **libfido2:** https://github.com/Yubico/libfido2

### USB/IP
- **Arch Wiki USB/IP:** https://wiki.archlinux.org/title/USB/IP
- **USB/IP Project:** http://usbip.sourceforge.net/

---

## 🔐 БЕЗОПАСНОСТЬ

### Best Practices

1. **Passphrase Storage**
   - НИКОГДА не хранить в plain text
   - Использовать bcrypt/scrypt для хеширования
   - Временное хранение только в памяти

2. **Credential Storage**
   - Файл credentials.enc должен быть encrypted
   - Permissions: 600 (только владелец)
   - Регулярные backups

3. **Access Control**
   - Только авторизованные пользователи
   - Логирование всех операций
   - Rate limiting на критичные операции

4. **Network Security**
   - USB/IP server только на localhost
   - Не expose на внешнюю сеть
   - Firewall rules

5. **Logging**
   - Логировать все start/stop/delete операции
   - НЕ логировать passphrase
   - Ротация логов

### Security Checklist

- [ ] Passphrase хешируется перед сохранением
- [ ] Credentials файл зашифрован
- [ ] File permissions правильные (600)
- [ ] USB/IP только localhost
- [ ] Все операции логируются
- [ ] Rate limiting включен
- [ ] Backup система работает
- [ ] Sudo rules ограничены конкретными командами
- [ ] Session timeout настроен
- [ ] CSRF protection включен

---

## 🎨 UI/UX РЕКОМЕНДАЦИИ

### Design Principles

1. **Consistency** - единый стиль с основным проектом
2. **Clarity** - понятные названия кнопок и действий
3. **Feedback** - визуальный отклик на все действия
4. **Safety** - подтверждения для критичных операций
5. **Accessibility** - keyboard shortcuts, ARIA labels

### Color Scheme
- **Success:** Green (#28a745) - device running, successful operations
- **Danger:** Red (#dc3545) - device stopped, delete actions
- **Warning:** Orange (#ffc107) - warnings, confirmations
- **Info:** Blue (#17a2b8) - information, status
- **Dark:** Bootstrap dark theme base

### Icons (Font Awesome)
- 🔑 `fa-key` - Main FIDO icon
- ▶️ `fa-play` - Start device
- ⏹️ `fa-stop` - Stop device
- 🔄 `fa-sync` - Refresh
- 📋 `fa-list` - Credentials list
- 🗑️ `fa-trash` - Delete
- ⚙️ `fa-cog` - Settings
- 📊 `fa-chart-bar` - Statistics
- 🔐 `fa-lock` - Security/Passphrase
- ✅ `fa-check-circle` - Success
- ❌ `fa-times-circle` - Error

---

## 📝 ПРИМЕЧАНИЯ ДЛЯ РАЗРАБОТКИ

### Фазы тестирования

**Phase 1: Basic Functionality**
- Запуск/остановка устройства
- Отображение статуса
- Проверка на demo.yubico.com

**Phase 2: Credentials Management**
- Список credentials работает
- Удаление работает
- Refresh обновляет данные

**Phase 3: Security**
- Passphrase management
- Backup/Restore
- Logs viewer

**Phase 4: Polish**
- Statistics dashboard
- Auto-start
- Error handling
- Final UI tweaks

### Known Limitations

1. **macOS Support** - пока не поддерживается virtual-fido
2. **Multiple Devices** - только одно устройство одновременно
3. **Passphrase Recovery** - нет механизма восстановления (by design)
4. **Browser Compatibility** - зависит от WebAuthn support

### Future Enhancements

- [ ] Multi-device support
- [ ] Cloud backup integration
- [ ] Mobile app notifications
- [ ] Biometric approval (вместо терминала)
- [ ] Advanced statistics и analytics
- [ ] Export credentials to JSON/CSV
- [ ] Import from other FIDO managers
- [ ] Webhook notifications
- [ ] API для external integrations

---

## ✅ ИТОГОВЫЙ CHECKLIST

### Pre-Development
- [x] Исследование проекта virtual-fido
- [x] Анализ требований
- [x] Проектирование архитектуры
- [x] Создание плана интеграции

### Development Phases
- [ ] Phase 1: Setup & Basic Control (Tasks 1-7)
- [ ] Phase 2: Credentials Management (Tasks 8-9)
- [ ] Phase 3: Security Features (Tasks 10-11)
- [ ] Phase 4: Monitoring (Tasks 12-13)
- [ ] Phase 5: Advanced Features (Tasks 14-15)
- [ ] Phase 6: Final Testing (Tasks 16-17)

### Testing Checkpoints
- [ ] Checkpoint 1: Basic UI works (Task 7)
- [ ] Checkpoint 2: Credentials CRUD works (Task 9)
- [ ] Checkpoint 3: Logs viewer works (Task 12)
- [ ] Final Checkpoint: All features integrated (Task 15)

### Documentation
- [x] Integration plan created
- [x] API documentation written
- [ ] User guide written
- [ ] Troubleshooting guide written

### Deployment
- [ ] Install script updated
- [ ] Systemd service configured
- [ ] Permissions configured
- [ ] GitHub repository updated

---

**Автор плана:** Replit Agent  
**Дата создания:** October 25, 2025  
**Статус:** In Progress  
**Версия:** 1.0

---

## 🚀 НАЧАЛО РАБОТЫ

**Текущий статус:** Task 1 выполнен ✅

**Следующий шаг:** Task 2 - Установка Go и компиляция virtual-fido

**Внешняя ссылка для тестирования:**  
🔗 https://3913cd2f-3667-4efe-8dec-14b05e58754b-00-3v7k0sfl99ynh.riker.replit.dev

**Команда для запуска:** Workflow "Start application" уже запущен

---

*Этот документ будет обновляться по мере выполнения задач.*
