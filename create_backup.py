#!/usr/bin/env python3
"""
Скрипт для создания резервной копии проекта Orange USB/IP и загрузки её на GitHub
"""

import os
import requests
import base64
import json
from datetime import datetime

# Конфигурация GitHub
GITHUB_TOKEN = os.environ.get('GITHUB_TOKEN')
GITHUB_REPO = 'maksfaktor/usbip-web'
GITHUB_API_URL = f'https://api.github.com/repos/{GITHUB_REPO}/contents'

def upload_to_github(file_path, github_path, message):
    """
    Загружает файл на GitHub
    """
    if not GITHUB_TOKEN:
        print("❌ GITHUB_TOKEN не найден в переменных окружения")
        return False
    
    try:
        # Читаем содержимое файла
        with open(file_path, 'rb') as f:
            content = f.read()
        
        # Кодируем в base64
        encoded_content = base64.b64encode(content).decode('utf-8')
        
        # Проверяем, существует ли файл
        headers = {
            'Authorization': f'token {GITHUB_TOKEN}',
            'Accept': 'application/vnd.github.v3+json'
        }
        
        response = requests.get(f'{GITHUB_API_URL}/{github_path}', headers=headers)
        sha = None
        if response.status_code == 200:
            sha = response.json()['sha']
        
        # Подготавливаем данные для загрузки
        data = {
            'message': message,
            'content': encoded_content
        }
        
        if sha:
            data['sha'] = sha
        
        # Отправляем запрос
        response = requests.put(f'{GITHUB_API_URL}/{github_path}', 
                              headers=headers, 
                              data=json.dumps(data))
        
        if response.status_code in [200, 201]:
            print(f"✅ Файл {github_path} успешно загружен")
            return True
        else:
            print(f"❌ Ошибка загрузки {github_path}: {response.status_code}")
            print(f"Ответ: {response.text}")
            return False
            
    except Exception as e:
        print(f"❌ Ошибка при загрузке файла {file_path}: {str(e)}")
        return False

def main():
    """
    Главная функция для создания и загрузки резервной копии
    """
    print("🔄 Создание резервной копии Orange USB/IP...")
    
    # Определяем имя файла с текущей датой
    current_time = datetime.now().strftime("%Y%m%d-%H%M%S")
    backup_filename = f"orange-usbip-backup-{current_time}.tar.gz"
    
    # Найдем последний созданный архив
    backup_files = [f for f in os.listdir('.') if f.startswith('orange-usbip-backup-') and f.endswith('.tar.gz')]
    
    if not backup_files:
        print("❌ Файлы резервной копии не найдены")
        return
    
    # Берем последний файл
    latest_backup = sorted(backup_files)[-1]
    print(f"📦 Найден архив: {latest_backup}")
    
    # Загружаем на GitHub
    commit_message = f"Backup: Orange USB/IP complete project backup - {current_time}"
    
    if upload_to_github(latest_backup, latest_backup, commit_message):
        print(f"✅ Резервная копия успешно сохранена на GitHub как {latest_backup}")
    else:
        print("❌ Не удалось загрузить резервную копию на GitHub")

if __name__ == "__main__":
    main()