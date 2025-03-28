# api-service/scripts/init_db.py

import sys
import os
from pathlib import Path

# Добавляем корневую директорию в sys.path, чтобы импорты работали корректно
sys.path.append(str(Path(__file__).parent.parent))

from app.core.db import Base, engine
from app.models.user import User
from app.models.project import Project
from app.models.task import Task
from app.models.message import Message
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def init_db():
    logger.info("Создание таблиц в базе данных MySQL...")
    
    # Создаем все таблицы
    Base.metadata.create_all(bind=engine)
    
    logger.info("Таблицы успешно созданы")
    
    # Проверка создания таблиц
    from sqlalchemy import inspect
    inspector = inspect(engine)
    tables = inspector.get_table_names()
    logger.info(f"Созданные таблицы: {', '.join(tables)}")

if __name__ == "__main__":
    init_db()