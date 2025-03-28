# agent-service/app/analyzers/code_analyzer.py

import logging
import asyncio
import httpx
from typing import Dict, List, Any, Optional
from app.services.claude_api import ClaudeAPI
from app.core.config import settings
from app.utils.prompt_utils import build_system_prompt

logger = logging.getLogger(__name__)

class CodeAnalyzer:
    """
    Класс для анализа кода с использованием API Claude.
    """
    
    def __init__(self):
        """Инициализация анализатора кода."""
        self.claude_api = ClaudeAPI()
        logger.info("CodeAnalyzer инициализирован")
    
    async def analyze_code(self, code: str, language: Optional[str] = None, context: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """
        Анализирует предоставленный код с использованием API Claude.
        
        Args:
            code: Строка с кодом для анализа
            language: Язык программирования кода
            context: Дополнительный контекст для анализа
            
        Returns:
            Dict с результатами анализа
        """
        logger.info(f"Начало анализа кода на языке: {language or 'не указан'}")
        
        # Создаем системный промпт для анализа кода
        system_prompt = build_system_prompt("code_analysis", context)
        
        # Формируем промпт для анализа кода
        prompt = f"""
        Проанализируй следующий код{f' на языке {language}' if language else ''}:

        ```{language or ''}
        {code}
        ```

        Выполни следующие задачи:
        1. Объясни основную функциональность и структуру кода
        2. Оцени качество кода и выяви потенциальные проблемы, включая:
           - Ошибки или баги
           - Проблемы производительности
           - Уязвимости безопасности
           - Нарушения лучших практик и стандартов
        3. Предложи конкретные улучшения с примерами кода

        Организуй ответ в разделы:
        - Общий обзор
        - Анализ структуры
        - Потенциальные проблемы
        - Рекомендуемые улучшения
        """
        
        # Получаем ответ от Claude API
        response = await self.claude_api.send_request(prompt)
        
        # Структурируем результат анализа
        analysis_result = {
            "code": code,
            "language": language,
            "analysis": response
        }
        
        logger.info("Анализ кода завершен")
        return analysis_result
    
    async def analyze_repository(self, repo_url: str, branch: Optional[str] = None) -> Dict[str, Any]:
        """
        Анализирует репозиторий кода, получая ключевые файлы через Git Service.
        
        Args:
            repo_url: URL репозитория
            branch: Ветка для анализа (опционально)
            
        Returns:
            Dict с результатами анализа репозитория
        """
        logger.info(f"Начало анализа репозитория: {repo_url}, ветка: {branch or 'default'}")
        
        try:
            # Запрашиваем информацию о репозитории из Git Service
            async with httpx.AsyncClient() as client:
                params = {"url": repo_url}
                if branch:
                    params["branch"] = branch
                
                response = await client.get(
                    f"{settings.GIT_SERVICE_URL}/repos/analyze",
                    params=params,
                    timeout=60.0
                )
                
                if response.status_code != 200:
                    logger.error(f"Ошибка при запросе информации о репозитории: {response.text}")
                    raise ValueError(f"Ошибка получения информации о репозитории: {response.status_code}")
                
                repo_info = response.json()
            
            # Получаем ключевые файлы для анализа
            key_files = repo_info.get("key_files", [])
            
            # Подготавливаем контекст для анализа
            context = {
                "repository": {
                    "url": repo_url,
                    "branch": branch,
                    "description": repo_info.get("description", "Нет описания"),
                    "language": repo_info.get("language", "Не определен"),
                    "files_count": repo_info.get("files_count", 0)
                }
            }
            
            # Формируем промпт для анализа репозитория
            files_content = []
            for file in key_files:
                files_content.append(f"## Файл: {file['path']}")
                files_content.append(f"```{file.get('language', '')}")
                files_content.append(file.get("content", "Содержимое недоступно"))
                files_content.append("```\n")
            
            files_str = "\n".join(files_content)
            
            prompt = f"""
            Проанализируй следующий репозиторий:
            
            Репозиторий: {repo_url}
            Ветка: {branch or 'default'}
            Язык: {repo_info.get('language', 'Не определен')}
            Описание: {repo_info.get('description', 'Нет описания')}
            Количество файлов: {repo_info.get('files_count', 0)}
            
            Ниже представлены ключевые файлы репозитория для анализа:
            
            {files_str}
            
            Предоставь следующую информацию:
            1. Общий обзор репозитория и его назначение
            2. Архитектура проекта и основные компоненты
            3. Используемые технологии и библиотеки
            4. Основные паттерны проектирования
            5. Потенциальные улучшения и рекомендации
            
            Структурируй ответ по разделам и дай конкретные рекомендации, если возможно.
            """
            
            # Отправляем запрос к Claude API
            response = await self.claude_api.send_request(prompt, max_tokens=4000)
            
            # Формируем результат анализа
            analysis_result = {
                "repository": {
                    "url": repo_url,
                    "branch": branch,
                    "language": repo_info.get("language"),
                    "description": repo_info.get("description"),
                    "files_count": repo_info.get("files_count")
                },
                "key_files": [file["path"] for file in key_files],
                "analysis": response
            }
            
            logger.info(f"Анализ репозитория {repo_url} завершен")
            return analysis_result
        
        except Exception as e:
            logger.error(f"Ошибка при анализе репозитория: {str(e)}")
            raise ValueError(f"Не удалось выполнить анализ репозитория: {str(e)}")
    
    async def analyze_code_diff(self, diff: str, context: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """
        Анализирует различия в коде (diff) с использованием API Claude.
        
        Args:
            diff: Строка с diff-ом в формате unified diff
            context: Дополнительный контекст для анализа
            
        Returns:
            Dict с результатами анализа diff-а
        """
        logger.info("Начало анализа различий в коде")
        
        # Создаем системный промпт для анализа кода
        system_prompt = build_system_prompt("code_analysis", context)
        
        # Формируем промпт для анализа diff-а
        prompt = f"""
        Проанализируй следующие изменения кода (diff):

        ```diff
        {diff}
        ```

        Предоставь следующую информацию:
        1. Краткое описание изменений
        2. Анализ влияния изменений на функциональность
        3. Потенциальные проблемы или риски, связанные с изменениями
        4. Рекомендации по улучшению или альтернативные подходы, если применимо

        Организуй ответ по разделам, фокусируясь на ключевых изменениях.
        """
        
        # Получаем ответ от Claude API
        response = await self.claude_api.send_request(prompt)
        
        # Структурируем результат анализа
        analysis_result = {
            "diff": diff,
            "analysis": response
        }
        
        logger.info("Анализ различий в коде завершен")
        return analysis_result