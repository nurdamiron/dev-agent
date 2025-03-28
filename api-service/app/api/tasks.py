# api-service/app/api/tasks.py

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from app.core.db import get_db
from app.core.security import get_current_active_user
from app.models.user import User
from app.models.task import Task
from app.services.agent_service import AgentService
from pydantic import BaseModel
from typing import List, Optional, Dict, Any
from datetime import datetime

router = APIRouter()

class TaskResponse(BaseModel):
    id: str
    description: str
    status: str
    progress: int
    result: Optional[Dict[str, Any]]
    error: Optional[str]
    project_id: str
    created_at: datetime
    started_at: Optional[datetime]
    completed_at: Optional[datetime]

    class Config:
        orm_mode = True

class TaskStatusUpdate(BaseModel):
    status: str
    progress: int
    result: Optional[Dict[str, Any]] = None
    error: Optional[str] = None

@router.get("", response_model=List[TaskResponse])
def get_tasks(
    project_id: Optional[str] = None,
    status: Optional[str] = None,
    limit: int = 20,
    offset: int = 0,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """Получение списка задач пользователя"""
    query = db.query(Task).filter(Task.user_id == current_user.id)
    
    if project_id:
        query = query.filter(Task.project_id == project_id)
    
    if status:
        query = query.filter(Task.status == status)
    
    # Сортировка по времени создания (сначала новые)
    query = query.order_by(Task.created_at.desc())
    
    # Пагинация
    tasks = query.offset(offset).limit(limit).all()
    
    return tasks

@router.get("/{task_id}", response_model=TaskResponse)
def get_task(
    task_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """Получение информации о задаче"""
    task = db.query(Task).filter(
        Task.id == task_id,
        Task.user_id == current_user.id
    ).first()
    
    if not task:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Задача не найдена"
        )
    
    return task

@router.patch("/{task_id}/status", response_model=TaskResponse)
async def update_task_status(
    task_id: str,
    status_update: TaskStatusUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """Обновление статуса задачи (для внутреннего использования)"""
    task = db.query(Task).filter(Task.id == task_id).first()
    
    if not task:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Задача не найдена"
        )
    
    # Обновляем поля задачи
    task.status = status_update.status
    task.progress = status_update.progress
    
    if status_update.result is not None:
        task.result = status_update.result
    
    if status_update.error is not None:
        task.error = status_update.error
    
    # Обновляем временные метки
    if status_update.status == "in_progress" and task.started_at is None:
        task.started_at = datetime.utcnow()
    
    if status_update.status in ["completed", "failed"]:
        task.completed_at = datetime.utcnow()
    
    db.commit()
    db.refresh(task)
    
    return task

@router.delete("/{task_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_task(
    task_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """Удаление задачи"""
    task = db.query(Task).filter(
        Task.id == task_id,
        Task.user_id == current_user.id
    ).first()
    
    if not task:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Задача не найдена"
        )
    
    db.delete(task)
    db.commit()
    
    return None