from pydantic import BaseSettings, validator
from typing import List, Optional
import os
from dotenv import load_dotenv

# Загрузка переменных окружения из .env файла
load_dotenv()

class Settings(BaseSettings):
    # Основные настройки приложения
    PROJECT_NAME: str = "DevAgent API"
    API_V1_STR: str = "/api/v1"
    
    # CORS настройки
    CORS_ORIGINS: List[str] = ["*"]
    
    # JWT настройки
    JWT_SECRET: str = os.getenv("JWT_SECRET", "secret_key_change_in_production")
    JWT_ALGORITHM: str = "HS256"
    JWT_ACCESS_TOKEN_EXPIRE_MINUTES: int = 60 * 24 * 7  # 7 дней
    
    # Настройки базы данных
    DATABASE_URL: Optional[str] = os.getenv("DATABASE_URL")
    MYSQL_USER: Optional[str] = os.getenv("MYSQL_USER")
    MYSQL_PASSWORD: Optional[str] = os.getenv("MYSQL_PASSWORD")
    MYSQL_HOST: Optional[str] = os.getenv("MYSQL_HOST")
    MYSQL_PORT: Optional[str] = os.getenv("MYSQL_PORT", "3306")
    MYSQL_DB: Optional[str] = os.getenv("MYSQL_DB")
    
    # URL сервисов
    AGENT_SERVICE_URL: str = os.getenv("AGENT_SERVICE_URL", "http://agent-service:8001")
    GIT_SERVICE_URL: str = os.getenv("GIT_SERVICE_URL", "http://git-service:8004")
    
    @validator("DATABASE_URL", pre=True)
    def validate_db_url(cls, v, values):
        if v:
            return v
        # Проверяем, есть ли все необходимые параметры для MySQL
        if all(values.get(key) for key in ["MYSQL_USER", "MYSQL_PASSWORD", "MYSQL_HOST", "MYSQL_DB"]):
            port = values.get("MYSQL_PORT", "3306")
            return f"mysql+pymysql://{values['MYSQL_USER']}:{values['MYSQL_PASSWORD']}@{values['MYSQL_HOST']}:{port}/{values['MYSQL_DB']}"
        return v
    
    class Config:
        case_sensitive = True

settings = Settings()