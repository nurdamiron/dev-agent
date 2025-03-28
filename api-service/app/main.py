# api-service/app/main.py

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import logging
from app.core.config import settings
from app.api import auth, messages, projects, tasks

# Настройка логирования
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Инициализация приложения FastAPI
app = FastAPI(
    title=settings.PROJECT_NAME,
    description="API сервис для AI-агента разработчика",
    version="1.0.0"
)

# Настройка CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Подключение маршрутов
app.include_router(auth.router, prefix="/auth", tags=["authentication"])
app.include_router(messages.router, prefix="/messages", tags=["messages"])
app.include_router(projects.router, prefix="/projects", tags=["projects"])
app.include_router(tasks.router, prefix="/tasks", tags=["tasks"])

@app.get("/health")
async def health_check():
    """
    Проверка состояния сервиса.
    """
    return {"status": "ok"}

@app.get("/db-test")
async def db_test():
    """
    Проверка соединения с базой данных.
    """
    try:
        from sqlalchemy import text
        from app.core.db import engine
        
        with engine.connect() as connection:
            result = connection.execute(text("SELECT 1"))
            return {"status": "ok", "message": "Подключение к базе данных успешно"}
    except Exception as e:
        return {"status": "error", "message": f"Ошибка подключения к базе данных: {str(e)}"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)