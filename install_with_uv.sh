#!/bin/bash
# install_with_uv.sh - Установка USB/IP Web Interface с использованием uv и SQLite

set -e

echo "=== Установка USB/IP Web Interface ==="
echo "Начало установки: $(date)"

# Проверка root прав
if [ "$(id -u)" -ne 0 ]; then
    echo "Ошибка: этот скрипт должен быть запущен с правами root (sudo)" >&2
    exit 1
fi

# Установка системных зависимостей
echo "[1/4] Установка системных зависимостей..."
apt-get update -q
apt-get install -y python3 python3-pip python3-dev usbip linux-tools-generic git curl

# Установка uv
echo "[2/4] Установка uv..."
curl -sSf https://astral.sh/uv/install.sh | sh
export PATH="$HOME/.cargo/bin:$PATH"

# Клонирование репозитория (если запускаем не из репозитория)
REPO_DIR="usbip-web"
if [ ! -f "app.py" ] && [ ! -d "$REPO_DIR" ]; then
    echo "[3/4] Клонирование репозитория..."
    git clone https://github.com/maksfaktor/usbip-web.git
    cd "$REPO_DIR"
fi

# Установка зависимостей Python с помощью uv
echo "[4/4] Установка зависимостей Python с использованием uv..."
uv pip install -r requirements-deploy.txt

# SQLite будет создана автоматически при первом запуске приложения
echo "База данных SQLite будет создана автоматически при первом запуске приложения."

# Очистка переменных окружения, чтобы использовать SQLite по умолчанию
if [ -f ".env" ]; then
    rm .env
fi

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
echo "After=network.target"
echo ""
echo "[Service]"
echo "User=root"
echo "WorkingDirectory=$(pwd)"
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