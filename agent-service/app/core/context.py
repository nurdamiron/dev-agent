# agent-service/app/core/context.py

import logging
from typing import Dict, List, Any, Optional, Set
import json
import os
from pathlib import Path
import httpx
from app.core.config import settings

logger = logging.getLogger(__name__)

class ProjectContext:
    """
    Класс для управления контекстом проекта.
    Хранит и обрабатывает информацию о проектах, их файлах и контексте.
    """
    
    def __init__(self):
        """Инициализация контекста проекта."""
        self.contexts = {}  # Словарь для хранения контекстов проектов
        self.context_cache_dir = Path("cache/contexts")
        
        # Создаем директорию для кэширования контекстов, если не существует
        os.makedirs(self.context_cache_dir, exist_ok=True)
        
        logger.info("ProjectContext инициализирован")
    
    async def get_project_context(self, project_id: str) -> Dict[str, Any]:
        """
        Получает контекст проекта.
        
        Args:
            project_id: Идентификатор проекта
            
        Returns:
            Dict с контекстом проекта
        """
        # Проверяем, есть ли контекст в кэше
        if project_id in self.contexts:
            logger.info(f"Контекст проекта {project_id} найден в кэше")
            return self.contexts[project_id]
        
        # Проверяем, есть ли контекст в файловом кэше
        cache_file = self.context_cache_dir / f"{project_id}.json"
        if cache_file.exists():
            try:
                with open(cache_file, "r", encoding="utf-8") as f:
                    context = json.load(f)
                    self.contexts[project_id] = context
                    logger.info(f"Контекст проекта {project_id} загружен из файла")
                    return context
            except Exception as e:
                logger.error(f"Ошибка при загрузке контекста из файла: {str(e)}")
        
        # Если контекста нет в кэше, запрашиваем его из API Service
        try:
            context = await self._fetch_project_context(project_id)
            
            # Сохраняем контекст в кэш
            self.contexts[project_id] = context
            
            # Сохраняем контекст в файл
            with open(cache_file, "w", encoding="utf-8") as f:
                json.dump(context, f)
            
            logger.info(f"Контекст проекта {project_id} получен из API и сохранен в кэш")
            return context
        
        except Exception as e:
            logger.error(f"Ошибка при получении контекста проекта {project_id}: {str(e)}")
            return {"project_id": project_id, "error": str(e)}
    
    async def update_project_context(self, project_id: str, updates: Dict[str, Any]) -> Dict[str, Any]:
        """
        Обновляет контекст проекта.
        
        Args:
            project_id: Идентификатор проекта
            updates: Словарь с обновлениями для контекста
            
        Returns:
            Dict с обновленным контекстом проекта
        """
        # Получаем текущий контекст
        context = await self.get_project_context(project_id)
        
        # Обновляем контекст
        context.update(updates)
        
        # Сохраняем контекст в кэш
        self.contexts[project_id] = context
        
        # Сохраняем контекст в файл
        cache_file = self.context_cache_dir / f"{project_id}.json"
        with open(cache_file, "w", encoding="utf-8") as f:
            json.dump(context, f)
        
        logger.info(f"Контекст проекта {project_id} обновлен")
        return context
    
    async def clear_project_context(self, project_id: str) -> bool:
        """
        Очищает контекст проекта.
        
        Args:
            project_id: Идентификатор проекта
            
        Returns:
            bool: True, если контекст успешно очищен
        """
        # Удаляем контекст из кэша
        if project_id in self.contexts:
            del self.contexts[project_id]
        
        # Удаляем файл контекста
        cache_file = self.context_cache_dir / f"{project_id}.json"
        if cache_file.exists():
            try:
                os.remove(cache_file)
                logger.info(f"Контекст проекта {project_id} очищен")
                return True
            except Exception as e:
                logger.error(f"Ошибка при удалении файла контекста: {str(e)}")
                return False
        
        return True
    
    async def _fetch_project_context(self, project_id: str) -> Dict[str, Any]:
        """
        Запрашивает контекст проекта из API Service.
        
        Args:
            project_id: Идентификатор проекта
            
        Returns:
            Dict с контекстом проекта
        """
        try:
            async with httpx.AsyncClient() as client:
                # Получаем информацию о проекте
                response = await client.get(
                    f"{settings.API_SERVICE_URL}/projects/{project_id}",
                    timeout=10.0
                )
                
                if response.status_code != 200:
                    logger.error(f"Ошибка при получении информации о проекте: {response.text}")
                    raise ValueError(f"Ошибка получения информации о проекте: {response.status_code}")
                
                project_info = response.json()
                
                # Если у проекта есть репозиторий, получаем информацию о нем
                repo_info = {}
                if project_info.get("repository_url"):
                    # Если есть Git Service, запрашиваем у него информацию о репозитории
                    if settings.GIT_SERVICE_URL:
                        repo_response = await client.get(
                            f"{settings.GIT_SERVICE_URL}/repos/analyze",
                            params={"url": project_info["repository_url"]},
                            timeout=30.0
                        )
                        
                        if repo_response.status_code == 200:
                            repo_info = repo_response.json()
                
                # Формируем контекст проекта
                context = {
                    "project": project_info,
                    "repository": repo_info
                }
                
                return context
        
        except Exception as e:
            logger.error(f"Ошибка при запросе к API Service: {str(e)}")
            raise ValueError(f"Не удалось получить контекст проекта: {str(e)}")