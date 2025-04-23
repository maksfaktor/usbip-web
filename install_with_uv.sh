#!/bin/bash
# install_with_uv.sh - Установка USB/IP Web Interface с использованием uv

set -e

echo "=== Установка USB/IP Web Interface ==="
echo "Начало установки: $(date)"

# Проверка root прав
if [ "$(id -u)" -ne 0 ]; then
    echo "Ошибка: этот скрипт должен быть запущен с правами root (sudo)" >&2
    exit 1
fi

# Установка системных зависимостей
echo "[1/5] Установка системных зависимостей..."
apt-get update -q
apt-get install -y python3 python3-pip python3-dev libpq-dev postgresql postgresql-contrib usbip linux-tools-generic git curl

# Установка uv
echo "[2/5] Установка uv..."
curl -sSf https://astral.sh/uv/install.sh | sh
export PATH="$HOME/.cargo/bin:$PATH"

# Клонирование репозитория (если запускаем не из репозитория)
REPO_DIR="usbip-web"
if [ ! -f "app.py" ] && [ ! -d "$REPO_DIR" ]; then
    echo "[3/5] Клонирование репозитория..."
    git clone https://github.com/maksfaktor/usbip-web.git
    cd "$REPO_DIR"
fi

# Установка зависимостей Python с помощью uv
echo "[4/5] Установка зависимостей Python с использованием uv..."
uv pip install -r requirements-deploy.txt

# Настройка базы данных PostgreSQL
echo "[5/5] Настройка базы данных PostgreSQL..."
# Создаем пользователя и базу данных, если они еще не существуют
if ! sudo -u postgres psql -tAc "SELECT 1 FROM pg_roles WHERE rolname='usbip'" | grep -q 1; then
    sudo -u postgres psql -c "CREATE USER usbip WITH PASSWORD 'usbip_password';"
fi

if ! sudo -u postgres psql -lqt | cut -d \| -f 1 | grep -qw usbip_web; then
    sudo -u postgres psql -c "CREATE DATABASE usbip_web OWNER usbip;"
fi

sudo -u postgres psql -c "GRANT ALL PRIVILEGES ON DATABASE usbip_web TO usbip;"

# Настройка переменных окружения
export DATABASE_URL="postgresql://usbip:usbip_password@localhost/usbip_web"
# Сохраняем настройки для последующих запусков
echo 'DATABASE_URL="postgresql://usbip:usbip_password@localhost/usbip_web"' > .env

# Запуск приложения
echo "=== Установка завершена ==="
echo "Вы можете запустить приложение командой:"
echo "gunicorn --bind 0.0.0.0:5000 main:app"
echo ""
echo "Или с помощью systemd-сервиса (рекомендуется):"
echo "1. Создайте файл /etc/systemd/system/usbip-web.service"
echo "2. Используйте следующую конфигурацию:"
echo ""
echo "[Unit]"
echo "Description=USB/IP Web Interface"
echo "After=network.target postgresql.service"
echo ""
echo "[Service]"
echo "User=root"
echo "WorkingDirectory=$(pwd)"
echo "Environment=DATABASE_URL=postgresql://usbip:usbip_password@localhost/usbip_web"
echo "ExecStart=$(which gunicorn) --bind 0.0.0.0:5000 main:app"
echo "Restart=always"
echo ""
echo "[Install]"
echo "WantedBy=multi-user.target"
echo ""
echo "3. Выполните команды:"
echo "   sudo systemctl daemon-reload"
echo "   sudo systemctl enable usbip-web"
echo "   sudo systemctl start usbip-web"
echo ""
echo "После запуска откройте http://YOUR_SERVER_IP:5000 в вашем браузере"