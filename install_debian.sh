#!/bin/bash

# Orange USBIP - Скрипт автоматической установки для Debian/Ubuntu систем
# Создан: $(date +%Y-%m-%d)

set -e  # Прерывать выполнение при ошибках

# Функция для отображения цветного текста
echo_color() {
    local color=$1
    local message=$2
    case $color in
        "green") echo -e "\033[0;32m$message\033[0m" ;;
        "red") echo -e "\033[0;31m$message\033[0m" ;;
        "yellow") echo -e "\033[0;33m$message\033[0m" ;;
        "blue") echo -e "\033[0;34m$message\033[0m" ;;
        *) echo "$message" ;;
    esac
}

# Функция для отображения прогресса
progress_update() {
    local step=$1
    local total=$2
    local message=$3
    echo_color "blue" "[$step/$total] $message"
}

# Проверка запуска от имени root
if [ "$EUID" -ne 0 ]; then
    echo_color "red" "Ошибка: скрипт должен быть запущен с правами суперпользователя (sudo)."
    echo "Запустите: sudo $0"
    exit 1
fi

# Определяем реального пользователя (не sudo)
if [ -n "$SUDO_USER" ]; then
    REAL_USER=$SUDO_USER
else
    REAL_USER=$(whoami)
fi
USER_HOME=$(eval echo ~$REAL_USER)

echo_color "green" "===================================================="
echo_color "green" "  Автоматическая установка Orange USBIP для Debian  "
echo_color "green" "===================================================="
echo ""
echo_color "yellow" "Этот скрипт настроит USB/IP сервер и клиент на вашей системе."
echo ""

TOTAL_STEPS=10
CURRENT_STEP=0

# Шаг 1: Проверка операционной системы
CURRENT_STEP=$((CURRENT_STEP + 1))
progress_update $CURRENT_STEP $TOTAL_STEPS "Проверка операционной системы..."

if ! command -v apt-get &> /dev/null; then
    echo_color "red" "Эта система не использует apt-get. Скрипт предназначен для Debian/Ubuntu-подобных систем."
    exit 1
fi

# Проверка архитектуры
ARCH=$(uname -m)

# Поддерживаемые архитектуры: x86, x86_64, arm64/aarch64
if [[ "$ARCH" == "arm"* ]] && [[ "$ARCH" != "armv7"* ]]; then
    echo_color "green" "✓ Архитектура $ARCH совместима (64-битный ARM)."
elif [[ "$ARCH" == "aarch64" ]]; then
    echo_color "green" "✓ Архитектура $ARCH совместима (64-битный ARM)."
elif [[ "$ARCH" == "armv7"* ]]; then
    echo_color "yellow" "Для 32-битных ARM систем (ARMv7) рекомендуется использовать скрипт install_arm.sh"
    echo "Продолжить установку? (y/n)"
    read -r response
    if [[ "$response" != "y" ]]; then
        echo_color "yellow" "Установка прервана пользователем."
        exit 0
    fi
elif [[ "$ARCH" == "x86_64" ]] || [[ "$ARCH" == "i686" ]]; then
    echo_color "green" "✓ Архитектура $ARCH совместима (x86/x86_64)."
else
    echo_color "yellow" "Архитектура $ARCH не тестировалась, но мы попробуем установить."
fi

# Шаг 2: Обновление системы
CURRENT_STEP=$((CURRENT_STEP + 1))
progress_update $CURRENT_STEP $TOTAL_STEPS "Обновление списка пакетов..."

apt-get update -qq
echo_color "green" "✓ Репозитории обновлены."

# Шаг 3: Установка необходимых зависимостей
CURRENT_STEP=$((CURRENT_STEP + 1))
progress_update $CURRENT_STEP $TOTAL_STEPS "Установка необходимых пакетов..."

apt-get install -y git python3 python3-pip python3-venv linux-tools-generic usbutils curl > /dev/null 2>&1

# Установка uv - современного пакетного менеджера Python
echo_color "yellow" "Установка uv - современного пакетного менеджера Python..."
curl -sSf https://astral.sh/uv/install.sh | sh > /dev/null 2>&1 || {
    echo_color "yellow" "Не удалось установить uv через скрипт, попробуем через pip..."
    pip3 install -q --break-system-packages uv
}

# Добавляем uv в PATH, если необходимо
export PATH="$HOME/.cargo/bin:$PATH"

# Проверка установки uv
if ! command -v uv &> /dev/null; then
    echo_color "yellow" "Не удалось установить uv. Будем использовать стандартный pip."
else
    echo_color "green" "✓ uv успешно установлен."
fi

echo_color "green" "✓ Необходимые пакеты установлены."

# Шаг 4: Проверка установки usbip
CURRENT_STEP=$((CURRENT_STEP + 1))
progress_update $CURRENT_STEP $TOTAL_STEPS "Проверка и настройка USB/IP..."

# Переменная для отслеживания, была ли установка компонентов, требующих перезагрузки
KERNEL_MODULES_INSTALLED=false

# Определяем версию ядра
echo_color "blue" "    → Определение версии ядра..."
KERNEL_VERSION=$(uname -r)
KERNEL_MAJOR=$(echo $KERNEL_VERSION | cut -d. -f1)
KERNEL_MINOR=$(echo $KERNEL_VERSION | cut -d. -f2)
echo_color "blue" "    → Обнаружена версия ядра: $KERNEL_VERSION"

# Устанавливаем соответствующий пакет linux-tools для конкретной версии ядра
echo_color "blue" "    → Установка Linux Tools для текущего ядра..."
if apt-cache show linux-tools-$KERNEL_VERSION &> /dev/null; then
    echo_color "blue" "    → Найден пакет linux-tools-$KERNEL_VERSION"
    apt-get install -y linux-tools-$KERNEL_VERSION > /dev/null 2>&1
    KERNEL_MODULES_INSTALLED=true
elif apt-cache show linux-tools-$(uname -r | cut -d- -f1) &> /dev/null; then
    KERNEL_BASE_VERSION=$(uname -r | cut -d- -f1)
    echo_color "blue" "    → Найден пакет linux-tools-$KERNEL_BASE_VERSION"
    apt-get install -y linux-tools-$KERNEL_BASE_VERSION > /dev/null 2>&1
    KERNEL_MODULES_INSTALLED=true
else
    echo_color "yellow" "    → Не найден специфичный пакет linux-tools для вашего ядра"
    echo_color "blue" "    → Устанавливаем общий пакет linux-tools-generic..."
    apt-get install -y linux-tools-generic > /dev/null 2>&1
    KERNEL_MODULES_INSTALLED=true
fi

# Создаем ссылку, если необходимо
if ! command -v usbip &> /dev/null; then
    echo_color "blue" "    → Поиск утилиты usbip в системе..."
    USBIP_PATH=$(find /usr/lib/linux-tools -name "usbip" | head -n 1)
    if [ -n "$USBIP_PATH" ]; then
        echo_color "blue" "    → Создание символической ссылки на usbip..."
        ln -sf "$USBIP_PATH" /usr/local/bin/usbip
    else
        echo_color "yellow" "    → Не удалось найти утилиту USB/IP. Пробуем другие методы..."
        echo_color "blue" "    → Попытка прямой установки пакетов для USB/IP..."
        apt-get install -y linux-tools-generic hwdata usbip > /dev/null 2>&1
    fi
fi

# Проверяем, успешно ли установлен USB/IP
if ! command -v usbip &> /dev/null; then
    if [ "$ARCH" == "armv7"* ]; then
        echo_color "yellow" "⚠ На ARMv7 могут потребоваться дополнительные шаги установки USB/IP."
        echo_color "yellow" "   Рекомендуется использовать скрипт install_arm.sh для этой архитектуры."
        
        echo "Хотите продолжить установку без USB/IP? (y/n)"
        read -r response
        if [[ "$response" != "y" ]]; then
            echo_color "blue" "Установка прервана. Используйте скрипт install_arm.sh"
            exit 0
        fi
    fi
    
    echo_color "red" "⚠ Не удалось установить USB/IP. Продолжение установки без USB/IP."
    echo_color "yellow" "Вам потребуется установить USB/IP вручную позже."
else
    echo_color "green" "✓ USB/IP успешно установлен."
fi

# Шаг 5: Загрузка модулей ядра
CURRENT_STEP=$((CURRENT_STEP + 1))
progress_update $CURRENT_STEP $TOTAL_STEPS "Настройка модулей ядра для USB/IP..."

# Добавление модулей в автозагрузку
MODULES_ADDED=false
if ! grep -q "usbip-core" /etc/modules; then
    echo "usbip-core" >> /etc/modules
    MODULES_ADDED=true
fi
if ! grep -q "usbip-host" /etc/modules; then
    echo "usbip-host" >> /etc/modules
    MODULES_ADDED=true
fi
if ! grep -q "vhci-hcd" /etc/modules; then
    echo "vhci-hcd" >> /etc/modules
    MODULES_ADDED=true
fi

# Пытаемся загрузить модули
MODULES_LOADED=true
echo_color "blue" "    → Загрузка модуля usbip-core..."
modprobe usbip-core 2>/dev/null || {
    echo_color "yellow" "    ⚠ Не удалось загрузить модуль usbip-core"
    MODULES_LOADED=false
}

echo_color "blue" "    → Загрузка модуля usbip-host..."
modprobe usbip-host 2>/dev/null || {
    echo_color "yellow" "    ⚠ Не удалось загрузить модуль usbip-host"
    MODULES_LOADED=false
}

echo_color "blue" "    → Загрузка модуля vhci-hcd..."
modprobe vhci-hcd 2>/dev/null || {
    echo_color "yellow" "    ⚠ Не удалось загрузить модуль vhci-hcd"
    MODULES_LOADED=false
}

# Если модули добавлены в автозагрузку или установлены новые компоненты ядра,
# и не все модули загружены - вероятно нужна перезагрузка
if ([ "$MODULES_ADDED" = true ] || [ "$KERNEL_MODULES_INSTALLED" = true ]) && [ "$MODULES_LOADED" = false ]; then
    echo_color "red" ""
    echo_color "red" "⚠ ВНИМАНИЕ: Возможно потребуется перезагрузка системы"
    echo_color "red" "для полной активации модулей ядра USB/IP!"
    echo_color "yellow" ""
    echo_color "yellow" "После перезагрузки, запустите скрипт еще раз для завершения установки."
    echo_color "yellow" "Команда для перезагрузки: sudo reboot"
    echo_color "yellow" ""
    
    echo "Продолжить установку без перезагрузки? (y/n)"
    read -r response
    if [[ "$response" != "y" ]]; then
        echo_color "blue" "Установка прервана. Пожалуйста, перезагрузите систему и запустите скрипт снова."
        exit 0
    fi
    
    echo_color "yellow" "Продолжаем установку. Некоторые функции могут не работать до перезагрузки."
fi

echo_color "green" "✓ Модули USB/IP настроены."

# Шаг 6: Настройка демона USB/IP
CURRENT_STEP=$((CURRENT_STEP + 1))
progress_update $CURRENT_STEP $TOTAL_STEPS "Настройка демона USB/IP..."

# Создаем systemd сервис для usbipd, если он не существует
if [ ! -f "/etc/systemd/system/usbipd.service" ]; then
    cat > /etc/systemd/system/usbipd.service << 'EOF'
[Unit]
Description=USB/IP daemon
After=network.target

[Service]
Type=simple
ExecStart=/usr/sbin/usbipd -D
Restart=on-failure

[Install]
WantedBy=multi-user.target
EOF

    systemctl daemon-reload
    systemctl enable usbipd
    systemctl start usbipd || echo_color "yellow" "Не удалось запустить usbipd, проверьте путь к бинарному файлу"
fi

echo_color "green" "✓ Демон USB/IP настроен."

# Шаг 7: Настройка каталога приложения
CURRENT_STEP=$((CURRENT_STEP + 1))
progress_update $CURRENT_STEP $TOTAL_STEPS "Создание каталога для приложения..."

APP_DIR="$USER_HOME/orange-usbip"
if [ ! -d "$APP_DIR" ]; then
    mkdir -p "$APP_DIR"
    chown $REAL_USER:$REAL_USER "$APP_DIR"
fi

# Клонирование репозитория
cd "$APP_DIR"
if [ -d ".git" ]; then
    echo "Обновление существующего репозитория..."
    sudo -u $REAL_USER git pull
else
    echo "Клонирование репозитория..."
    sudo -u $REAL_USER git clone https://github.com/maksfaktor/usbip-web.git .
fi

echo_color "green" "✓ Репозиторий успешно скачан в $APP_DIR."

# Шаг 8: Настройка виртуальной среды Python
CURRENT_STEP=$((CURRENT_STEP + 1))
progress_update $CURRENT_STEP $TOTAL_STEPS "Настройка виртуальной среды Python..."

cd "$APP_DIR"
if [ ! -d "venv" ]; then
    sudo -u $REAL_USER python3 -m venv venv
fi

# Установка зависимостей через uv или pip
if command -v uv &> /dev/null; then
    echo_color "blue" "Используем uv для быстрой установки зависимостей..."
    sudo -u $REAL_USER bash -c "
    source venv/bin/activate
    uv pip install --upgrade pip
    uv pip install -r requirements-deploy.txt
    deactivate
    "
else
    echo_color "yellow" "Используем стандартный pip для установки зависимостей..."
    sudo -u $REAL_USER bash -c "
    source venv/bin/activate
    pip install --upgrade pip
    pip install -r requirements-deploy.txt
    deactivate
    "
fi

echo_color "green" "✓ Виртуальная среда Python настроена."

# Шаг 9: Создание systemd сервиса
CURRENT_STEP=$((CURRENT_STEP + 1))
progress_update $CURRENT_STEP $TOTAL_STEPS "Создание systemd сервиса..."

cat > /etc/systemd/system/orange-usbip.service << EOF
[Unit]
Description=Orange USBIP Web Interface
After=network.target usbipd.service

[Service]
User=$REAL_USER
Group=$REAL_USER
WorkingDirectory=$APP_DIR
ExecStart=$APP_DIR/venv/bin/gunicorn --bind 0.0.0.0:5000 main:app
Restart=on-failure
Environment="PATH=$APP_DIR/venv/bin:/usr/local/sbin:/usr/local/bin:/usr/sbin:/usr/bin:/sbin:/bin"

[Install]
WantedBy=multi-user.target
EOF

systemctl daemon-reload
systemctl enable orange-usbip
systemctl start orange-usbip

echo_color "green" "✓ Systemd сервис создан и запущен."

# Шаг 10: Настройка доступа к USB/IP через sudo
CURRENT_STEP=$((CURRENT_STEP + 1))
progress_update $CURRENT_STEP $TOTAL_STEPS "Настройка прав доступа для USB/IP..."

# Настройка sudo для пользователя
if [ ! -f "/etc/sudoers.d/usbip-$REAL_USER" ]; then
    cat > "/etc/sudoers.d/usbip-$REAL_USER" << EOF
$REAL_USER ALL=(ALL) NOPASSWD: /usr/sbin/usbip
$REAL_USER ALL=(ALL) NOPASSWD: /usr/lib/linux-tools/*/usbip
$REAL_USER ALL=(ALL) NOPASSWD: /usr/local/bin/usbip
EOF
    chmod 440 "/etc/sudoers.d/usbip-$REAL_USER"
fi

echo_color "green" "✓ Права доступа настроены."

# Проверка запуска сервиса
if systemctl is-active --quiet orange-usbip; then
    # Получаем IP-адрес
    IP_ADDR=$(hostname -I | awk '{print $1}')
    
    echo_color "green" "===================================================="
    echo_color "green" "  Установка Orange USBIP успешно завершена!     "
    echo_color "green" "===================================================="
    echo ""
    echo_color "yellow" "Сервис доступен по адресу: http://$IP_ADDR:5000"
    echo_color "yellow" "Логин: admin"
    echo_color "yellow" "Пароль: admin"
    echo ""
    echo_color "red" "ВНИМАНИЕ: Обязательно смените пароль после первого входа!"
    echo ""
    echo_color "blue" "Управление сервисом:"
    echo " - Перезапуск:   sudo systemctl restart orange-usbip"
    echo " - Остановка:    sudo systemctl stop orange-usbip"
    echo " - Статус:       sudo systemctl status orange-usbip"
    echo " - Логи:         sudo journalctl -u orange-usbip"
    echo ""
else
    echo_color "red" "Сервис не запустился. Проверьте логи: sudo journalctl -u orange-usbip"
    exit 1
fi

exit 0