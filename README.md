# USB/IP Web Interface

Веб-интерфейс на Flask для управления USB/IP на Orange Pi Plus 2E (ARMv7) и других платформах.

## Описание

Этот проект представляет собой веб-интерфейс для управления USB/IP - технологии, позволяющей использовать USB-устройства по сети. Интерфейс позволяет:

- Просматривать локальные USB устройства
- Публиковать USB устройства через USB/IP
- Подключаться к удаленным серверам для доступа к их USB устройствам
- Отключать устройства при необходимости
- Создавать и управлять виртуальными USB устройствами и портами
- Настраивать алиасы для устройств и имена для портов

## Технологии

- Python 3
- Flask
- SQLAlchemy
- PostgreSQL
- USB/IP (Linux)
- Bootstrap 5

## Требования

- Linux с установленной утилитой USB/IP
- Python 3.7+
- PostgreSQL

### Установка USB/IP в Linux

На большинстве дистрибутивов Linux утилиту USB/IP можно установить следующим образом:

#### Ubuntu/Debian:
```
sudo apt update
sudo apt install linux-tools-generic
```

#### Fedora:
```
sudo dnf install kernel-modules-extra
sudo dnf install usbip
```

#### Arch Linux:
```
sudo pacman -S usbip
```

### Настройка PostgreSQL

Установите PostgreSQL и создайте базу данных:

```
# Установка PostgreSQL
sudo apt install postgresql postgresql-contrib

# Запуск и включение службы PostgreSQL
sudo systemctl start postgresql
sudo systemctl enable postgresql

# Создание пользователя и базы данных
sudo -u postgres psql -c "CREATE USER usbip_user WITH PASSWORD 'your_password';"
sudo -u postgres psql -c "CREATE DATABASE usbip_db OWNER usbip_user;"
sudo -u postgres psql -c "GRANT ALL PRIVILEGES ON DATABASE usbip_db TO usbip_user;"
```

## Установка

1. Клонируйте репозиторий:
   ```
   git clone https://github.com/maksfaktor/usbip-web.git
   cd usbip-web
   ```

2. Установите зависимости:

   ### Метод 1: Установка через скрипт (рекомендуется)
   Вы можете использовать включенный скрипт, который автоматически создаст виртуальное окружение и установит зависимости:
   ```
   # Сделайте скрипт исполняемым
   chmod +x install_python.sh
   
   # Запустите скрипт
   ./install_python.sh
   ```

   ### Метод 2: Ручная установка
   Если вы предпочитаете ручную установку, выполните следующие шаги:
   ```
   # Создание виртуального окружения
   python3 -m venv venv
   
   # Активация виртуального окружения
   source venv/bin/activate
   
   # Установка зависимостей
   pip install -r requirements-deploy.txt
   ```

3. Активация виртуального окружения (если оно еще не активировано):
   ```
   source venv/bin/activate
   ```

4. Настройте переменные окружения:
   ```
   export DATABASE_URL=postgresql://user:password@localhost/usbip_db
   ```

5. Запустите приложение:
   ```
   gunicorn --bind 0.0.0.0:5000 main:app
   ```

> **Примечание**: В Ubuntu 24.04 и других современных дистрибутивах рекомендуется использовать виртуальное окружение для установки пакетов Python (согласно PEP 668).

## Использование

После запуска приложения откройте браузер и перейдите по адресу http://localhost:5000/

По умолчанию создается пользователь с логином `admin` и паролем `password`.
**Важно**: После первого входа в систему обязательно смените пароль администратора!

## Кросс-платформенная совместимость

Приложение разработано для работы на различных процессорных архитектурах:
- ARM (Orange Pi, Raspberry Pi и др.)
- x86
- x86-64

### Настройка на Orange Pi Plus 2E (ARMv7)

Для работы приложения на Orange Pi, выполните следующие шаги:

1. Установите Armbian или другой совместимый дистрибутив Linux.
2. Установите USB/IP:
   ```
   sudo apt update
   sudo apt install linux-tools-generic
   ```
3. Убедитесь, что модуль USB/IP загружен:
   ```
   sudo modprobe usbip-core
   sudo modprobe usbip-host
   sudo modprobe vhci-hcd
   ```
4. Добавьте модули в автозагрузку:
   ```
   echo "usbip-core" | sudo tee -a /etc/modules
   echo "usbip-host" | sudo tee -a /etc/modules
   echo "vhci-hcd" | sudo tee -a /etc/modules
   ```
5. Запустите usbip демон:
   ```
   sudo systemctl enable usbipd
   sudo systemctl start usbipd
   ```

После этого выполните обычную процедуру установки приложения, как указано в разделе "Установка".

## Безопасность

Все команды USB/IP выполняются с привилегиями root через sudo. 
Рекомендуется настроить sudoers для выполнения специфичных команд usbip без пароля.

### Настройка Sudo для USB/IP

Чтобы избежать постоянного ввода пароля при выполнении команд USB/IP, настройте файл sudoers:

```
# Откройте файл sudoers для редактирования
sudo visudo -f /etc/sudoers.d/usbip

# Добавьте следующие строки, заменив YOUR_USERNAME на ваше имя пользователя
YOUR_USERNAME ALL=(ALL) NOPASSWD: /usr/sbin/usbip
YOUR_USERNAME ALL=(ALL) NOPASSWD: /usr/lib/linux-tools/*/usbip

# Сохраните файл и выйдите (в vi: нажмите ESC, затем :wq и Enter)
```

После этого вы сможете выполнять команды usbip с sudo без запроса пароля.

## Лицензия

MIT