# agent-service/app/core/config.py

import os
from pydantic import BaseSettings, validator
from typing import Optional, List
from dotenv import load_dotenv

# Загрузка переменных окружения из .env файла
load_dotenv()

class Settings(BaseSettings):
    # Настройки API и сервера
    PORT: int = int(os.getenv("PORT", "8001"))
    HOST: str = os.getenv("HOST", "0.0.0.0")
    
    # Настройки Claude API
    CLAUDE_API_KEY: Optional[str] = os.getenv("CLAUDE_API_KEY")
    CLAUDE_API_MODEL: str = os.getenv("CLAUDE_API_MODEL", "claude-3-7-sonnet-20250219")
    
    # URL других сервисов
    API_SERVICE_URL: str = os.getenv("API_SERVICE_URL", "http://localhost:8000")
    GIT_SERVICE_URL: str = os.getenv("GIT_SERVICE_URL", "http://localhost:8004")
    
    # Redis настройки
    REDIS_URL: str = os.getenv("REDIS_URL", "redis://localhost:6379/0")
    
    # Директории промптов и ресурсов
    PROMPTS_DIR: str = os.getenv("PROMPTS_DIR", "prompts")
    
    # Настройки логирования
    LOG_LEVEL: str = os.getenv("LOG_LEVEL", "INFO")
    
    # Валидация обязательных полей
    @validator("CLAUDE_API_KEY", pre=True)
    def validate_claude_api_key(cls, v):
        if not v:
            raise ValueError("CLAUDE_API_KEY не настроен. Укажите его в .env файле или переменных окружения.")
        return v
    
    class Config:
        env_file = ".env"
        case_sensitive = True

# Создаем экземпляр настроек
settings = Settings()