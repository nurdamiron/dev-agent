# agent-service/app/tasks/queue.py

import logging
import asyncio
import json
from typing import Dict, Any, Optional, List
import redis.asyncio as redis
from app.core.config import settings

logger = logging.getLogger(__name__)

class TaskQueue:
    """
    Класс для управления очередью задач с использованием Redis.
    """
    
    def __init__(self):
        """Инициализация очереди задач."""
        self.redis_url = settings.REDIS_URL
        self.task_queue_key = "agent:tasks:queue"
        self.task_data_key_prefix = "agent:tasks:data:"
        
        # Подключение к Redis будет происходить при первом вызове метода
        self._redis_client = None
        
        logger.info("TaskQueue инициализирован с Redis URL: {self.redis_url}")
    
    async def _get_redis(self) -> redis.Redis:
        """
        Получает клиент Redis с ленивой инициализацией.
        
        Returns:
            Клиент Redis
        """
        if self._redis_client is None:
            logger.info("Создание подключения к Redis")
            self._redis_client = redis.from_url(self.redis_url)
        
        return self._redis_client
    
    async def add_task(self, task: Dict[str, Any]) -> bool:
        """
        Добавляет задачу в очередь.
        
        Args:
            task: Словарь с информацией о задаче
            
        Returns:
            bool: True, если задача успешно добавлена
        """
        if not task or "id" not in task:
            logger.error("Попытка добавить некорректную задачу в очередь")
            return False
        
        try:
            client = await self._get_redis()
            
            # Сохраняем детальную информацию о задаче
            task_data_key = f"{self.task_data_key_prefix}{task['id']}"
            await client.set(task_data_key, json.dumps(task))
            
            # Добавляем ID задачи в очередь
            await client.lpush(self.task_queue_key, task['id'])
            
            logger.info(f"Задача {task['id']} добавлена в очередь")
            return True
        
        except Exception as e:
            logger.error(f"Ошибка при добавлении задачи в очередь: {str(e)}")
            return False
    
    async def get_task(self) -> Optional[Dict[str, Any]]:
        """
        Получает следующую задачу из очереди.
        
        Returns:
            Dict с информацией о задаче или None, если очередь пуста
        """
        try:
            client = await self._get_redis()
            
            # Извлекаем ID задачи из очереди (блокирующая операция с таймаутом)
            result = await client.brpop(self.task_queue_key, timeout=1)
            
            if not result:
                return None
            
            # Получаем ID задачи из результата
            _, task_id = result
            task_id = task_id.decode('utf-8')
            
            # Получаем детальную информацию о задаче
            task_data_key = f"{self.task_data_key_prefix}{task_id}"
            task_data = await client.get(task_data_key)
            
            if not task_data:
                logger.warning(f"Не найдены данные для задачи {task_id}")
                return None
            
            # Преобразуем JSON-строку в словарь
            task = json.loads(task_data.decode('utf-8'))
            
            logger.info(f"Получена задача {task_id} из очереди")
            return task
        
        except Exception as e:
            logger.error(f"Ошибка при получении задачи из очереди: {str(e)}")
            return None
    
    async def update_task(self, task_id: str, updates: Dict[str, Any]) -> bool:
        """
        Обновляет информацию о задаче.
        
        Args:
            task_id: Идентификатор задачи
            updates: Словарь с обновлениями для задачи
            
        Returns:
            bool: True, если задача успешно обновлена
        """
        try:
            client = await self._get_redis()
            
            # Получаем текущую информацию о задаче
            task_data_key = f"{self.task_data_key_prefix}{task_id}"
            task_data = await client.get(task_data_key)
            
            if not task_data:
                logger.warning(f"Не найдены данные для задачи {task_id} при обновлении")
                return False
            
            # Преобразуем JSON-строку в словарь
            task = json.loads(task_data.decode('utf-8'))
            
            # Обновляем информацию о задаче
            task.update(updates)
            
            # Сохраняем обновленную информацию
            await client.set(task_data_key, json.dumps(task))
            
            logger.info(f"Задача {task_id} обновлена")
            return True
        
        except Exception as e:
            logger.error(f"Ошибка при обновлении задачи: {str(e)}")
            return False
    
    async def get_task_by_id(self, task_id: str) -> Optional[Dict[str, Any]]:
        """
        Получает информацию о задаче по ID.
        
        Args:
            task_id: Идентификатор задачи
            
        Returns:
            Dict с информацией о задаче или None, если задача не найдена
        """
        try:
            client = await self._get_redis()
            
            # Получаем информацию о задаче
            task_data_key = f"{self.task_data_key_prefix}{task_id}"
            task_data = await client.get(task_data_key)
            
            if not task_data:
                logger.warning(f"Не найдены данные для задачи {task_id}")
                return None
            
            # Преобразуем JSON-строку в словарь
            task = json.loads(task_data.decode('utf-8'))
            
            return task
        
        except Exception as e:
            logger.error(f"Ошибка при получении задачи по ID: {str(e)}")
            return None
    
    async def delete_task(self, task_id: str) -> bool:
        """
        Удаляет информацию о задаче.
        
        Args:
            task_id: Идентификатор задачи
            
        Returns:
            bool: True, если задача успешно удалена
        """
        try:
            client = await self._get_redis()
            
            # Удаляем информацию о задаче
            task_data_key = f"{self.task_data_key_prefix}{task_id}"
            result = await client.delete(task_data_key)
            
            logger.info(f"Задача {task_id} удалена, результат: {result}")
            return result > 0
        
        except Exception as e:
            logger.error(f"Ошибка при удалении задачи: {str(e)}")
            return False
    
    async def list_tasks(self, status: Optional[str] = None) -> List[Dict[str, Any]]:
        """
        Получает список всех задач, опционально фильтруя по статусу.
        
        Args:
            status: Опциональный фильтр по статусу задачи
            
        Returns:
            Список словарей с информацией о задачах
        """
        try:
            client = await self._get_redis()
            
            # Получаем ключи всех задач
            keys = await client.keys(f"{self.task_data_key_prefix}*")
            
            tasks = []
            
            # Получаем данные для каждой задачи
            for key in keys:
                task_data = await client.get(key)
                if task_data:
                    task = json.loads(task_data.decode('utf-8'))
                    
                    # Фильтруем по статусу, если указан
                    if status is None or task.get('status') == status:
                        tasks.append(task)
            
            return tasks
        
        except Exception as e:
            logger.error(f"Ошибка при получении списка задач: {str(e)}")
            return []