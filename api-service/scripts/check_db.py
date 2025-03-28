# api-service/scripts/check_db.py

import sys
import os
from pathlib import Path

# Добавляем корневую директорию в sys.path, чтобы импорты работали корректно
sys.path.append(str(Path(__file__).parent.parent))

from app.core.db import engine
from sqlalchemy import text
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def check_db_connection():
    """
    Проверяет подключение к базе данных.
    """
    try:
        with engine.connect() as connection:
            result = connection.execute(text("SELECT 1"))
            logger.info("✅ Подключение к базе данных успешно")
            return True
    except Exception as e:
        logger.error(f"❌ Ошибка подключения к базе данных: {str(e)}")
        return False

if __name__ == "__main__":
    success = check_db_connection()
    if not success:
        sys.exit(1)