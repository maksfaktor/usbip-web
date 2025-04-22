#!/bin/bash

# Скрипт для установки Python 3 на Orange Pi Plus 2E (ARMv7)
# Установка будет произведена в /usr/local, чтобы не затрагивать системный Python

set -e # Прекращение выполнения при ошибке

# Функция для вывода сообщений
log() {
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] $1"
}

# Проверка root прав
if [ "$(id -u)" -ne 0 ]; then
    log "Ошибка: для установки требуются права root. Запустите скрипт с sudo."
    exit 1
fi

# Проверка архитектуры
ARCH=$(uname -m)
if [[ "$ARCH" != "armv7"* && "$ARCH" != "arm"* ]]; then
    log "Предупреждение: этот скрипт оптимизирован для ARMv7, но текущая архитектура - $ARCH"
    read -p "Продолжить установку? (y/n): " -n 1 -r
    echo
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        exit 1
    fi
fi

log "Начало установки Python 3 для Orange Pi Plus 2E (ARMv7)..."
log "Архитектура системы: $ARCH"

# Установка необходимых зависимостей
log "Установка зависимостей..."
apt-get update
apt-get install -y build-essential libssl-dev zlib1g-dev libbz2-dev \
    libreadline-dev libsqlite3-dev wget curl llvm libncurses5-dev libncursesw5-dev \
    xz-utils tk-dev libffi-dev liblzma-dev git usbip

# Определение версии Python для установки (используем последнюю стабильную 3.11)
PYTHON_VERSION="3.11.4"
log "Будет установлен Python версии $PYTHON_VERSION"

# Создание временной директории
TMP_DIR=$(mktemp -d)
log "Временная директория для сборки: $TMP_DIR"
cd "$TMP_DIR"

# Загрузка исходного кода Python
log "Загрузка исходного кода Python $PYTHON_VERSION..."
wget "https://www.python.org/ftp/python/${PYTHON_VERSION}/Python-${PYTHON_VERSION}.tar.xz"
tar xf "Python-${PYTHON_VERSION}.tar.xz"
cd "Python-${PYTHON_VERSION}"

# Оптимизация для ARMv7
log "Настройка сборки для ARMv7..."
export CFLAGS="-march=armv7-a -mfpu=neon-vfpv4 -mfloat-abi=hard -O2"
export CXXFLAGS="$CFLAGS"

# Настройка и компиляция
log "Настройка и компиляция Python..."
./configure --prefix=/usr/local \
    --enable-optimizations \
    --with-lto \
    --with-system-ffi \
    --enable-loadable-sqlite-extensions

# Ограничение использования ядер для предотвращения перегрева
NUM_CORES=$(nproc)
if [ "$NUM_CORES" -gt 2 ]; then
    MAKE_JOBS=2
else
    MAKE_JOBS=1
fi
log "Использование $MAKE_JOBS ядер для компиляции..."

# Компиляция с ограничением числа процессов
make -j"$MAKE_JOBS"

# Установка
log "Установка Python..."
make altinstall

# Создание символических ссылок
log "Настройка символических ссылок..."
ln -sf /usr/local/bin/python${PYTHON_VERSION%.*} /usr/local/bin/python3
ln -sf /usr/local/bin/pip${PYTHON_VERSION%.*} /usr/local/bin/pip3

# Установка pip и обновление
log "Установка и обновление pip..."
/usr/local/bin/python3 -m pip install --upgrade pip

# Установка необходимых пакетов для веб-интерфейса
log "Установка Flask и необходимых пакетов..."
/usr/local/bin/pip3 install flask flask-login gunicorn

# Очистка
log "Очистка временных файлов..."
cd /
rm -rf "$TMP_DIR"

# Проверка установки
PYTHON_PATH=$(which python3)
PYTHON_VERSION_INSTALLED=$(/usr/local/bin/python3 --version)
PIP_VERSION_INSTALLED=$(/usr/local/bin/pip3 --version)

log "Установка завершена успешно!"
log "Путь к Python: $PYTHON_PATH -> /usr/local/bin/python3"
log "Установленная версия Python: $PYTHON_VERSION_INSTALLED"
log "Установленная версия pip: $PIP_VERSION_INSTALLED"
log "Установлены пакеты: Flask, Flask-Login, Gunicorn"

log "Для запуска веб-интерфейса USB/IP выполните:"
log "  $ cd /путь/к/приложению"
log "  $ python3 main.py"
log "Или с помощью Gunicorn:"
log "  $ gunicorn -b 0.0.0.0:5000 main:app"

log "Веб-интерфейс будет доступен по адресу: http://IP-адрес:5000"
log "Логин: admin, пароль: admin"
