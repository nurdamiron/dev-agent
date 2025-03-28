# agent-service/app/main.py

import uvicorn
import logging
from fastapi import FastAPI, HTTPException, Depends, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Dict, Any, Optional, List
import os

from app.core.config import settings
from app.core.agent import DevAgent
from app.tasks.executor import TaskExecutor
from app.tasks.queue import TaskQueue

# Настройка логирования
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Инициализация FastAPI приложения
app = FastAPI(
    title="DevAgent Service",
    description="AI-агент разработчика на базе Claude",
    version="1.0.0"
)

# Настройка CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # В продакшене лучше указать конкретные домены
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Модели данных
class MessageRequest(BaseModel):
    user_id: str
    message: str
    project_id: Optional[str] = None
    context: Optional[Dict[str, Any]] = None

class TaskStatusUpdate(BaseModel):
    status: str
    progress: int
    result: Optional[Dict[str, Any]] = None
    error: Optional[str] = None

# Инициализация сервисов
dev_agent = DevAgent()
task_queue = TaskQueue()

@app.on_event("startup")
async def startup_event():
    logger.info("Запуск API сервиса AI-агента разработчика")
    logger.info(f"Версия Claude API: {settings.CLAUDE_API_MODEL}")

@app.get("/health")
async def health_check():
    """Проверка состояния сервиса."""
    return {"status": "ok"}

@app.post("/process")
async def process_message(request: MessageRequest, background_tasks: BackgroundTasks):
    """
    Обрабатывает сообщение от пользователя и возвращает ответ.
    Для длительных операций создает фоновую задачу.
    """
    logger.info(f"Получено сообщение от пользователя {request.user_id}")
    
    try:
        # Создаем контекст проекта
        project_context = None
        if request.project_id:
            project_context = {"project_id": request.project_id}
            if request.context:
                project_context.update(request.context)
        
        # Обрабатываем сообщение через агента
        response = await dev_agent.process_message(
            user_id=request.user_id,
            message=request.message,
            project_context=project_context
        )
        
        return response
    
    except Exception as e:
        logger.error(f"Ошибка при обработке сообщения: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/tasks/{task_id}")
async def get_task_status(task_id: str):
    """
    Возвращает текущий статус задачи.
    """
    task = await task_queue.get_task_by_id(task_id)
    
    if not task:
        raise HTTPException(status_code=404, detail="Задача не найдена")
    
    return task

@app.patch("/tasks/{task_id}/status")
async def update_task_status(task_id: str, update: TaskStatusUpdate):
    """
    Обновляет статус задачи (используется внутренними процессами).
    """
    success = await task_queue.update_task(task_id, update.dict(exclude_unset=True))
    
    if not success:
        raise HTTPException(status_code=404, detail="Задача не найдена")
    
    return {"status": "updated"}

@app.get("/tasks")
async def list_tasks(status: Optional[str] = None):
    """
    Возвращает список всех задач с опциональной фильтрацией по статусу.
    """
    tasks = await task_queue.list_tasks(status)
    return tasks

if __name__ == "__main__":
    uvicorn.run(
        "app.main:app",
        host="0.0.0.0",
        port=int(os.getenv("PORT", "8001")),
        reload=True
    )