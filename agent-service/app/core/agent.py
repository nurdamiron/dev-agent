# agent-service/app/core/agent.py

import logging
import uuid
import json
from typing import Dict, List, Any, Optional
from fastapi import HTTPException
from app.services.claude_api import ClaudeAPI
from app.analyzers.code_analyzer import CodeAnalyzer
from app.analyzers.dependency_analyzer import DependencyAnalyzer
from app.generators.code_generator import CodeGenerator
from app.utils.prompt_utils import load_prompt, format_context_for_prompt
from app.utils.file_utils import format_file_context
from app.tasks.executor import TaskExecutor

logger = logging.getLogger(__name__)

class DevAgent:
    """
    Основной класс AI-агента разработчика, который координирует все взаимодействия
    и решения, принимаемые AI при работе с запросами пользователей.
    """
    
    def __init__(self):
        """Инициализация агента и его компонентов."""
        self.claude_api = ClaudeAPI()
        self.code_analyzer = CodeAnalyzer()
        self.dependency_analyzer = DependencyAnalyzer()
        self.code_generator = CodeGenerator()
        self.task_executor = TaskExecutor()
        
        # Загрузка шаблонов промптов
        self.prompts = {
            "code_analysis": load_prompt("code_analysis.txt"),
            "code_generation": load_prompt("code_generation.txt"),
            "error_fixing": load_prompt("error_fixing.txt")
        }
        
        logger.info("DevAgent инициализирован")
    
    async def process_message(self, user_id: str, message: str, 
                             project_context: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """
        Обрабатывает входящее сообщение от пользователя и определяет необходимые действия.
        
        Args:
            user_id: Идентификатор пользователя
            message: Текст сообщения от пользователя
            project_context: Дополнительный контекст проекта (репозиторий, файлы и т.д.)
            
        Returns:
            Dict с ответом и метаданными
        """
        logger.info(f"Обработка сообщения для пользователя {user_id}")
        
        # Определяем тип запроса
        request_type = await self._classify_request(message, project_context)
        
        # В зависимости от типа запроса выбираем стратегию обработки
        response = {}
        
        if request_type == "code_analysis":
            response = await self._handle_code_analysis(message, project_context)
        elif request_type == "code_generation":
            response = await self._handle_code_generation(message, project_context)
        elif request_type == "error_fixing":
            response = await self._handle_error_fixing(message, project_context)
        elif request_type == "git_operation":
            response = await self._handle_git_operation(message, project_context)
        elif request_type == "general_question":
            response = await self._handle_general_question(message, project_context)
        else:
            # Если не удалось определить тип запроса, обрабатываем как общий вопрос
            response = await self._handle_general_question(message, project_context)
        
        return response
    
    async def _classify_request(self, message: str, 
                               context: Optional[Dict[str, Any]] = None) -> str:
        """
        Классифицирует тип запроса пользователя для определения дальнейших действий.
        
        Args:
            message: Текст сообщения от пользователя
            context: Дополнительный контекст
            
        Returns:
            Строка с типом запроса: code_analysis, code_generation, error_fixing, git_operation, general_question
        """
        # Формируем промпт для классификации запроса
        prompt = f"""
        Я разрабатываю систему для анализа запросов пользователей. Пожалуйста, определи тип следующего запроса,
        выбрав ТОЛЬКО ОДНУ категорию из списка:

        1. code_analysis - запрос на анализ кода, архитектуры, объяснение как что-то работает
        2. code_generation - запрос на генерацию нового кода или модификацию существующего
        3. error_fixing - запрос на исправление ошибки или отладку проблемы
        4. git_operation - запрос на операции с git (clone, commit, push и т.д.)
        5. general_question - общий вопрос, не относящийся к указанным категориям
        
        Запрос пользователя: "{message}"
        
        Ответ (только название категории):
        """
        
        # Вызываем Claude API для классификации
        result = await self.claude_api.send_request(prompt, max_tokens=100)
        
        # Обрабатываем ответ для получения чистой категории
        result = result.strip().lower()
        
        # Извлекаем тип запроса из ответа
        for request_type in ["code_analysis", "code_generation", "error_fixing", "git_operation", "general_question"]:
            if request_type in result:
                return request_type
        
        # По умолчанию считаем запрос общим вопросом
        return "general_question"
    
    async def _handle_code_analysis(self, message: str, 
                                   context: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """Обрабатывает запрос на анализ кода."""
        logger.info("Обработка запроса на анализ кода")
        
        # Получаем контекст кода из проекта, если предоставлен
        code_context = ""
        if context and "files" in context:
            code_context = format_file_context(context["files"])
        
        # Формируем промпт для анализа кода
        prompt = self.prompts["code_analysis"].format(
            user_message=message,
            code_context=code_context
        )
        
        # Получаем ответ от Claude API
        response_text = await self.claude_api.send_request(prompt)
        
        # В случае анализа кода обычно возвращаем синхронный ответ
        return {
            "message": response_text,
            "meta": {
                "type": "code_analysis",
                "analyzed_files": context.get("files", []) if context else []
            }
        }
    
    async def _handle_code_generation(self, message: str, 
                                     context: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """Обрабатывает запрос на генерацию кода."""
        logger.info("Обработка запроса на генерацию кода")
        
        # Для генерации кода может потребоваться создание фоновой задачи
        task_id = str(uuid.uuid4())
        
        # Получаем контекст кода
        code_context = ""
        if context and "files" in context:
            code_context = format_file_context(context["files"])
        
        # Формируем промпт для генерации кода
        prompt = self.prompts["code_generation"].format(
            user_message=message,
            code_context=code_context
        )
        
        # Для быстрого ответа генерируем предварительный ответ
        preliminary_response = await self.claude_api.send_request(
            prompt, max_tokens=1000
        )
        
        # Создаем задачу для полной генерации в фоне, если требуется большой объем кода
        task = {
            "id": task_id,
            "type": "code_generation",
            "status": "pending",
            "progress": 0,
            "description": f"Генерация кода для запроса: {message[:50]}..."
        }
        
        # Запускаем задачу в фоновом режиме, если генерация сложная
        if len(message.split()) > 20 or (context and len(context.get("files", [])) > 2):
            await self.task_executor.execute(
                task_id=task_id,
                task_type="code_generation",
                prompt=prompt,
                context=context
            )
            
            return {
                "message": f"Я начал генерировать код для вашего запроса. " + 
                          f"Вот предварительный результат:\n\n{preliminary_response}",
                "meta": {
                    "type": "code_generation"
                },
                "task": task
            }
        else:
            # Для простых запросов возвращаем результат сразу
            return {
                "message": preliminary_response,
                "meta": {
                    "type": "code_generation"
                }
            }
    
    async def _handle_error_fixing(self, message: str, 
                                  context: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """Обрабатывает запрос на исправление ошибок."""
        logger.info("Обработка запроса на исправление ошибок")
        
        # Получаем контекст кода и ошибки
        code_context = ""
        error_context = ""
        
        if context:
            if "files" in context:
                code_context = format_file_context(context["files"])
            if "error" in context:
                error_context = context["error"]
        
        # Формируем промпт для исправления ошибок
        prompt = self.prompts["error_fixing"].format(
            user_message=message,
            code_context=code_context,
            error_context=error_context
        )
        
        # Получаем ответ от Claude API
        response_text = await self.claude_api.send_request(prompt)
        
        return {
            "message": response_text,
            "meta": {
                "type": "error_fixing",
                "analyzed_files": context.get("files", []) if context else []
            }
        }
    
    async def _handle_git_operation(self, message: str, 
                                   context: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """Обрабатывает запрос на операции с Git."""
        logger.info("Обработка запроса на операции с Git")
        
        # Создаем задачу для выполнения Git-операций
        task_id = str(uuid.uuid4())
        
        task = {
            "id": task_id,
            "type": "git_operation",
            "status": "pending",
            "progress": 0,
            "description": f"Git-операция: {message[:50]}..."
        }
        
        # Формируем промпт для Claude, чтобы понять, что именно нужно сделать
        prompt = f"""
        Пользователь запрашивает операцию с Git: "{message}"
        
        Проанализируй запрос и определи:
        1. Какой тип операции требуется (clone, commit, push, pull, branch и т.д.)
        2. Какие параметры необходимы для выполнения (URL репозитория, ветка, сообщение и т.д.)
        3. Шаги, которые нужно выполнить
        
        Представь результат в JSON формате:
        {{
            "operation_type": "тип операции",
            "parameters": {{
                "param1": "value1",
                "param2": "value2"
            }},
            "steps": [
                "шаг 1",
                "шаг 2"
            ]
        }}
        """
        
        # Получаем план действий от Claude API
        operation_plan_text = await self.claude_api.send_request(prompt, max_tokens=1000)
        
        try:
            # Извлекаем JSON из ответа
            operation_plan = self._extract_json(operation_plan_text)
            
            # Запускаем задачу для выполнения Git-операций
            await self.task_executor.execute(
                task_id=task_id,
                task_type="git_operation",
                operation_plan=operation_plan,
                context=context
            )
            
            # Возвращаем пользователю информацию о начале выполнения задачи
            return {
                "message": f"Я начал выполнение Git-операции: {operation_plan.get('operation_type', 'операция')}. " +
                          f"Вы получите уведомление, когда задача будет завершена.",
                "meta": {
                    "type": "git_operation",
                    "operation_type": operation_plan.get("operation_type")
                },
                "task": task
            }
        except Exception as e:
            logger.error(f"Ошибка при обработке Git-операции: {str(e)}")
            return {
                "message": f"Произошла ошибка при анализе вашего запроса на Git-операцию. " +
                          f"Пожалуйста, уточните, что именно вы хотите сделать с репозиторием.",
                "meta": {
                    "type": "git_operation",
                    "error": str(e)
                }
            }
    
    async def _handle_general_question(self, message: str, 
                                      context: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """Обрабатывает общие вопросы."""
        logger.info("Обработка общего вопроса")
        
        # Формируем промпт с контекстом проекта, если он есть
        project_context = ""
        if context and "project" in context:
            project_context = f"Контекст проекта: {json.dumps(context['project'])}\n\n"
        
        prompt = f"""
        {project_context}
        
        Пользователь спрашивает: {message}
        
        Пожалуйста, предоставь информативный и полезный ответ, относящийся к разработке ПО.
        Если вопрос связан с конкретным проектом, учти предоставленный контекст.
        """
        
        # Получаем ответ от Claude API
        response_text = await self.claude_api.send_request(prompt)
        
        return {
            "message": response_text,
            "meta": {
                "type": "general_question"
            }
        }
    
    def _extract_json(self, text: str) -> Dict:
        """
        Извлекает JSON из текстового ответа, ищет фрагмент в фигурных скобках.
        
        Args:
            text: Текст, содержащий JSON
            
        Returns:
            Dict с извлеченным JSON
        
        Raises:
            ValueError: Если не удалось извлечь валидный JSON
        """
        try:
            # Ищем JSON в ответе (между фигурными скобками)
            start_index = text.find("{")
            end_index = text.rfind("}")
            
            if start_index == -1 or end_index == -1:
                raise ValueError("JSON не найден в ответе")
            
            json_str = text[start_index:end_index+1]
            return json.loads(json_str)
        except json.JSONDecodeError as e:
            logger.error(f"Ошибка декодирования JSON: {str(e)}")
            raise ValueError(f"Не удалось разобрать JSON в ответе: {str(e)}")