# Orange USB/IP Web Interface

Веб-интерфейс для управления USB устройствами по сети через USB/IP протокол.

## Быстрый старт

### Установка

```bash
curl -fsSL https://raw.githubusercontent.com/maksfaktor/usbip-web/main/install_debian.sh | sudo bash
```

### Использование

1. Откройте http://ваш-ip:5000
2. Войдите (admin / admin123)
3. Публикуйте устройства через "Local USB Devices"
4. Подключайте через "Remote USB Devices"

## Функции

- 🔌 Публикация локальных USB устройств
- 🌐 Подключение удаленных USB устройств  
- 📊 Мониторинг состояния устройств
- 🔐 Аутентификация пользователей
- 🌍 Русский/English интерфейс

## Команды

**Диагностика:**
```bash
sudo ./doctor.sh
```

**Удаление:**
```bash
curl -fsSL https://raw.githubusercontent.com/maksfaktor/usbip-web/main/check_and_remove.sh | sudo bash
```

## Поддержка

- Debian/Ubuntu (x86_64, ARM)
- Orange Pi, Raspberry Pi
- Любой Linux с USB/IP

## Ссылки

- Проект: https://github.com/maksfaktor/usbip-web
- Issues: https://github.com/maksfaktor/usbip-web/issues

MIT License
