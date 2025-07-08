#!/bin/bash

echo "=== Fixing Python Dependencies ==="

# Остановим службу
sudo systemctl stop orange-usbip

# Попробуем установить через apt
echo "1. Installing via apt..."
sudo apt update
sudo apt install -y python3-flask python3-flask-login python3-flask-sqlalchemy python3-flask-wtf python3-werkzeug python3-email-validator python3-requests python3-pip python3-gunicorn

# Если что-то не установилось через apt, используем pip с --break-system-packages
echo "2. Installing remaining packages via pip..."
sudo pip3 install --break-system-packages trafilatura netifaces

# Проверим импорт
echo "3. Testing import..."
cd /home/maxx/orange-usbip
python3 -c "
try:
    from app import app
    print('✓ Import successful')
except Exception as e:
    print(f'✗ Import failed: {e}')
    exit(1)
"

if [ $? -eq 0 ]; then
    echo "4. Restarting service..."
    sudo systemctl restart orange-usbip
    sudo systemctl status orange-usbip --no-pager
    echo "✓ Service should be running now"
else
    echo "✗ Import still failing, need manual fix"
fi

echo "=== Complete ==="