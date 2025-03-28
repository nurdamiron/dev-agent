# agent-service/app/tasks/executor.py

import logging
import asyncio
import json
from typing import Dict, Any, Optional
import httpx
from app.core.config import settings
from app.tasks.queue import TaskQueue
from app.services.claude_api import ClaudeAPI
from app.services.git_api import GitAPI

logger = logging.getLogger(__name__)

class TaskExecutor:
    """
    Класс для асинхронного выполнения задач агента.
    Обрабатывает длительные операции в фоновом режиме.
    """
    
    def __init__(self):
        """Инициализация исполнителя задач."""
        self.task_queue = TaskQueue()
        self.claude_api = ClaudeAPI()
        self.git_api = GitAPI()
        
        # Запуск обработчика очереди
        asyncio.create_task(self._process_queue())
        
        logger.info("TaskExecutor инициализирован")
    
    async def execute(self, task_id: str, task_type: str, **kwargs) -> Dict[str, Any]:
        """
        Добавляет задачу в очередь для асинхронного выполнения.
        
        Args:
            task_id: Уникальный идентификатор задачи
            task_type: Тип задачи (code_generation, git_operation и т.д.)
            **kwargs: Дополнительные параметры для выполнения задачи
            
        Returns:
            Dict с информацией о задаче
        """
        logger.info(f"Добавление задачи {task_id} типа {task_type} в очередь")
        
        # Создаем задачу с переданными параметрами
        task = {
            "id": task_id,
            "type": task_type,
            "status": "pending",
            "progress": 0,
            "params": kwargs
        }
        
        # Добавляем задачу в очередь
        await self.task_queue.add_task(task)
        
        # Обновляем статус задачи в API
        await self._update_task_status(task_id, "pending", 0)
        
        return task
    
    async def _process_queue(self):
        """
        Бесконечный цикл обработки задач из очереди.
        """
        logger.info("Запуск процесса обработки очереди задач")
        
        while True:
            try:
                # Получаем задачу из очереди
                task = await self.task_queue.get_task()
                
                if task:
                    # Обрабатываем задачу в зависимости от типа
                    logger.info(f"Начало выполнения задачи {task['id']} типа {task['type']}")
                    
                    # Обновляем статус задачи
                    await self._update_task_status(task['id'], "in_progress", 10)
                    
                    try:
                        if task['type'] == 'code_generation':
                            await self._handle_code_generation_task(task)
                        elif task['type'] == 'git_operation':
                            await self._handle_git_operation_task(task)
                        elif task['type'] == 'code_analysis':
                            await self._handle_code_analysis_task(task)
                        else:
                            logger.warning(f"Неизвестный тип задачи: {task['type']}")
                            await self._update_task_status(
                                task['id'], 
                                "failed", 
                                0, 
                                error=f"Неизвестный тип задачи: {task['type']}"
                            )
                    
                    except Exception as e:
                        logger.error(f"Ошибка при выполнении задачи {task['id']}: {str(e)}")
                        await self._update_task_status(
                            task['id'], 
                            "failed", 
                            0, 
                            error=str(e)
                        )
            
            except Exception as e:
                logger.error(f"Ошибка в процессе обработки очереди: {str(e)}")
            
            # Небольшая пауза перед следующей итерацией
            await asyncio.sleep(1)
    
    async def _handle_code_generation_task(self, task: Dict[str, Any]):
        """
        Обрабатывает задачу генерации кода.
        
        Args:
            task: Словарь с информацией о задаче
        """
        logger.info(f"Обработка задачи генерации кода {task['id']}")
        
        # Получаем параметры задачи
        params = task['params']
        prompt = params.get('prompt', '')
        context = params.get('context', {})
        
        try:
            # Обновляем прогресс задачи
            await self._update_task_status(task['id'], "in_progress", 30)
            
            # Вызываем Claude API для генерации кода
            response = await self.claude_api.send_request(prompt, max_tokens=4000)
            
            # Обновляем прогресс задачи
            await self._update_task_status(task['id'], "in_progress", 70)
            
            # Извлекаем код из ответа (можно реализовать более сложную логику)
            code_blocks = self._extract_code_blocks(response)
            
            # Подготавливаем результат
            result = {
                "response": response,
                "code_blocks": code_blocks
            }
            
            # Завершаем задачу с результатом
            await self._update_task_status(task['id'], "completed", 100, result=result)
        
        except Exception as e:
            logger.error(f"Ошибка при генерации кода: {str(e)}")
            await self._update_task_status(task['id'], "failed", 0, error=str(e))
    
    async def _handle_git_operation_task(self, task: Dict[str, Any]):
        """
        Обрабатывает задачу операций с Git.
        
        Args:
            task: Словарь с информацией о задаче
        """
        logger.info(f"Обработка задачи Git-операции {task['id']}")
        
        # Получаем параметры задачи
        params = task['params']
        operation_plan = params.get('operation_plan', {})
        context = params.get('context', {})
        
        try:
            # Обновляем прогресс задачи
            await self._update_task_status(task['id'], "in_progress", 20)
            
            # Получаем тип операции
            operation_type = operation_plan.get('operation_type', '').lower()
            operation_params = operation_plan.get('parameters', {})
            
            # Обновляем прогресс задачи
            await self._update_task_status(task['id'], "in_progress", 40)
            
            # Выполняем соответствующую Git-операцию
            result = {}
            
            if operation_type == 'clone':
                repo_url = operation_params.get('repo_url')
                branch = operation_params.get('branch')
                result = await self.git_api.clone_repository(repo_url, branch)
            
            elif operation_type == 'commit':
                repo_path = operation_params.get('repo_path')
                message = operation_params.get('message')
                files = operation_params.get('files', [])
                result = await self.git_api.commit_changes(repo_path, message, files)
            
            elif operation_type == 'push':
                repo_path = operation_params.get('repo_path')
                branch = operation_params.get('branch')
                result = await self.git_api.push_changes(repo_path, branch)
            
            elif operation_type == 'pull':
                repo_path = operation_params.get('repo_path')
                branch = operation_params.get('branch')
                result = await self.git_api.pull_changes(repo_path, branch)
            
            elif operation_type == 'branch':
                repo_path = operation_params.get('repo_path')
                branch_name = operation_params.get('branch_name')
                create = operation_params.get('create', False)
                result = await self.git_api.manage_branch(repo_path, branch_name, create)
            
            else:
                raise ValueError(f"Неподдерживаемая Git-операция: {operation_type}")
            
            # Обновляем прогресс задачи
            await self._update_task_status(task['id'], "in_progress", 80)
            
            # Подготавливаем результат
            operation_result = {
                "operation_type": operation_type,
                "result": result
            }
            
            # Завершаем задачу с результатом
            await self._update_task_status(task['id'], "completed", 100, result=operation_result)
        
        except Exception as e:
            logger.error(f"Ошибка при выполнении Git-операции: {str(e)}")
            await self._update_task_status(task['id'], "failed", 0, error=str(e))
    
    async def _handle_code_analysis_task(self, task: Dict[str, Any]):
        """
        Обрабатывает задачу анализа кода.
        
        Args:
            task: Словарь с информацией о задаче
        """
        logger.info(f"Обработка задачи анализа кода {task['id']}")
        
        # Получаем параметры задачи
        params = task['params']
        prompt = params.get('prompt', '')
        context = params.get('context', {})
        
        try:
            # Обновляем прогресс задачи
            await self._update_task_status(task['id'], "in_progress", 30)
            
            # Вызываем Claude API для анализа кода
            response = await self.claude_api.send_request(prompt, max_tokens=4000)
            
            # Обновляем прогресс задачи
            await self._update_task_status(task['id'], "in_progress", 80)
            
            # Подготавливаем результат
            result = {
                "analysis": response
            }
            
            # Завершаем задачу с результатом
            await self._update_task_status(task['id'], "completed", 100, result=result)
        
        except Exception as e:
            logger.error(f"Ошибка при анализе кода: {str(e)}")
            await self._update_task_status(task['id'], "failed", 0, error=str(e))
    
    async def _update_task_status(self, task_id: str, status: str, progress: int, 
                                 result: Optional[Dict[str, Any]] = None, 
                                 error: Optional[str] = None):
        """
        Обновляет статус задачи через API.
        
        Args:
            task_id: Идентификатор задачи
            status: Новый статус задачи (pending, in_progress, completed, failed)
            progress: Процент выполнения (0-100)
            result: Результат выполнения задачи (для completed)
            error: Сообщение об ошибке (для failed)
        """
        logger.info(f"Обновление статуса задачи {task_id}: {status}, прогресс: {progress}%")
        
        # Формируем данные для обновления
        update_data = {
            "status": status,
            "progress": progress
        }
        
        if result is not None:
            update_data["result"] = result
        
        if error is not None:
            update_data["error"] = error
        
        try:
            # Отправляем запрос на обновление статуса задачи
            async with httpx.AsyncClient() as client:
                response = await client.patch(
                    f"{settings.API_SERVICE_URL}/tasks/{task_id}/status",
                    json=update_data,
                    timeout=10.0
                )
                
                if response.status_code != 200:
                    logger.error(f"Ошибка при обновлении статуса задачи: {response.text}")
        
        except Exception as e:
            logger.error(f"Ошибка при отправке обновления статуса задачи: {str(e)}")
    
    def _extract_code_blocks(self, text: str) -> Dict[str, str]:
        """
        Извлекает блоки кода из текстового ответа.
        
        Args:
            text: Текст, содержащий блоки кода в формате markdown
            
        Returns:
            Dict с извлеченными блоками кода, где ключ - предполагаемое имя файла или язык,
            а значение - содержимое блока кода
        """
        import re
        
        # Регулярное выражение для поиска блоков кода в формате markdown
        # ```language
        # code
        # ```
        code_block_pattern = r"```([a-zA-Z0-9_+-]*)\n(.*?)\n```"
        
        # Находим все блоки кода
        code_blocks = {}
        matches = re.finditer(code_block_pattern, text, re.DOTALL)
        
        for i, match in enumerate(matches):
            language = match.group(1) or "text"
            code = match.group(2)
            
            # Генерируем имя файла на основе языка, если возможно
            file_extension = self._get_file_extension(language)
            file_name = f"file_{i+1}{file_extension}"
            
            code_blocks[file_name] = code
        
        return code_blocks
    
    def _get_file_extension(self, language: str) -> str:
        """
        Возвращает расширение файла на основе языка программирования.
        
        Args:
            language: Язык программирования
            
        Returns:
            Строка с расширением файла, включая точку
        """
        # Словарь соответствия языков и расширений файлов
        extensions = {
            "python": ".py",
            "javascript": ".js",
            "typescript": ".ts",
            "java": ".java",
            "c": ".c",
            "cpp": ".cpp",
            "csharp": ".cs",
            "go": ".go",
            "ruby": ".rb",
            "php": ".php",
            "swift": ".swift",
            "kotlin": ".kt",
            "rust": ".rs",
            "html": ".html",
            "css": ".css",
            "json": ".json",
            "yaml": ".yaml",
            "yml": ".yml",
            "xml": ".xml",
            "markdown": ".md",
            "md": ".md",
            "sql": ".sql",
            "shell": ".sh",
            "bash": ".sh",
            "dockerfile": ".Dockerfile",
            "makefile": ".Makefile"
        }
        
        return extensions.get(language.lower(), ".txt")