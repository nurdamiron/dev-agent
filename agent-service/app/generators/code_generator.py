# agent-service/app/generators/code_generator.py

import logging
import re
from typing import Dict, List, Any, Optional, Tuple
from app.services.claude_api import ClaudeAPI
from app.utils.prompt_utils import build_system_prompt

logger = logging.getLogger(__name__)

class CodeGenerator:
    """
    Класс для генерации кода с использованием API Claude.
    """
    
    def __init__(self):
        """Инициализация генератора кода."""
        self.claude_api = ClaudeAPI()
        logger.info("CodeGenerator инициализирован")
    
    async def generate_code(self, description: str, language: str, 
                           context: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """
        Генерирует код на основе текстового описания.
        
        Args:
            description: Описание требуемого кода
            language: Язык программирования для генерации
            context: Дополнительный контекст для генерации
            
        Returns:
            Dict с результатами генерации
        """
        logger.info(f"Начало генерации кода на языке {language}")
        
        # Создаем системный промпт для генерации кода
        system_prompt = build_system_prompt("code_generation", context)
        
        # Формируем контекст из файлов, если он предоставлен
        context_str = ""
        if context and "files" in context:
            context_str = "Существующий код для контекста:\n\n"
            for file in context["files"]:
                file_path = file.get("path", "Неизвестный файл")
                file_content = file.get("content", "Содержимое недоступно")
                context_str += f"## Файл: {file_path}\n```\n{file_content}\n```\n\n"
        
        # Формируем промпт для генерации кода
        prompt = f"""
        Напиши код на языке {language} для выполнения следующей задачи:
        
        {description}
        
        {context_str}
        
        Требования:
        1. Код должен быть чистым, хорошо структурированным и следовать лучшим практикам
        2. Включи необходимые импорты и зависимости
        3. Добавь комментарии для объяснения ключевых частей кода
        4. Следуй стандартным соглашениям о стиле для языка {language}
        
        Предоставь полный код, готовый к использованию. Если код должен быть разделен на несколько файлов,
        обозначь каждый файл с указанием пути. Например:
        
        ## Файл: src/main.py
        ```python
        # Код здесь
        ```
        
        ## Файл: src/utils.py
        ```python
        # Код здесь
        ```
        """
        
        # Получаем ответ от Claude API
        response = await self.claude_api.send_request(prompt, max_tokens=4000)
        
        # Извлекаем сгенерированный код
        files = self._extract_code_files(response)
        
        # Формируем результат
        result = {
            "language": language,
            "description": description,
            "files": files
        }
        
        logger.info(f"Генерация кода завершена. Сгенерировано {len(files)} файлов")
        return result
    
    async def modify_code(self, original_code: str, instructions: str, 
                         language: str, context: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """
        Модифицирует существующий код в соответствии с инструкциями.
        
        Args:
            original_code: Исходный код для модификации
            instructions: Инструкции по модификации кода
            language: Язык программирования
            context: Дополнительный контекст
            
        Returns:
            Dict с результатами модификации
        """
        logger.info(f"Начало модификации кода на языке {language}")
        
        # Создаем системный промпт для модификации кода
        system_prompt = build_system_prompt("code_generation", context)
        
        # Формируем промпт для модификации кода
        prompt = f"""
        Модифицируй следующий код на языке {language} в соответствии с инструкциями:
        
        ## Исходный код:
        ```{language}
        {original_code}
        ```
        
        ## Инструкции для модификации:
        {instructions}
        
        Требования:
        1. Сохрани существующую структуру кода, если не указано иное
        2. Внеси только необходимые изменения
        3. Объясни ключевые изменения в комментариях
        4. Следуй стандартным соглашениям о стиле для языка {language}
        
        Предоставь полный модифицированный код и кратко опиши основные внесенные изменения.
        """
        
        # Получаем ответ от Claude API
        response = await self.claude_api.send_request(prompt, max_tokens=4000)
        
        # Извлекаем модифицированный код и сводку изменений
        code, summary = self._extract_modified_code(response, language)
        
        # Формируем результат
        result = {
            "language": language,
            "original_code": original_code,
            "modified_code": code,
            "summary": summary,
            "instructions": instructions
        }
        
        logger.info("Модификация кода завершена")
        return result
    
    async def generate_tests(self, code: str, language: str, 
                            test_framework: Optional[str] = None,
                            context: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """
        Генерирует тесты для предоставленного кода.
        
        Args:
            code: Код, для которого нужно сгенерировать тесты
            language: Язык программирования
            test_framework: Фреймворк для тестирования (опционально)
            context: Дополнительный контекст
            
        Returns:
            Dict с результатами генерации тестов
        """
        logger.info(f"Начало генерации тестов для кода на языке {language}")
        
        # Определяем фреймворк для тестирования, если не указан
        if not test_framework:
            test_framework = self._get_default_test_framework(language)
        
        # Создаем системный промпт для генерации тестов
        system_prompt = build_system_prompt("code_generation", context)
        
        # Формируем промпт для генерации тестов
        prompt = f"""
        Напиши модульные тесты для следующего кода на языке {language} с использованием фреймворка {test_framework}:
        
        ```{language}
        {code}
        ```
        
        Требования:
        1. Тесты должны быть полными и охватывать основные функциональности кода
        2. Проверить как позитивные сценарии, так и обработку ошибок
        3. Добавить необходимые mock-объекты или fixtures, если требуется
        4. Следовать лучшим практикам тестирования для языка {language} и фреймворка {test_framework}
        
        Предоставь полный код тестов и коротко объясни, что тестирует каждый тест.
        """
        
        # Получаем ответ от Claude API
        response = await self.claude_api.send_request(prompt, max_tokens=4000)
        
        # Извлекаем сгенерированные тесты
        test_code, explanation = self._extract_test_code(response, language)
        
        # Формируем результат
        result = {
            "language": language,
            "original_code": code,
            "test_framework": test_framework,
            "test_code": test_code,
            "explanation": explanation
        }
        
        logger.info("Генерация тестов завершена")
        return result
    
    async def refactor_code(self, original_code: str, language: str, 
                           refactoring_type: str = "general",
                           context: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """
        Рефакторит код в соответствии с указанным типом рефакторинга.
        
        Args:
            original_code: Исходный код для рефакторинга
            language: Язык программирования
            refactoring_type: Тип рефакторинга (general, performance, readability, etc.)
            context: Дополнительный контекст
            
        Returns:
            Dict с результатами рефакторинга
        """
        logger.info(f"Начало рефакторинга кода на языке {language}, тип: {refactoring_type}")
        
        # Создаем системный промпт для рефакторинга
        system_prompt = build_system_prompt("code_generation", context)
        
        # Формируем описание типа рефакторинга
        refactoring_description = self._get_refactoring_description(refactoring_type)
        
        # Формируем промпт для рефакторинга
        prompt = f"""
        Рефактори следующий код на языке {language}, фокусируясь на {refactoring_description}:
        
        ```{language}
        {original_code}
        ```
        
        Требования:
        1. Сохрани функциональность кода
        2. Следуй лучшим практикам для языка {language}
        3. Оптимизируй код в соответствии с типом рефакторинга: {refactoring_type}
        4. Прокомментируй ключевые изменения
        
        Предоставь полный рефакторинг кода и объясни основные сделанные улучшения.
        """
        
        # Получаем ответ от Claude API
        response = await self.claude_api.send_request(prompt, max_tokens=4000)
        
        # Извлекаем рефакторинг кода и сводку изменений
        refactored_code, improvements = self._extract_refactored_code(response, language)
        
        # Формируем результат
        result = {
            "language": language,
            "original_code": original_code,
            "refactored_code": refactored_code,
            "refactoring_type": refactoring_type,
            "improvements": improvements
        }
        
        logger.info("Рефакторинг кода завершен")
        return result
    
    def _extract_code_files(self, response: str) -> List[Dict[str, Any]]:
        """
        Извлекает файлы с кодом из ответа Claude API.
        
        Args:
            response: Текстовый ответ от Claude API
            
        Returns:
            List с информацией о файлах
        """
        files = []
        
        # Регулярное выражение для поиска блоков файлов
        # ## Файл: path/to/file.ext
        # ```[language]
        # code
        # ```
        file_pattern = r"## Файл:\s*(.*?)\n```(?:\w*)\n(.*?)```"
        
        # Находим все блоки файлов
        matches = re.finditer(file_pattern, response, re.DOTALL)
        
        for match in matches:
            file_path = match.group(1).strip()
            file_content = match.group(2).strip()
            
            # Определяем язык по расширению файла
            extension = file_path.split(".")[-1] if "." in file_path else ""
            language = self._get_language_by_extension(extension)
            
            files.append({
                "path": file_path,
                "content": file_content,
                "language": language
            })
        
        # Если блоки файлов не найдены, но есть блок кода, считаем его одним файлом
        if not files:
            code_pattern = r"```(?:(\w+)\n)?(.*?)```"
            matches = re.finditer(code_pattern, response, re.DOTALL)
            
            for match in matches:
                language = match.group(1) or "text"
                code = match.group(2).strip()
                
                extension = self._get_extension_by_language(language)
                file_path = f"generated_code{extension}"
                
                files.append({
                    "path": file_path,
                    "content": code,
                    "language": language
                })
        
        return files
    
    def _extract_modified_code(self, response: str, language: str) -> Tuple[str, str]:
        """
        Извлекает модифицированный код и сводку изменений из ответа Claude API.
        
        Args:
            response: Текстовый ответ от Claude API
            language: Язык программирования
            
        Returns:
            Tuple с модифицированным кодом и сводкой изменений
        """
        # Регулярное выражение для поиска блока кода
        code_pattern = r"```(?:\w*)\n(.*?)```"
        
        # Находим все блоки кода
        code_matches = re.finditer(code_pattern, response, re.DOTALL)
        
        modified_code = ""
        for match in code_matches:
            code = match.group(1).strip()
            modified_code = code  # Берем последний найденный блок кода
        
        # Извлекаем сводку изменений
        # Ищем текст после последнего блока кода или перед первым блоком кода
        if modified_code:
            last_code_end = response.rfind("```") + 3
            summary = response[last_code_end:].strip()
            
            # Если после кода нет текста, ищем текст до первого блока кода
            if not summary:
                first_code_start = response.find("```")
                if first_code_start > 0:
                    summary = response[:first_code_start].strip()
        else:
            summary = response.strip()
        
        return modified_code, summary
    
    def _extract_test_code(self, response: str, language: str) -> Tuple[str, str]:
        """
        Извлекает код тестов и объяснение из ответа Claude API.
        
        Args:
            response: Текстовый ответ от Claude API
            language: Язык программирования
            
        Returns:
            Tuple с кодом тестов и объяснением
        """
        # Регулярное выражение для поиска блока кода
        code_pattern = r"```(?:\w*)\n(.*?)```"
        
        # Находим все блоки кода
        code_matches = re.finditer(code_pattern, response, re.DOTALL)
        
        test_code = ""
        for match in code_matches:
            code = match.group(1).strip()
            test_code = code  # Берем последний найденный блок кода
        
        # Извлекаем объяснение
        # Ищем текст после последнего блока кода или перед первым блоком кода
        if test_code:
            last_code_end = response.rfind("```") + 3
            explanation = response[last_code_end:].strip()
            
            # Если после кода нет текста, ищем текст до первого блока кода
            if not explanation:
                first_code_start = response.find("```")
                if first_code_start > 0:
                    explanation = response[:first_code_start].strip()
        else:
            explanation = response.strip()
        
        return test_code, explanation
    
    def _extract_refactored_code(self, response: str, language: str) -> Tuple[str, str]:
        """
        Извлекает рефакторинг кода и улучшения из ответа Claude API.
        
        Args:
            response: Текстовый ответ от Claude API
            language: Язык программирования
            
        Returns:
            Tuple с рефакторингом кода и улучшениями
        """
        # Аналогично методу _extract_modified_code
        return self._extract_modified_code(response, language)
    
    def _get_default_test_framework(self, language: str) -> str:
        """
        Возвращает фреймворк для тестирования по умолчанию для указанного языка.
        
        Args:
            language: Язык программирования
            
        Returns:
            Строка с названием фреймворка
        """
        frameworks = {
            "python": "pytest",
            "javascript": "jest",
            "typescript": "jest",
            "java": "JUnit",
            "csharp": "NUnit",
            "go": "testing",
            "ruby": "RSpec",
            "php": "PHPUnit",
            "rust": "cargo test",
            "swift": "XCTest"
        }
        
        return frameworks.get(language.lower(), "unittest")
    
    def _get_refactoring_description(self, refactoring_type: str) -> str:
        """
        Возвращает описание типа рефакторинга.
        
        Args:
            refactoring_type: Тип рефакторинга
            
        Returns:
            Строка с описанием
        """
        descriptions = {
            "general": "общем улучшении кода",
            "performance": "оптимизации производительности",
            "readability": "улучшении читаемости кода",
            "maintainability": "улучшении поддерживаемости кода",
            "security": "улучшении безопасности кода",
            "modernization": "модернизации кода под современные стандарты",
            "clean_code": "принципах чистого кода"
        }
        
        return descriptions.get(refactoring_type.lower(), "общем улучшении кода")
    
    def _get_language_by_extension(self, extension: str) -> str:
        """
        Определяет язык программирования по расширению файла.
        
        Args:
            extension: Расширение файла
            
        Returns:
            Строка с названием языка
        """
        extensions = {
            "py": "python",
            "js": "javascript",
            "ts": "typescript",
            "jsx": "jsx",
            "tsx": "tsx",
            "html": "html",
            "css": "css",
            "java": "java",
            "c": "c",
            "cpp": "cpp",
            "cs": "csharp",
            "go": "go",
            "rb": "ruby",
            "php": "php",
            "swift": "swift",
            "kt": "kotlin",
            "rs": "rust",
            "sh": "bash",
            "json": "json",
            "yml": "yaml",
            "yaml": "yaml",
            "xml": "xml",
            "md": "markdown"
        }
        
        return extensions.get(extension.lower(), "text")
    
    def _get_extension_by_language(self, language: str) -> str:
        """
        Определяет расширение файла по языку программирования.
        
        Args:
            language: Язык программирования
            
        Returns:
            Строка с расширением файла
        """
        languages = {
            "python": ".py",
            "javascript": ".js",
            "typescript": ".ts",
            "jsx": ".jsx",
            "tsx": ".tsx",
            "html": ".html",
            "css": ".css",
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
            "bash": ".sh",
            "json": ".json",
            "yaml": ".yml",
            "xml": ".xml",
            "markdown": ".md"
        }
        
        return languages.get(language.lower(), ".txt")