#!/bin/bash

# Создание виртуального окружения (если его нет)
if [ ! -d "venv" ]; then
    echo "Создание виртуального окружения Python..."
    python3 -m venv venv
fi

# Активация виртуального окружения
source venv/bin/activate

# Установка зависимостей
echo "Установка зависимостей Python..."
pip install --upgrade pip
pip install -r requirements-deploy.txt

echo "Установка Python зависимостей завершена."