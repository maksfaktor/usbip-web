# OrangeUSB - Веб-интерфейс для USB/IP

Веб-интерфейс на Flask для управления USB/IP на Orange Pi Plus 2E (ARMv7) и других платформах.

## Возможности

- Просмотр и управление локальными USB устройствами
- Публикация USB устройств по сети
- Подключение к удаленным USB устройствам через IP
- Создание и эмуляция виртуальных USB устройств
- Управление виртуальными USB портами
- Именование устройств и портов для удобства
- Поиск информации об устройствах по VID:PID
- Ведение журнала операций
- Администрирование учетных записей

## Технологии

- Python 3.7+
- Flask и Flask-Login для веб-интерфейса и аутентификации
- SQLAlchemy для работы с базой данных
- PostgreSQL для хранения данных
- Bootstrap для стилизации интерфейса
- Утилита usbip для управления USB-устройствами

## Требования

### Системные зависимости

- Python 3.7 или выше
- Пакет linux-tools-generic, содержащий утилиту usbip
- PostgreSQL (или другая поддерживаемая SQLAlchemy база данных)

### Python-зависимости

- email-validator
- flask
- flask-login
- flask-sqlalchemy
- flask-wtf
- gunicorn
- psycopg2-binary
- sqlalchemy
- trafilatura
- werkzeug

## Установка

### Установка на Debian/Ubuntu (включая Orange Pi)

```bash
# Установка системных зависимостей
sudo apt update
sudo apt install python3 python3-pip linux-tools-generic hwdata usbip postgresql

# Клонирование репозитория
git clone https://github.com/maksfaktor/usbip-web.git
cd usbip-web

# Установка Python-зависимостей
pip3 install -r requirements.txt

# Настройка базы данных
sudo -u postgres createdb usbipweb
export DATABASE_URL="postgresql://postgres:postgres@localhost/usbipweb"

# Запуск приложения
gunicorn --bind 0.0.0.0:5000 main:app
```

## Использование

После установки и запуска приложения, откройте веб-браузер и перейдите по адресу http://localhost:5000 (или IP-адрес устройства, если подключаетесь удаленно).

По умолчанию создается администратор с логином `admin` и паролем `admin`. Рекомендуется сразу изменить пароль через раздел администрирования.

## Лицензия

Этот проект распространяется под лицензией MIT.