from pydantic import BaseSettings, PostgresDsn, validator
from typing import List, Optional, Dict, Any
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
    DATABASE_URL: Optional[PostgresDsn] = os.getenv("DATABASE_URL")
    
    # URL сервисов
    AGENT_SERVICE_URL: str = os.getenv("AGENT_SERVICE_URL", "http://agent-service:8001")
    GIT_SERVICE_URL: str = os.getenv("GIT_SERVICE_URL", "http://git-service:8004")
    
    class Config:
        case_sensitive = True

settings = Settings()