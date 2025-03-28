from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks
from app.core.security import get_current_user
from app.models.user import User
from app.models.message import MessageRequest, MessageResponse
from app.services.agent_service import AgentService
import logging

logger = logging.getLogger(__name__)
router = APIRouter()

@router.post("", response_model=MessageResponse)
async def send_message(
    request: MessageRequest,
    background_tasks: BackgroundTasks,
    current_user: User = Depends(get_current_user)
):
    """
    Обработка сообщения от пользователя.
    """
    logger.info(f"Получено сообщение от пользователя {current_user.email}: {request.message[:50]}...")
    
    try:
        # Создаем сервис агента
        agent_service = AgentService()
        
        # Вызываем сервис агента
        response = await agent_service.process_message(
            user_id=current_user.id,
            message=request.message,
            project_id=request.projectId,
            context=request.context
        )
        
        # Если создана задача, запускаем ее обработку в фоновом режиме
        if response.get("task"):
            task_id = response["task"]["id"]
            background_tasks.add_task(agent_service.track_task, task_id)
        
        return response
    except Exception as e:
        logger.error(f"Ошибка обработки сообщения: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Внутренняя ошибка сервера: {str(e)}")