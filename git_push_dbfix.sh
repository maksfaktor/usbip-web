#!/bin/bash
# Git Push for Database Permissions Fix

# Add modified files
git add install_debian.sh FIDO2_PROGRESS.md replit.md

# Create commit
git commit -m "Hotfix: Auto-initialize database with correct permissions

PROBLEM: Installation creates database as root, causing 'readonly database' error
when service runs as user.

SOLUTION:
- Added database initialization step BEFORE service starts
- Database created as user (not root) via: su - user -c 'python db.create_all()'
- Set correct permissions: chmod 664 instance/app.db
- Service starts only AFTER database is ready

RESULT: Fully automatic installation with no manual configuration needed.

Fixes: sqlite3.OperationalError: attempt to write a readonly database"

# Push to GitHub
git push origin main

echo ""
echo "✅ Changes pushed to GitHub!"
echo ""
echo "Now you can test on your Lenovo PC:"
echo "  sudo bash -c \"\$(curl -fsSL https://raw.githubusercontent.com/maksfaktor/usbip-web/main/install_debian.sh)\""
