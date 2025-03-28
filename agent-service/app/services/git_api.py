# agent-service/app/services/git_api.py

import logging
import os
import httpx
import json
from typing import Dict, List, Any, Optional
from pathlib import Path
from app.core.config import settings

logger = logging.getLogger(__name__)

class GitAPI:
    """
    Класс для взаимодействия с Git API через Git Service.
    """
    
    def __init__(self):
        """Инициализация Git API."""
        self.git_service_url = settings.GIT_SERVICE_URL
        logger.info(f"GitAPI инициализирован с URL: {self.git_service_url}")
    
    async def clone_repository(self, repo_url: str, branch: Optional[str] = None) -> Dict[str, Any]:
        """
        Клонирует репозиторий через Git Service.
        
        Args:
            repo_url: URL репозитория
            branch: Ветка для клонирования (опционально)
            
        Returns:
            Dict с информацией о клонированном репозитории
        """
        logger.info(f"Клонирование репозитория: {repo_url}, ветка: {branch or 'default'}")
        
        try:
            # Формируем параметры запроса
            params = {"url": repo_url}
            if branch:
                params["branch"] = branch
            
            # Отправляем запрос к Git Service
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    f"{self.git_service_url}/repos/clone",
                    params=params,
                    timeout=60.0
                )
                
                if response.status_code != 200:
                    logger.error(f"Ошибка при клонировании репозитория: {response.text}")
                    raise ValueError(f"Ошибка клонирования репозитория: {response.status_code}")
                
                result = response.json()
                logger.info(f"Репозиторий успешно клонирован: {result.get('repo_id')}")
                return result
        
        except Exception as e:
            logger.error(f"Ошибка при клонировании репозитория: {str(e)}")
            raise ValueError(f"Не удалось клонировать репозиторий: {str(e)}")
    
    async def get_repository_info(self, repo_id: str) -> Dict[str, Any]:
        """
        Получает информацию о репозитории.
        
        Args:
            repo_id: Идентификатор репозитория
            
        Returns:
            Dict с информацией о репозитории
        """
        logger.info(f"Получение информации о репозитории: {repo_id}")
        
        try:
            # Отправляем запрос к Git Service
            async with httpx.AsyncClient() as client:
                response = await client.get(
                    f"{self.git_service_url}/repos/{repo_id}",
                    timeout=10.0
                )
                
                if response.status_code != 200:
                    logger.error(f"Ошибка при получении информации о репозитории: {response.text}")
                    raise ValueError(f"Ошибка получения информации о репозитории: {response.status_code}")
                
                result = response.json()
                return result
        
        except Exception as e:
            logger.error(f"Ошибка при получении информации о репозитории: {str(e)}")
            raise ValueError(f"Не удалось получить информацию о репозитории: {str(e)}")
    
    async def get_file_content(self, repo_id: str, file_path: str) -> Dict[str, Any]:
        """
        Получает содержимое файла из репозитория.
        
        Args:
            repo_id: Идентификатор репозитория
            file_path: Путь к файлу в репозитории
            
        Returns:
            Dict с содержимым файла и информацией о нём
        """
        logger.info(f"Получение содержимого файла: {file_path} из репозитория: {repo_id}")
        
        try:
            # Отправляем запрос к Git Service
            async with httpx.AsyncClient() as client:
                response = await client.get(
                    f"{self.git_service_url}/repos/{repo_id}/files",
                    params={"path": file_path},
                    timeout=10.0
                )
                
                if response.status_code != 200:
                    logger.error(f"Ошибка при получении содержимого файла: {response.text}")
                    raise ValueError(f"Ошибка получения содержимого файла: {response.status_code}")
                
                result = response.json()
                return result
        
        except Exception as e:
            logger.error(f"Ошибка при получении содержимого файла: {str(e)}")
            raise ValueError(f"Не удалось получить содержимое файла: {str(e)}")
    
    async def list_files(self, repo_id: str, path: str = "") -> List[Dict[str, Any]]:
        """
        Получает список файлов в репозитории или директории.
        
        Args:
            repo_id: Идентификатор репозитория
            path: Путь к директории (опционально)
            
        Returns:
            List с информацией о файлах
        """
        logger.info(f"Получение списка файлов из репозитория: {repo_id}, путь: {path or 'root'}")
        
        try:
            # Отправляем запрос к Git Service
            async with httpx.AsyncClient() as client:
                params = {}
                if path:
                    params["path"] = path
                
                response = await client.get(
                    f"{self.git_service_url}/repos/{repo_id}/list",
                    params=params,
                    timeout=10.0
                )
                
                if response.status_code != 200:
                    logger.error(f"Ошибка при получении списка файлов: {response.text}")
                    raise ValueError(f"Ошибка получения списка файлов: {response.status_code}")
                
                result = response.json()
                return result.get("files", [])
        
        except Exception as e:
            logger.error(f"Ошибка при получении списка файлов: {str(e)}")
            raise ValueError(f"Не удалось получить список файлов: {str(e)}")
    
    async def commit_changes(self, repo_id: str, message: str, changes: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Коммитит изменения в репозиторий.
        
        Args:
            repo_id: Идентификатор репозитория
            message: Сообщение коммита
            changes: Список изменений (словари с path, content, action)
            
        Returns:
            Dict с информацией о коммите
        """
        logger.info(f"Коммит изменений в репозиторий: {repo_id}, сообщение: {message}")
        
        try:
            # Формируем данные для запроса
            data = {
                "message": message,
                "changes": changes
            }
            
            # Отправляем запрос к Git Service
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    f"{self.git_service_url}/repos/{repo_id}/commit",
                    json=data,
                    timeout=30.0
                )
                
                if response.status_code != 200:
                    logger.error(f"Ошибка при коммите изменений: {response.text}")
                    raise ValueError(f"Ошибка коммита изменений: {response.status_code}")
                
                result = response.json()
                logger.info(f"Изменения успешно закоммичены: {result.get('commit_id')}")
                return result
        
        except Exception as e:
            logger.error(f"Ошибка при коммите изменений: {str(e)}")
            raise ValueError(f"Не удалось закоммитить изменения: {str(e)}")
    
    async def push_changes(self, repo_id: str, branch: str = "main") -> Dict[str, Any]:
        """
        Пушит изменения в удаленный репозиторий.
        
        Args:
            repo_id: Идентификатор репозитория
            branch: Ветка для пуша
            
        Returns:
            Dict с информацией о пуше
        """
        logger.info(f"Пуш изменений в репозиторий: {repo_id}, ветка: {branch}")
        
        try:
            # Формируем данные для запроса
            data = {
                "branch": branch
            }
            
            # Отправляем запрос к Git Service
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    f"{self.git_service_url}/repos/{repo_id}/push",
                    json=data,
                    timeout=30.0
                )
                
                if response.status_code != 200:
                    logger.error(f"Ошибка при пуше изменений: {response.text}")
                    raise ValueError(f"Ошибка пуша изменений: {response.status_code}")
                
                result = response.json()
                logger.info(f"Изменения успешно запушены: {result.get('status')}")
                return result
        
        except Exception as e:
            logger.error(f"Ошибка при пуше изменений: {str(e)}")
            raise ValueError(f"Не удалось запушить изменения: {str(e)}")
    
    async def pull_changes(self, repo_id: str, branch: str = "main") -> Dict[str, Any]:
        """
        Пуллит изменения из удаленного репозитория.
        
        Args:
            repo_id: Идентификатор репозитория
            branch: Ветка для пулла
            
        Returns:
            Dict с информацией о пулле
        """
        logger.info(f"Пулл изменений из репозитория: {repo_id}, ветка: {branch}")
        
        try:
            # Формируем данные для запроса
            data = {
                "branch": branch
            }
            
            # Отправляем запрос к Git Service
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    f"{self.git_service_url}/repos/{repo_id}/pull",
                    json=data,
                    timeout=30.0
                )
                
                if response.status_code != 200:
                    logger.error(f"Ошибка при пулле изменений: {response.text}")
                    raise ValueError(f"Ошибка пулла изменений: {response.status_code}")
                
                result = response.json()
                logger.info(f"Изменения успешно запуллены: {result.get('status')}")
                return result
        
        except Exception as e:
            logger.error(f"Ошибка при пулле изменений: {str(e)}")
            raise ValueError(f"Не удалось запуллить изменения: {str(e)}")
    
    async def manage_branch(self, repo_id: str, branch: str, create: bool = False) -> Dict[str, Any]:
        """
        Управляет ветками в репозитории (создание, переключение).
        
        Args:
            repo_id: Идентификатор репозитория
            branch: Имя ветки
            create: Создать новую ветку (если True) или переключиться на существующую (если False)
            
        Returns:
            Dict с информацией о операции с веткой
        """
        action = "создание" if create else "переключение"
        logger.info(f"{action} ветки {branch} в репозитории: {repo_id}")
        
        try:
            # Формируем данные для запроса
            data = {
                "branch": branch,
                "create": create
            }
            
            # Отправляем запрос к Git Service
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    f"{self.git_service_url}/repos/{repo_id}/branch",
                    json=data,
                    timeout=10.0
                )
                
                if response.status_code != 200:
                    logger.error(f"Ошибка при управлении веткой: {response.text}")
                    raise ValueError(f"Ошибка управления веткой: {response.status_code}")
                
                result = response.json()
                logger.info(f"Операция с веткой успешно выполнена: {result.get('status')}")
                return result
        
        except Exception as e:
            logger.error(f"Ошибка при управлении веткой: {str(e)}")
            raise ValueError(f"Не удалось выполнить операцию с веткой: {str(e)}")
    
    async def get_diff(self, repo_id: str, file_path: Optional[str] = None) -> Dict[str, Any]:
        """
        Получает diff изменений в репозитории или конкретном файле.
        
        Args:
            repo_id: Идентификатор репозитория
            file_path: Путь к файлу (опционально, если None - для всего репозитория)
            
        Returns:
            Dict с информацией о diff
        """
        target = f"файла {file_path}" if file_path else "репозитория"
        logger.info(f"Получение diff для {target} в репозитории: {repo_id}")
        
        try:
            # Формируем параметры запроса
            params = {}
            if file_path:
                params["path"] = file_path
            
            # Отправляем запрос к Git Service
            async with httpx.AsyncClient() as client:
                response = await client.get(
                    f"{self.git_service_url}/repos/{repo_id}/diff",
                    params=params,
                    timeout=10.0
                )
                
                if response.status_code != 200:
                    logger.error(f"Ошибка при получении diff: {response.text}")
                    raise ValueError(f"Ошибка получения diff: {response.status_code}")
                
                result = response.json()
                return result
        
        except Exception as e:
            logger.error(f"Ошибка при получении diff: {str(e)}")
            raise ValueError(f"Не удалось получить diff: {str(e)}")
    
    async def create_pull_request(self, repo_id: str, title: str, description: str, 
                                 source_branch: str, target_branch: str = "main") -> Dict[str, Any]:
        """
        Создает pull request в удаленном репозитории.
        
        Args:
            repo_id: Идентификатор репозитория
            title: Заголовок pull request
            description: Описание pull request
            source_branch: Исходная ветка
            target_branch: Целевая ветка (по умолчанию main)
            
        Returns:
            Dict с информацией о созданном pull request
        """
        logger.info(f"Создание pull request из {source_branch} в {target_branch} в репозитории: {repo_id}")
        
        try:
            # Формируем данные для запроса
            data = {
                "title": title,
                "description": description,
                "source_branch": source_branch,
                "target_branch": target_branch
            }
            
            # Отправляем запрос к Git Service
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    f"{self.git_service_url}/repos/{repo_id}/pr",
                    json=data,
                    timeout=30.0
                )
                
                if response.status_code != 200:
                    logger.error(f"Ошибка при создании pull request: {response.text}")
                    raise ValueError(f"Ошибка создания pull request: {response.status_code}")
                
                result = response.json()
                logger.info(f"Pull request успешно создан: {result.get('pr_url')}")
                return result
        
        except Exception as e:
            logger.error(f"Ошибка при создании pull request: {str(e)}")
            raise ValueError(f"Не удалось создать pull request: {str(e)}")
    
    async def analyze_repository(self, repo_url: str, branch: Optional[str] = None) -> Dict[str, Any]:
        """
        Анализирует репозиторий для получения общей информации и ключевых файлов.
        
        Args:
            repo_url: URL репозитория
            branch: Ветка для анализа (опционально)
            
        Returns:
            Dict с результатами анализа репозитория
        """
        logger.info(f"Анализ репозитория: {repo_url}, ветка: {branch or 'default'}")
        
        try:
            # Формируем параметры запроса
            params = {"url": repo_url}
            if branch:
                params["branch"] = branch
            
            # Отправляем запрос к Git Service
            async with httpx.AsyncClient() as client:
                response = await client.get(
                    f"{self.git_service_url}/repos/analyze",
                    params=params,
                    timeout=60.0
                )
                
                if response.status_code != 200:
                    logger.error(f"Ошибка при анализе репозитория: {response.text}")
                    raise ValueError(f"Ошибка анализа репозитория: {response.status_code}")
                
                result = response.json()
                logger.info(f"Репозиторий успешно проанализирован")
                return result
        
        except Exception as e:
            logger.error(f"Ошибка при анализе репозитория: {str(e)}")
            raise ValueError(f"Не удалось проанализировать репозиторий: {str(e)}")