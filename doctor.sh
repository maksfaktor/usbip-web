#!/bin/bash

# Функции для цветного вывода
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[0;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

echo_color() {
    color=$1
    message=$2
    case "$color" in
        "red") echo -e "${RED}$message${NC}" ;;
        "green") echo -e "${GREEN}$message${NC}" ;;
        "yellow") echo -e "${YELLOW}$message${NC}" ;;
        "blue") echo -e "${BLUE}$message${NC}" ;;
        *) echo "$message" ;;
    esac
}

# Функция для проверки статуса
check_status() {
    if [ $? -eq 0 ]; then
        echo_color "green" "✓ $1"
    else
        echo_color "red" "✗ $1"
        if [ ! -z "$2" ]; then
            echo_color "yellow" "  → $2"
        fi
    fi
}

# Функция для отображения заголовка
show_header() {
    echo ""
    echo_color "blue" "===================================================="
    echo_color "blue" "  $1"
    echo_color "blue" "===================================================="
    echo ""
}

# Функция для проверки наличия команды
check_command() {
    command -v $1 > /dev/null 2>&1
    check_status "Команда $1 доступна" "Установите пакет, содержащий команду $1"
}

# Основной скрипт
clear
show_header "Orange USBIP Diagnostic Tool"

# Проверка операционной системы
show_header "1. Проверка операционной системы"
echo "Имя операционной системы: $(uname -s)"
echo "Версия операционной системы: $(uname -r)"
echo "Архитектура: $(uname -m)"

# Проверка наличия необходимых команд
show_header "2. Проверка наличия необходимых команд"
check_command "usbip"
check_command "gunicorn"
check_command "python3"
check_command "systemctl"
check_command "nc"

# Проверка запущенных сервисов
show_header "3. Проверка запущенных сервисов"

# Проверка службы usbipd
echo "Проверка службы usbipd:"
systemctl is-active --quiet usbipd
if [ $? -eq 0 ]; then
    echo_color "green" "✓ Служба usbipd запущена"
else
    echo_color "red" "✗ Служба usbipd не запущена"
    echo_color "yellow" "  → Выполняется поиск исполняемого файла usbipd..."
    
    USBIPD_PATH=$(find /usr -name "usbipd" -type f -executable 2>/dev/null | head -1)
    if [ -z "$USBIPD_PATH" ]; then
        echo_color "red" "  → Исполняемый файл usbipd не найден"
    else
        echo_color "green" "  → Найден исполняемый файл usbipd: $USBIPD_PATH"
        echo_color "yellow" "  → Проверка наличия запущенного процесса usbipd..."
        
        ps aux | grep -v grep | grep -q usbipd
        if [ $? -eq 0 ]; then
            echo_color "green" "  → Процесс usbipd запущен"
        else
            echo_color "red" "  → Процесс usbipd не запущен"
            echo_color "yellow" "  → Рекомендуется запустить usbipd вручную: sudo $USBIPD_PATH -D"
        fi
    fi
fi

# Проверка службы Orange USBIP
echo "Проверка службы Orange USBIP:"
systemctl is-active --quiet orange-usbip
if [ $? -eq 0 ]; then
    echo_color "green" "✓ Служба orange-usbip запущена"
else
    echo_color "red" "✗ Служба orange-usbip не запущена"
    echo_color "yellow" "  → Рекомендуется запустить службу: sudo systemctl start orange-usbip"
fi

# Проверка модулей ядра
show_header "4. Проверка модулей ядра"
echo "Проверка модуля usbip-core:"
lsmod | grep -q usbip_core
check_status "Модуль usbip-core загружен" "Загрузите модуль: sudo modprobe usbip-core"

echo "Проверка модуля usbip-host:"
lsmod | grep -q usbip_host
check_status "Модуль usbip-host загружен" "Загрузите модуль: sudo modprobe usbip-host"

echo "Проверка модуля vhci-hcd:"
lsmod | grep -q vhci_hcd
check_status "Модуль vhci-hcd загружен" "Загрузите модуль: sudo modprobe vhci-hcd"

# Проверка открытых портов
show_header "5. Проверка открытых портов"
echo "Проверка порта 3240 (usbipd):"
netstat -tuln | grep -q ":3240 "
if [ $? -eq 0 ]; then
    echo_color "green" "✓ Порт 3240 прослушивается"
else
    echo_color "red" "✗ Порт 3240 не прослушивается"
    echo_color "yellow" "  → Служба usbipd не запущена или не прослушивает порт"
    echo_color "yellow" "  → Рекомендуется перезапустить службу usbipd"
fi

echo "Проверка порта 5000 (Orange USBIP Web):"
netstat -tuln | grep -q ":5000 "
if [ $? -eq 0 ]; then
    echo_color "green" "✓ Порт 5000 прослушивается"
else
    echo_color "red" "✗ Порт 5000 не прослушивается"
    echo_color "yellow" "  → Веб-интерфейс Orange USBIP не запущен"
    echo_color "yellow" "  → Рекомендуется перезапустить службу orange-usbip"
fi

# Проверка брандмауэра
show_header "6. Проверка брандмауэра"
if command -v ufw > /dev/null 2>&1; then
    echo "Статус UFW:"
    sudo ufw status | grep -q "Status: active"
    if [ $? -eq 0 ]; then
        echo_color "yellow" "UFW активен, проверка правил для портов 3240 и 5000:"
        sudo ufw status | grep -q "3240"
        if [ $? -eq 0 ]; then
            echo_color "green" "✓ Порт 3240 разрешен в UFW"
        else
            echo_color "red" "✗ Порт 3240 не разрешен в UFW"
            echo_color "yellow" "  → Рекомендуется разрешить порт: sudo ufw allow 3240/tcp"
        fi
        
        sudo ufw status | grep -q "5000"
        if [ $? -eq 0 ]; then
            echo_color "green" "✓ Порт 5000 разрешен в UFW"
        else
            echo_color "red" "✗ Порт 5000 не разрешен в UFW"
            echo_color "yellow" "  → Рекомендуется разрешить порт: sudo ufw allow 5000/tcp"
        fi
    else
        echo_color "green" "UFW неактивен, порты не блокируются"
    fi
else
    echo_color "yellow" "UFW не установлен, проверка iptables:"
    sudo iptables -L INPUT -n | grep -q "3240"
    if [ $? -eq 0 ]; then
        echo_color "green" "✓ Порт 3240 разрешен в iptables"
    else
        echo_color "yellow" "Порт 3240 может быть заблокирован в iptables"
        echo_color "yellow" "  → Рекомендуется разрешить порт: sudo iptables -I INPUT -p tcp --dport 3240 -j ACCEPT"
    fi
fi

# Проверка опубликованных устройств
show_header "7. Проверка опубликованных устройств"
sudo usbip list -l > /dev/null 2>&1
if [ $? -eq 0 ]; then
    echo "Локальные USB устройства:"
    DEVICES=$(sudo usbip list -l | grep -c "busid")
    if [ $DEVICES -gt 0 ]; then
        echo_color "green" "✓ Найдено $DEVICES устройств"
        echo ""
        sudo usbip list -l | grep -A 1 "busid" | grep -v "\-\-" | sed 's/^/  /'
    else
        echo_color "yellow" "✗ Не найдено USB устройств"
    fi
    
    echo ""
    echo "Опубликованные устройства:"
    PUBLISHED=$(sudo usbip port | grep -c "usbip")
    if [ $PUBLISHED -gt 0 ]; then
        echo_color "green" "✓ Найдено $PUBLISHED опубликованных устройств"
        echo ""
        sudo usbip port | grep -A 1 "Port" | grep -v "\-\-" | sed 's/^/  /'
    else
        echo_color "yellow" "✗ Нет опубликованных устройств"
        echo_color "yellow" "  → Для публикации устройства используйте: sudo usbip bind -b <busid>"
    fi
else
    echo_color "red" "✗ Не удалось получить список USB устройств"
    echo_color "yellow" "  → Возможно, команда usbip недоступна или не имеет нужных прав"
fi

# Проверка сетевых интерфейсов
show_header "8. Проверка сетевых интерфейсов"
if command -v ip > /dev/null 2>&1; then
    echo "Доступные сетевые интерфейсы:"
    ip -br addr show | grep -v "lo" | awk '{print "  " $1 ": " $3}'
    
    echo ""
    echo "Маршруты по умолчанию:"
    ip route | grep default | sed 's/^/  /'
else
    echo_color "yellow" "Команда ip не найдена, используем ifconfig"
    ifconfig | grep -E "inet|eth|wlan" | grep -v "inet6" | sed 's/^/  /'
fi

# Проверка соединения с другими серверами
show_header "9. Тест сетевого соединения"
echo "Введите IP-адрес удаленного сервера для проверки (или оставьте пустым для пропуска):"
read remote_ip

if [ ! -z "$remote_ip" ]; then
    echo "Проверка доступности $remote_ip через ping:"
    ping -c 3 $remote_ip > /dev/null 2>&1
    check_status "Сервер $remote_ip доступен по ping" "Проверьте сетевое соединение и настройки брандмауэра"
    
    echo "Проверка порта 3240 на $remote_ip:"
    nc -z -w 5 $remote_ip 3240 > /dev/null 2>&1
    check_status "Порт 3240 на $remote_ip доступен" "Убедитесь, что на удаленном сервере запущен usbipd и разрешен порт 3240"
    
    echo "Проверка соединения с удаленным сервером через usbip:"
    sudo usbip list -r $remote_ip > /dev/null 2>&1
    if [ $? -eq 0 ]; then
        echo_color "green" "✓ Успешное соединение с сервером $remote_ip"
        echo ""
        echo "Доступные устройства на сервере $remote_ip:"
        sudo usbip list -r $remote_ip | grep -A 1 "busid" | grep -v "\-\-" | sed 's/^/  /'
    else
        echo_color "red" "✗ Не удалось получить список устройств с сервера $remote_ip"
        echo_color "yellow" "  → Убедитесь, что на удаленном сервере:"
        echo_color "yellow" "    1. Запущен сервис usbipd"
        echo_color "yellow" "    2. Есть опубликованные устройства"
        echo_color "yellow" "    3. Разрешены соединения на порт 3240"
    fi
fi

# Заключение
show_header "Диагностика завершена"
echo "Если у вас возникли проблемы, обратитесь к документации или форуму поддержки."
echo "Дополнительная информация: https://github.com/maksfaktor/usbip-web"
echo ""