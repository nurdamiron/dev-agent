# agent-service/app/services/agent_service.py

import logging
import httpx
from typing import Dict, Any, Optional
from app.core.config import settings

logger = logging.getLogger(__name__)

class AgentService:
    """
    Класс для взаимодействия с API Service.
    """
    
    def __init__(self):
        """Инициализация сервиса."""
        self.api_url = settings.API_SERVICE_URL
        logger.info(f"AgentService инициализирован с URL: {self.api_url}")
    
    async def track_task(self, task_id: str):
        """
        Отслеживает выполнение задачи и обновляет её статус в API Service.
        
        Args:
            task_id: Идентификатор задачи
        """
        logger.info(f"Отслеживание задачи {task_id}")
        
        try:
            # Получаем информацию о задаче
            task = await self._get_task(task_id)
            
            if not task or task.get("status") in ["completed", "failed"]:
                return
            
            # Обновляем статус задачи на "in_progress"
            await self._update_task_status(task_id, {
                "status": "in_progress",
                "progress": 10
            })
            
            # Здесь будет логика отслеживания задачи и обновления её статуса
            # ...
            
        except Exception as e:
            logger.error(f"Ошибка при отслеживании задачи {task_id}: {str(e)}")
            
            # Обновляем статус задачи на "failed"
            await self._update_task_status(task_id, {
                "status": "failed",
                "progress": 0,
                "error": str(e)
            })
    
    async def _get_task(self, task_id: str) -> Optional[Dict[str, Any]]:
        """
        Получает информацию о задаче из API Service.
        
        Args:
            task_id: Идентификатор задачи
            
        Returns:
            Dict с информацией о задаче или None, если задача не найдена
        """
        try:
            async with httpx.AsyncClient() as client:
                response = await client.get(
                    f"{self.api_url}/tasks/{task_id}",
                    timeout=10.0
                )
                
                if response.status_code == 200:
                    return response.json()
                else:
                    logger.error(f"Ошибка при получении задачи {task_id}: {response.text}")
                    return None
        
        except Exception as e:
            logger.error(f"Ошибка при запросе к API Service: {str(e)}")
            return None
    
    async def _update_task_status(self, task_id: str, status_update: Dict[str, Any]) -> bool:
        """
        Обновляет статус задачи в API Service.
        
        Args:
            task_id: Идентификатор задачи
            status_update: Словарь с обновлениями для задачи
            
        Returns:
            bool: True, если задача успешно обновлена
        """
        try:
            async with httpx.AsyncClient() as client:
                response = await client.patch(
                    f"{self.api_url}/tasks/{task_id}/status",
                    json=status_update,
                    timeout=10.0
                )
                
                if response.status_code == 200:
                    return True
                else:
                    logger.error(f"Ошибка при обновлении задачи {task_id}: {response.text}")
                    return False
        
        except Exception as e:
            logger.error(f"Ошибка при запросе к API Service: {str(e)}")
            return False