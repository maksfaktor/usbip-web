# Orange USBIP

Комплексное веб-решение для управления USB/IP на Linux, позволяющее публиковать, подключать и эмулировать USB-устройства через сеть.

<div align="center">

**🏆 Полностью кроссплатформенное управление USB устройствами по сети**  
**💻 Работает на всех Linux: ARM, x86, x86_64, ARM64 📱**

</div>

## 📌 Быстрая установка в одну команду

### ARMv7 (Orange Pi, Raspberry Pi 32-bit):
```bash
sudo bash -c "$(curl -fsSL https://raw.githubusercontent.com/maksfaktor/usbip-web/main/install_arm.sh)"
```

### x86, x86_64, ARM64 (Raspberry Pi 64-bit):
```bash
sudo bash -c "$(curl -fsSL https://raw.githubusercontent.com/maksfaktor/usbip-web/main/install_debian.sh)"
```

## Что такое Orange USBIP?

Orange USBIP — это веб-интерфейс на Flask для технологии USB/IP, которая позволяет использовать USB-устройства по сети. Проект разработан для легкого управления USB-устройствами на всех Linux платформах, включая ARM (Raspberry Pi, Orange Pi), x86, x86_64 и ARM64.

## Основные возможности

✅ **Управление физическими USB-устройствами:**
- Публикация локальных USB-устройств для удаленного доступа
- Подключение к удаленным устройствам по сети
- Настройка алиасов для удобной идентификации устройств

✅ **Эмуляция виртуальных USB-устройств:**
- Создание виртуальных HID-устройств (клавиатуры, мыши)
- Эмуляция USB-накопителей с управляемым хранилищем
- Настройка виртуальных COM-портов

✅ **Дополнительные возможности:**
- Мультиязычный интерфейс (русский и английский)
- Защищенный доступ с аутентификацией
- Детальное логирование действий
- Автоматическое определение сетевых интерфейсов

## Технологии

- Python 3
- Flask
- SQLAlchemy
- SQLite (по умолчанию) или PostgreSQL (опционально)
- USB/IP (Linux)
- Bootstrap 5
- Мультиязычный интерфейс (английский и русский)

## Требования

- Linux с установленной утилитой USB/IP
- Python 3.7+

### Установка USB/IP в Linux

На большинстве дистрибутивов Linux утилиту USB/IP можно установить следующим образом:

#### Ubuntu/Debian:
```
sudo apt update
sudo apt install linux-tools-generic
```

#### Fedora:
```
sudo dnf install kernel-modules-extra
sudo dnf install usbip
```

#### Arch Linux:
```
sudo pacman -S usbip
```

### О базе данных

По умолчанию приложение использует SQLite, что не требует дополнительной настройки. База данных будет автоматически создана при первом запуске приложения.

#### Использование PostgreSQL (опционально)

Если вам необходимо использовать PostgreSQL вместо SQLite, вы можете установить его и настроить:

```
# Установка PostgreSQL
sudo apt install postgresql postgresql-contrib

# Запуск и включение службы PostgreSQL
sudo systemctl start postgresql
sudo systemctl enable postgresql

# Создание пользователя и базы данных
sudo -u postgres psql -c "CREATE USER usbip_user WITH PASSWORD 'your_password';"
sudo -u postgres psql -c "CREATE DATABASE usbip_db OWNER usbip_user;"
sudo -u postgres psql -c "GRANT ALL PRIVILEGES ON DATABASE usbip_db TO usbip_user;"

# Установка переменной окружения для использования PostgreSQL
export DATABASE_URL="postgresql://usbip_user:your_password@localhost/usbip_db"
```

## Установка

### Быстрая установка

Просто скопируйте и вставьте **одну** из следующих команд в терминал:

#### Для ARMv7 (Orange Pi, Raspberry Pi 32-bit и др.):

```bash
sudo bash -c "$(curl -fsSL https://raw.githubusercontent.com/maksfaktor/usbip-web/main/install_arm.sh)"
```

#### Для x86, x86_64 и ARM64 (включая Raspberry Pi 64-bit):

```bash
sudo bash -c "$(curl -fsSL https://raw.githubusercontent.com/maksfaktor/usbip-web/main/install_debian.sh)"
```

### Стандартная автоматическая установка

Если вы предпочитаете проверить скрипт перед выполнением, можете использовать стандартный подход:

1. Скачайте установочный скрипт
2. Сделайте его исполняемым
3. Запустите от имени суперпользователя

#### Для ARM-устройств (Orange Pi, Raspberry Pi 32-bit):

```bash
wget https://raw.githubusercontent.com/maksfaktor/usbip-web/main/install_arm.sh
chmod +x install_arm.sh
sudo ./install_arm.sh
```

#### Для x86, x86_64 и ARM64 систем:

```bash
wget https://raw.githubusercontent.com/maksfaktor/usbip-web/main/install_debian.sh
chmod +x install_debian.sh
sudo ./install_debian.sh
```

### Что делают установочные скрипты?

Скрипты автоматически выполняют все необходимые шаги:
1. ✅ Проверяют и устанавливают все системные зависимости
2. ✅ Настраивают модули ядра для USB/IP
3. ✅ Создают и запускают systemd-сервисы
4. ✅ Настраивают права доступа
5. ✅ Создают рабочий каталог и виртуальное окружение Python
6. ✅ Проверяют необходимость перезагрузки системы
7. ✅ Сообщают IP-адрес для доступа к веб-интерфейсу

После успешной установки скрипт выведет адрес для доступа к веб-интерфейсу и учетные данные по умолчанию (`admin`/`admin`). Приложение будет запущено как системный сервис, который запускается автоматически при старте системы.

### Ручная установка (для опытных пользователей)

Если вы предпочитаете устанавливать программу вручную, выполните следующие шаги:

1. Установите необходимые системные зависимости:
   ```bash
   sudo apt update
   sudo apt install git python3 python3-pip python3-venv linux-tools-generic curl
   ```

2. Установите и настройте USB/IP:
   ```bash
   sudo modprobe usbip-core
   sudo modprobe usbip-host
   sudo modprobe vhci-hcd
   
   # Добавление модулей в автозагрузку
   echo "usbip-core" | sudo tee -a /etc/modules
   echo "usbip-host" | sudo tee -a /etc/modules
   echo "vhci-hcd" | sudo tee -a /etc/modules
   ```

3. Клонируйте репозиторий:
   ```bash
   mkdir -p ~/orange-usbip
   cd ~/orange-usbip
   git clone https://github.com/maksfaktor/usbip-web.git .
   ```

4. Создайте и активируйте виртуальное окружение:

   **Вариант 1: Установка через uv (рекомендуется для ускорения):**
   ```bash
   python3 -m venv venv
   source venv/bin/activate
   
   # Установка uv
   curl -sSf https://astral.sh/uv/install.sh | sh
   export PATH="$HOME/.cargo/bin:$PATH"
   
   # Установка зависимостей через uv
   uv pip install --upgrade pip
   uv pip install -r requirements-deploy.txt
   ```

   **Вариант 2: Стандартная установка через pip:**
   ```bash
   python3 -m venv venv
   source venv/bin/activate
   pip install --upgrade pip
   pip install -r requirements-deploy.txt
   ```

5. Для запуска приложения используйте:
   ```bash
   gunicorn --bind 0.0.0.0:5000 main:app
   ```

6. Чтобы настроить systemd-сервис, создайте файл `/etc/systemd/system/orange-usbip.service`:
   ```ini
   [Unit]
   Description=Orange USBIP Web Interface
   After=network.target

   [Service]
   User=YOUR_USERNAME
   Group=YOUR_USERNAME
   WorkingDirectory=/home/YOUR_USERNAME/orange-usbip
   ExecStart=/home/YOUR_USERNAME/orange-usbip/venv/bin/gunicorn --bind 0.0.0.0:5000 main:app
   Restart=on-failure

   [Install]
   WantedBy=multi-user.target
   ```

   Затем включите и запустите сервис:
   ```bash
   sudo systemctl daemon-reload
   sudo systemctl enable orange-usbip
   sudo systemctl start orange-usbip
   ```

> **Примечание по базе данных**: По умолчанию приложение использует SQLite. Для использования PostgreSQL установите переменную окружения в файле сервиса: `Environment="DATABASE_URL=postgresql://user:password@localhost/usbip_db"`

## Использование

После запуска приложения откройте браузер и перейдите по адресу http://localhost:5000/

По умолчанию создается пользователь с логином `admin` и паролем `admin`.
**Важно**: После первого входа в систему обязательно смените пароль администратора!

## Кросс-платформенная совместимость

Приложение разработано для работы на различных процессорных архитектурах:
- ARM (Orange Pi, Raspberry Pi и др.)
- x86
- x86-64

### Настройка на Orange Pi, Raspberry Pi и других ARM-устройствах

Для установки на ARM-устройства рекомендуется использовать специальный автоматический скрипт `install_arm.sh`, как описано в разделе "Автоматическая установка". Скрипт справится со всеми особенностями платформы, включая:

1. Компиляцию и установку USB/IP из исходников (на некоторых ARM-платформах стандартные пакеты могут не работать)
2. Настройку и загрузку совместимых модулей ядра
3. Создание необходимых системных сервисов
4. Оптимизацию для работы на устройствах с ограниченными ресурсами

```bash
# Скачайте установочный скрипт
wget https://raw.githubusercontent.com/maksfaktor/usbip-web/main/install_arm.sh

# Сделайте скрипт исполняемым
chmod +x install_arm.sh

# Запустите скрипт от имени суперпользователя
sudo ./install_arm.sh
```

После установки веб-интерфейс будет доступен на порту 5000, а логи можно просмотреть с помощью `sudo journalctl -u orange-usbip`.

## Безопасность

Все команды USB/IP выполняются с привилегиями root через sudo. 
Рекомендуется настроить sudoers для выполнения специфичных команд usbip без пароля.

### Настройка Sudo для USB/IP

Чтобы избежать постоянного ввода пароля при выполнении команд USB/IP, настройте файл sudoers:

```
# Откройте файл sudoers для редактирования
sudo visudo -f /etc/sudoers.d/usbip

# Добавьте следующие строки, заменив YOUR_USERNAME на ваше имя пользователя
YOUR_USERNAME ALL=(ALL) NOPASSWD: /usr/sbin/usbip
YOUR_USERNAME ALL=(ALL) NOPASSWD: /usr/lib/linux-tools/*/usbip

# Сохраните файл и выйдите (в vi: нажмите ESC, затем :wq и Enter)
```

После этого вы сможете выполнять команды usbip с sudo без запроса пароля.

## Тестирование в локальной сети

Вы можете настроить тестовую среду с несколькими компьютерами, где каждый из них может выступать как в роли USB/IP сервера (предоставляющего USB устройства), так и в роли клиента (подключающегося к удаленным USB устройствам).

### Настройка тестовой среды с двумя компьютерами

Эта инструкция поможет вам настроить два компьютера в локальной сети для тестирования функциональности USB/IP.

#### Предварительные требования

- Два компьютера с поддержкой Linux
- Локальная сеть с возможностью соединения между компьютерами
- USB устройства для тестирования

#### Шаг 1: Настройка сети

1. Настройте статические IP-адреса на обоих компьютерах:

   **Компьютер A:**
   ```
   sudo ip addr add 192.168.1.10/24 dev eth0
   ```

   **Компьютер B:**
   ```
   sudo ip addr add 192.168.1.11/24 dev eth0
   ```

   Замените `eth0` на имя вашего сетевого интерфейса.

2. Убедитесь, что компьютеры видят друг друга:

   ```
   ping 192.168.1.10  # с компьютера B
   ping 192.168.1.11  # с компьютера A
   ```

3. Настройте брандмауэр для разрешения соединений по порту 3240:

   ```
   sudo ufw allow 3240/tcp  # для Ubuntu/Debian с ufw
   # или
   sudo firewall-cmd --permanent --add-port=3240/tcp  # для Fedora/RHEL
   sudo firewall-cmd --reload
   ```

#### Шаг 2: Установка на обоих компьютерах

Следуйте инструкциям из раздела "Установка" для каждого компьютера:

1. Установите USB/IP
2. Установите зависимости
3. Клонируйте и настройте приложение

SQLite будет использоваться по умолчанию, без необходимости дополнительной настройки.

#### Шаг 3: Запуск демона USB/IP

На обоих компьютерах запустите демон USB/IP:

```
sudo systemctl start usbipd
sudo systemctl enable usbipd
```

#### Шаг 4: Запуск приложения

На обоих компьютерах запустите приложение:

```
source venv/bin/activate
gunicorn --bind 0.0.0.0:5000 main:app
```

Приложение будет использовать SQLite по умолчанию. Если нужен PostgreSQL, перед запуском добавьте:

```
export DATABASE_URL=postgresql://usbip_user:your_password@localhost/usbip_db
```

#### Шаг 5: Тестирование функциональности

1. **Проверка публикации устройств:**
   - На компьютере A откройте веб-интерфейс по адресу http://192.168.1.10:5000/
   - Войдите в систему
   - На главной странице найдите свои USB устройства
   - Нажмите кнопку "Опубликовать" для одного из устройств

2. **Проверка подключения к удаленным устройствам:**
   - На компьютере B откройте веб-интерфейс по адресу http://192.168.1.11:5000/
   - Войдите в систему
   - Перейдите на страницу "Удаленные устройства"
   - Введите IP-адрес компьютера A (192.168.1.10) и нажмите "Поиск устройств"
   - Вы должны увидеть опубликованные устройства с компьютера A
   - Нажмите "Подключить" для одного из устройств
   - Вернитесь на главную страницу, где теперь должно отображаться подключенное удаленное устройство

3. **Тестирование в обратном направлении:**
   - Повторите шаги 1-2, но публикуйте устройства с компьютера B и подключайтесь к ним с компьютера A

### Возможные проблемы и их решение

1. **Устройства не отображаются на странице удаленных устройств:**
   - Убедитесь, что порт 3240 открыт в брандмауэре
   - Проверьте, запущен ли демон usbipd на компьютере-сервере
   - Убедитесь, что устройство правильно опубликовано

2. **Ошибка при подключении устройства:**
   - Проверьте журналы на обоих компьютерах (`journalctl -u usbipd`)
   - Убедитесь, что устройство поддерживается USB/IP (не все устройства могут работать)
   - Проверьте наличие необходимых прав доступа

3. **Устройство отображается, но не работает после подключения:**
   - Некоторые устройства требуют дополнительных драйверов или настроек
   - USB устройства, требующие высокой скорости передачи данных, могут работать нестабильно через сеть
   - Попробуйте отключить и снова подключить устройство

## Лицензия

MIT

## Структура проекта

### Основные рабочие файлы проекта:
✓ app.py - главный файл приложения с маршрутами и логикой
✓ models.py - модели данных SQLite
✓ storage_routes.py - маршруты для управления хранилищем
✓ translations.py - система многоязычности
✓ usbip_utils.py - утилиты для работы с USB/IP
✓ virtual_storage_utils.py - функции для виртуального хранилища
✓ main.py - запуск приложения (используется)

### Статические файлы:
Все файлы в каталоге static/css, static/js и static/img используются в шаблонах через url_for.

### Каталоги, которые можно игнорировать в git:
✓ __pycache__ - кэш Python модулей
✓ .cache - кэш для UV
✓ attached_assets - вспомогательные файлы для Replit