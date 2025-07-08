#!/usr/bin/env python3
import os
import base64
import requests
import sys

# GitHub репозиторий и токен
REPO_OWNER = "maksfaktor"
REPO_NAME = "usbip-web"
GITHUB_TOKEN = os.environ.get("GITHUB_TOKEN")

if not GITHUB_TOKEN:
    print("Ошибка: Отсутствует токен GitHub.")
    print("Используйте: export GITHUB_TOKEN=your_token")
    sys.exit(1)

# Функция для получения SHA файла
def get_file_sha(file_path):
    # Обрабатываем случай с вложенными папками
    if '/' in file_path:
        # Проверяем существование папки
        folder_path = '/'.join(file_path.split('/')[:-1])
        file_name = file_path.split('/')[-1]
        api_url = f"https://api.github.com/repos/{REPO_OWNER}/{REPO_NAME}/contents/{folder_path}"
    else:
        api_url = f"https://api.github.com/repos/{REPO_OWNER}/{REPO_NAME}/contents"
        file_name = file_path
        
    headers = {
        "Authorization": f"token {GITHUB_TOKEN}",
        "Accept": "application/vnd.github.v3+json"
    }
    
    response = requests.get(api_url, headers=headers)
    if response.status_code == 200:
        contents = response.json()
        if isinstance(contents, list):
            for item in contents:
                if item["name"] == file_name:
                    return item["sha"]
            return None
        else:
            return contents.get("sha")
    elif response.status_code == 404:
        return None
    else:
        print(f"Ошибка при получении SHA для {file_path}: {response.status_code}")
        print(response.json())
        return None

# Функция для обновления файла
def update_file(file_path, message):
    with open(file_path, 'rb') as file:
        content = file.read()
    
    encoded_content = base64.b64encode(content).decode()
    sha = get_file_sha(file_path)
    
    api_url = f"https://api.github.com/repos/{REPO_OWNER}/{REPO_NAME}/contents/{file_path}"
    headers = {
        "Authorization": f"token {GITHUB_TOKEN}",
        "Accept": "application/vnd.github.v3+json"
    }
    
    data = {
        "message": message,
        "content": encoded_content,
        "branch": "main"
    }
    
    if sha:
        data["sha"] = sha
    
    response = requests.put(api_url, headers=headers, json=data)
    
    if response.status_code in [200, 201]:
        print(f"✅ Успешно обновлен файл: {file_path}")
        return True
    else:
        print(f"❌ Ошибка при обновлении {file_path}: {response.status_code}")
        print(response.json())
        return False

# Основная функция
def main():
    files_to_update = [
        "main.py",
        "app.py",
        "replit.md"
    ]
    
    commit_message = "Исправлена ошибка 500 после авторизации - добавлена поддержка PostgreSQL и SQLite"
    
    print("Отправляем изменения в GitHub...")
    
    for file_path in files_to_update:
        if os.path.exists(file_path):
            update_file(file_path, commit_message)
        else:
            print(f"⚠️ Файл не найден: {file_path}")

if __name__ == "__main__":
    main()