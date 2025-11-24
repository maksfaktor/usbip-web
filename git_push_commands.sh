#!/bin/bash
# Git Push Commands for Task 13.1
# Copy and paste these commands into Shell

# Ensure .env is in .gitignore (check only)
grep "\.env" .gitignore || echo ".env" >> .gitignore

# Add modified files
git add install_debian.sh requirements-deploy.txt app.py FIDO2_PROGRESS.md replit.md

# Create commit
git commit -m "Task 13.1: Add portable paths support with .env configuration

- Enhanced install_debian.sh with Step 9 for automatic FIDO2 setup
- Added python-dotenv dependency for environment variable loading
- Updated app.py to load .env file on startup
- Fixed hardcoded /home/runner paths for cross-system compatibility
- Updated documentation in FIDO2_PROGRESS.md and replit.md"

# Push to GitHub
git push origin main
