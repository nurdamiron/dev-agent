# api-service/scripts/create_admin.py

import sys
import os
from pathlib import Path

# Добавляем корневую директорию в sys.path, чтобы импорты работали корректно
sys.path.append(str(Path(__file__).parent.parent))

from app.core.db import get_db, Base, engine
from app.models.user import User
from app.core.security import get_password_hash
import logging
import uuid

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def create_admin_user(username: str, email: str, password: str):
    """
    Создает администратора в базе данных.
    
    Args:
        username: Имя пользователя
        email: Email пользователя
        password: Пароль пользователя
    """
    logger.info(f"Создание администратора с именем {username}...")
    
    # Создаем таблицы, если они не существуют
    Base.metadata.create_all(bind=engine)
    
    # Получаем сессию БД
    db = next(get_db())
    
    try:
        # Проверяем, существует ли пользователь с таким email
        existing_user = db.query(User).filter(User.email == email).first()
        if existing_user:
            logger.info(f"Пользователь с email {email} уже существует.")
            return
        
        # Создаем нового пользователя-администратора
        hashed_password = get_password_hash(password)
        admin_user = User(
            id=str(uuid.uuid4()),
            email=email,
            username=username,
            hashed_password=hashed_password,
            is_active=True,
            is_superuser=True
        )
        
        db.add(admin_user)
        db.commit()
        logger.info(f"Администратор {username} успешно создан.")
    
    except Exception as e:
        db.rollback()
        logger.error(f"Ошибка при создании администратора: {str(e)}")
    
    finally:
        db.close()

if __name__ == "__main__":
    # Проверяем аргументы командной строки
    if len(sys.argv) != 4:
        print("Использование: python create_admin.py <username> <email> <password>")
        sys.exit(1)
    
    username = sys.argv[1]
    email = sys.argv[2]
    password = sys.argv[3]
    
    create_admin_user(username, email, password)