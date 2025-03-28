# api-service/app/db_init.py
from app.core.db import Base, engine
from app.models.user import User
from app.models.project import Project
from app.models.task import Task
from app.models.message import Message
import logging

logger = logging.getLogger(__name__)

def init_db():
    logger.info("Создание таблиц в базе данных...")
    # Создаем все таблицы
    Base.metadata.create_all(bind=engine)
    logger.info("Таблицы успешно созданы")

if __name__ == "__main__":
    init_db()