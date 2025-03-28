# api-service/app/models/message.py

from sqlalchemy import Column, String, DateTime, Text, ForeignKey, JSON
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from app.core.db import Base
from pydantic import BaseModel
from typing import Optional, Dict, Any, List
import uuid

# SQLAlchemy модель для базы данных
class Message(Base):
    __tablename__ = "messages"

    id = Column(String(36), primary_key=True, index=True, default=lambda: str(uuid.uuid4()))
    content = Column(Text, nullable=False)
    role = Column(String(20), nullable=False)  # user, assistant, system
    meta = Column(JSON, nullable=True)  # Дополнительные данные
    
    task_id = Column(String(36), ForeignKey("tasks.id", ondelete="CASCADE"), nullable=True)
    user_id = Column(String(36), ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    
    # Отношения
    task = relationship("Task", back_populates="messages")
    user = relationship("User", back_populates="messages")

# Pydantic модели для API
class MessageRequest(BaseModel):
    message: str
    projectId: Optional[str] = None
    context: Optional[Dict[str, Any]] = None

class MessageResponse(BaseModel):
    message: str
    meta: Optional[Dict[str, Any]] = None
    task: Optional[Dict[str, Any]] = None

    class Config:
        orm_mode = True