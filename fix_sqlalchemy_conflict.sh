#!/bin/bash

echo "=== Fixing SQLAlchemy Version Conflict ==="

# Остановим службу
sudo systemctl stop orange-usbip

echo "1. Removing user-installed SQLAlchemy packages..."
pip3 uninstall -y sqlalchemy flask-sqlalchemy 2>/dev/null || true
rm -rf /home/maxx/.local/lib/python3.12/site-packages/sqlalchemy*
rm -rf /home/maxx/.local/lib/python3.12/site-packages/SQLAlchemy*

echo "2. Removing system packages that might conflict..."
sudo apt remove -y python3-sqlalchemy python3-flask-sqlalchemy

echo "3. Reinstalling system packages..."
sudo apt install -y python3-sqlalchemy python3-flask-sqlalchemy

echo "4. Checking Python paths..."
python3 -c "
import sys
print('Python paths:')
for p in sys.path:
    print(f'  {p}')
"

echo "5. Testing import..."
cd /home/maxx/orange-usbip
python3 -c "
try:
    import sqlalchemy
    print(f'✓ SQLAlchemy version: {sqlalchemy.__version__}')
    print(f'✓ SQLAlchemy location: {sqlalchemy.__file__}')
except Exception as e:
    print(f'✗ SQLAlchemy import failed: {e}')
    exit(1)

try:
    from flask_sqlalchemy import SQLAlchemy
    print('✓ Flask-SQLAlchemy import successful')
except Exception as e:
    print(f'✗ Flask-SQLAlchemy import failed: {e}')
    exit(1)

try:
    from app import app
    print('✓ App import successful')
except Exception as e:
    print(f'✗ App import failed: {e}')
    import traceback
    traceback.print_exc()
    exit(1)
"

if [ $? -eq 0 ]; then
    echo "6. Restarting service..."
    sudo systemctl restart orange-usbip
    sleep 2
    sudo systemctl status orange-usbip --no-pager
    echo "✓ Service should be running now"
else
    echo "✗ Import still failing"
    echo "Checking for remaining conflicts..."
    find /home/maxx/.local -name "*sqlalchemy*" -type d 2>/dev/null || true
fi

echo "=== Complete ==="