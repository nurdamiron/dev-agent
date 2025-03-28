# api-service/app/api/messages.py

from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks, status
from sqlalchemy.orm import Session
from app.core.db import get_db
from app.core.security import get_current_active_user
from app.models.user import User
from app.models.message import Message, MessageRequest, MessageResponse
from app.services.agent_service import AgentService
from typing import List, Optional
import logging

logger = logging.getLogger(__name__)
router = APIRouter()

@router.post("", response_model=MessageResponse)
async def send_message(
    request: MessageRequest,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """
    Обработка сообщения от пользователя.
    """
    logger.info(f"Получено сообщение от пользователя {current_user.email}: {request.message[:50]}...")
    
    try:
        # Создаем новое сообщение в БД
        db_message = Message(
            content=request.message,
            role="user",
            user_id=current_user.id,
            meta={"project_id": request.projectId} if request.projectId else None
        )
        
        db.add(db_message)
        db.commit()
        db.refresh(db_message)
        
        # Создаем сервис агента
        agent_service = AgentService()
        
        # Вызываем сервис агента
        response = await agent_service.process_message(
            user_id=current_user.id,
            message=request.message,
            project_id=request.projectId,
            context=request.context
        )
        
        # Создаем сообщение с ответом агента
        assistant_message = Message(
            content=response.get("message", ""),
            role="assistant",
            user_id=current_user.id,
            meta=response.get("meta"),
            task_id=response.get("task", {}).get("id") if response.get("task") else None
        )
        
        db.add(assistant_message)
        db.commit()
        
        # Если создана задача, запускаем ее обработку в фоновом режиме
        if response.get("task"):
            task_id = response["task"]["id"]
            background_tasks.add_task(agent_service.track_task, task_id)
        
        return response
    
    except Exception as e:
        logger.error(f"Ошибка обработки сообщения: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Внутренняя ошибка сервера: {str(e)}")

@router.get("", response_model=List[MessageResponse])
async def get_messages(
    project_id: Optional[str] = None,
    limit: int = 50,
    offset: int = 0,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """
    Получение истории сообщений пользователя.
    """
    query = db.query(Message).filter(Message.user_id == current_user.id)
    
    if project_id:
        # Фильтрация по проекту (предполагаем, что project_id хранится в meta)
        query = query.filter(Message.meta.contains({"project_id": project_id}))
    
    # Сортировка по времени создания (сначала новые)
    query = query.order_by(Message.created_at.desc())
    
    # Пагинация
    messages = query.offset(offset).limit(limit).all()
    
    # Преобразуем сообщения в формат ответа
    result = []
    for msg in messages:
        task = None
        if msg.task_id:
            # Получаем информацию о задаче, если она связана с сообщением
            # Это упрощенно, возможно, потребуется запрос к таблице задач
            task = {"id": msg.task_id}
        
        result.append({
            "message": msg.content,
            "meta": msg.meta,
            "task": task
        })
    
    return result