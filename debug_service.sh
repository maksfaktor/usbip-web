#!/bin/bash

echo "=== Debug Orange USB/IP Service ==="
echo

echo "1. Checking service status:"
sudo systemctl status orange-usbip --no-pager -l

echo
echo "2. Checking recent logs with details:"
sudo journalctl -u orange-usbip --no-pager -n 20 -o short-precise

echo
echo "3. Checking if Python can import the app:"
cd /home/maxx/orange-usbip
python3 -c "
try:
    from app import app
    print('✓ App import successful')
except Exception as e:
    print(f'✗ App import failed: {e}')
    import traceback
    traceback.print_exc()
"

echo
echo "4. Checking database file:"
ls -la /home/maxx/orange-usbip/usbip_web.db

echo
echo "5. Checking Python path and dependencies:"
which python3
python3 -m pip list | grep -E "(flask|sqlalchemy|werkzeug)"

echo
echo "6. Testing manual app start:"
cd /home/maxx/orange-usbip
timeout 5 python3 app.py || echo "Manual start failed or timed out"

echo
echo "7. Service file content:"
cat /etc/systemd/system/orange-usbip.service

echo
echo "=== Debug Complete ==="