# Orange USB/IP Web Interface - Готово к установке

## 🚀 Быстрая установка

[0;31mError: this script must be run with superuser privileges (sudo).[0m
Run: sudo /nix/store/x9d49vaqlrkw97p9ichdwrnbh013kq7z-bash-interactive-5.2p37/bin/bash

## 🔧 Последние исправления (09.07.2025)

### ✅ Что исправлено:
- Правильное отображение имен устройств (вместо "Unknown Device")
- Корректная работа кнопки "Publish Device"
- Правильный формат busid (1-8 вместо 1-5)
- Статус публикации устройств в реальном времени

### 🔍 Ожидаемые результаты:
- Имена устройств: "Chicony Electronics Co., Ltd : unknown product"
- Кнопка "Publish" становится зеленой "Published" после публикации
- Корректная работа с usbip list -l

## 📦 Доступные бекапы:
- orange-usbip-backup-20250708-214201.tar.gz - Предыдущая версия
- orange-usbip-backup-20250709-012300.tar.gz - Текущая версия с исправлениями

## 🔧 Удаление (если нужно):
[0;32m========================================================[0m
[0;32m  Orange USB/IP Service and Application Removal Tool   [0m
[0;32m========================================================[0m

[0;31mError: This script must be run with superuser privileges (sudo).[0m
Examples:
  sudo bash -c "$(curl -fsSL https://raw.githubusercontent.com/maksfaktor/usbip-web/main/check_and_remove.sh)"
  sudo ./check_and_remove.sh

## 🌐 Доступ:
После установки откройте в браузере: http://ваш-ip:5000
Логин: admin / Пароль: admin123
