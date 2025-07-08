import os

# Настройка конфигурации базы данных перед импортом app
database_url = os.environ.get("DATABASE_URL")
if database_url:
    # PostgreSQL конфигурация для продакшена
    os.environ['USE_POSTGRESQL'] = 'true'
else:
    # SQLite конфигурация для разработки
    os.environ['USE_POSTGRESQL'] = 'false'

from app import app

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)
