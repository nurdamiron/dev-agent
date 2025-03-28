# agent-service/app/analyzers/dependency_analyzer.py

import logging
import httpx
import re
from typing import Dict, List, Any, Optional, Set
from app.core.config import settings
from app.services.claude_api import ClaudeAPI

logger = logging.getLogger(__name__)

class DependencyAnalyzer:
    """
    Класс для анализа зависимостей в проектах различных языков программирования.
    """
    
    def __init__(self):
        """Инициализация анализатора зависимостей."""
        self.claude_api = ClaudeAPI()
        logger.info("DependencyAnalyzer инициализирован")
    
    async def analyze_dependencies(self, files: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Анализирует зависимости проекта на основе предоставленных файлов.
        
        Args:
            files: Список словарей с информацией о файлах
            
        Returns:
            Dict с результатами анализа зависимостей
        """
        logger.info("Начало анализа зависимостей проекта")
        
        # Определяем технологический стек проекта
        tech_stack = await self._detect_tech_stack(files)
        
        # Извлекаем файлы зависимостей в зависимости от технологического стека
        dependency_files = self._extract_dependency_files(files, tech_stack)
        
        if not dependency_files:
            logger.warning("Не найдены файлы с зависимостями для анализа")
            return {
                "tech_stack": tech_stack,
                "dependencies": [],
                "recommendations": "Не найдены файлы с зависимостями для анализа."
            }
        
        # Анализируем каждый файл зависимостей
        all_dependencies = []
        for dep_file in dependency_files:
            deps = await self._parse_dependencies(dep_file, tech_stack)
            all_dependencies.extend(deps)
        
        # Удаляем дубликаты
        unique_deps = []
        seen = set()
        for dep in all_dependencies:
            if dep["name"] not in seen:
                seen.add(dep["name"])
                unique_deps.append(dep)
        
        # Получаем рекомендации по зависимостям с использованием Claude API
        recommendations = await self._get_dependency_recommendations(unique_deps, tech_stack)
        
        analysis_result = {
            "tech_stack": tech_stack,
            "dependencies": unique_deps,
            "recommendations": recommendations
        }
        
        logger.info(f"Анализ зависимостей завершен. Найдено {len(unique_deps)} уникальных зависимостей")
        return analysis_result
    
    async def _detect_tech_stack(self, files: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Определяет технологический стек проекта на основе файлов.
        
        Args:
            files: Список словарей с информацией о файлах
            
        Returns:
            Dict с информацией о технологическом стеке
        """
        # Маркеры для определения технологий
        tech_markers = {
            "python": [".py", "requirements.txt", "setup.py", "Pipfile", "pyproject.toml"],
            "javascript": [".js", ".jsx", "package.json", "yarn.lock", "npm-shrinkwrap.json"],
            "typescript": [".ts", ".tsx", "tsconfig.json"],
            "java": [".java", "pom.xml", "build.gradle", ".gradle"],
            "csharp": [".cs", ".csproj", ".sln"],
            "go": [".go", "go.mod", "go.sum"],
            "ruby": [".rb", "Gemfile", "Gemfile.lock"],
            "php": [".php", "composer.json", "composer.lock"],
            "rust": [".rs", "Cargo.toml", "Cargo.lock"],
            "docker": ["Dockerfile", "docker-compose.yml"],
            "kubernetes": [".yaml", ".yml"]  # Потенциально Kubernetes конфигурации
        }
        
        # Счетчики для каждой технологии
        tech_counts = {tech: 0 for tech in tech_markers}
        
        # Проходим по всем файлам и считаем маркеры
        for file_info in files:
            file_path = file_info.get("path", "")
            
            for tech, markers in tech_markers.items():
                for marker in markers:
                    if marker in file_path:
                        tech_counts[tech] += 1
                        break
        
        # Определяем основные технологии
        main_techs = [tech for tech, count in tech_counts.items() if count > 0]
        
        # Определяем конкретные фреймворки и библиотеки
        frameworks = await self._detect_frameworks(files, main_techs)
        
        return {
            "main_languages": main_techs,
            "frameworks": frameworks
        }
    
    async def _detect_frameworks(self, files: List[Dict[str, Any]], main_techs: List[str]) -> List[str]:
        """
        Определяет фреймворки и библиотеки, используемые в проекте.
        
        Args:
            files: Список словарей с информацией о файлах
            main_techs: Список основных технологий
            
        Returns:
            List с названиями фреймворков
        """
        frameworks = []
        
        # Маркеры для определения фреймворков
        framework_markers = {
            "python": {
                "django": ["django", "settings.py", "urls.py", "wsgi.py"],
                "flask": ["flask", "app.run(", "@app.route"],
                "fastapi": ["fastapi", "from fastapi import"],
                "pytorch": ["torch", "import torch"],
                "tensorflow": ["tensorflow", "import tensorflow", "import tf"],
                "pandas": ["pandas", "import pandas as pd"],
                "numpy": ["numpy", "import numpy as np"]
            },
            "javascript": {
                "react": ["react", "import React", "from 'react'", "React.Component"],
                "vue": ["vue", "import Vue", "new Vue("],
                "angular": ["angular", "@angular/core", "NgModule"],
                "express": ["express", "require('express')", "import express"],
                "next.js": ["next", "import next", "pages directory"]
            },
            "java": {
                "spring": ["org.springframework", "@Autowired", "@Controller"],
                "hibernate": ["org.hibernate", "@Entity", "SessionFactory"],
                "jakarta ee": ["jakarta", "javax.servlet", "@WebServlet"]
            }
        }
        
        # Проходим по всем файлам и ищем маркеры фреймворков
        for tech in main_techs:
            if tech in framework_markers:
                for file_info in files:
                    file_content = file_info.get("content", "")
                    file_path = file_info.get("path", "")
                    
                    for framework, markers in framework_markers[tech].items():
                        for marker in markers:
                            if marker in file_content or marker in file_path:
                                if framework not in frameworks:
                                    frameworks.append(framework)
                                break
        
        return frameworks
    
    def _extract_dependency_files(self, files: List[Dict[str, Any]], tech_stack: Dict[str, Any]) -> List[Dict[str, Any]]:
        """
        Извлекает файлы с зависимостями на основе технологического стека.
        
        Args:
            files: Список словарей с информацией о файлах
            tech_stack: Информация о технологическом стеке
            
        Returns:
            List с файлами зависимостей
        """
        dependency_file_patterns = {
            "python": ["requirements.txt", "setup.py", "Pipfile", "pyproject.toml"],
            "javascript": ["package.json", "yarn.lock", "npm-shrinkwrap.json"],
            "java": ["pom.xml", "build.gradle"],
            "ruby": ["Gemfile", "Gemfile.lock"],
            "php": ["composer.json"],
            "rust": ["Cargo.toml"],
            "go": ["go.mod"]
        }
        
        dependency_files = []
        
        # Извлекаем файлы зависимостей для каждой технологии в стеке
        for tech in tech_stack.get("main_languages", []):
            if tech in dependency_file_patterns:
                patterns = dependency_file_patterns[tech]
                
                for file_info in files:
                    file_path = file_info.get("path", "")
                    
                    for pattern in patterns:
                        if pattern in file_path or file_path.endswith(pattern):
                            dependency_files.append(file_info)
                            break
        
        return dependency_files
    
    async def _parse_dependencies(self, file_info: Dict[str, Any], tech_stack: Dict[str, Any]) -> List[Dict[str, Any]]:
        """
        Парсит файл зависимостей для извлечения информации о зависимостях.
        
        Args:
            file_info: Словарь с информацией о файле
            tech_stack: Информация о технологическом стеке
            
        Returns:
            List словарей с информацией о зависимостях
        """
        file_path = file_info.get("path", "")
        file_content = file_info.get("content", "")
        
        dependencies = []
        
        # Парсим зависимости в зависимости от типа файла
        if "requirements.txt" in file_path:
            dependencies = self._parse_requirements_txt(file_content)
        elif "package.json" in file_path:
            dependencies = self._parse_package_json(file_content)
        elif "pom.xml" in file_path:
            dependencies = self._parse_pom_xml(file_content)
        elif "build.gradle" in file_path:
            dependencies = self._parse_gradle(file_content)
        elif "Gemfile" in file_path and not file_path.endswith(".lock"):
            dependencies = self._parse_gemfile(file_content)
        elif "Cargo.toml" in file_path:
            dependencies = self._parse_cargo_toml(file_content)
        elif "go.mod" in file_path:
            dependencies = self._parse_go_mod(file_content)
        else:
            # Для других форматов используем Claude API для извлечения зависимостей
            dependencies = await self._extract_dependencies_with_claude(file_path, file_content)
        
        return dependencies
    
    def _parse_requirements_txt(self, content: str) -> List[Dict[str, Any]]:
        """
        Парсит файл requirements.txt для Python.
        
        Args:
            content: Содержимое файла
            
        Returns:
            List словарей с информацией о зависимостях
        """
        dependencies = []
        
        for line in content.split("\n"):
            line = line.strip()
            
            # Пропускаем комментарии и пустые строки
            if not line or line.startswith("#"):
                continue
            
            # Пропускаем опции и ссылки на другие файлы
            if line.startswith("-r") or line.startswith("--"):
                continue
            
            # Извлекаем имя пакета и версию
            parts = re.split(r"[=<>~!]", line, 1)
            name = parts[0].strip()
            version = parts[1].strip() if len(parts) > 1 else "latest"
            
            dependencies.append({
                "name": name,
                "version": version,
                "type": "runtime"
            })
        
        return dependencies
    
    def _parse_package_json(self, content: str) -> List[Dict[str, Any]]:
        """
        Парсит файл package.json для JavaScript/Node.js.
        
        Args:
            content: Содержимое файла
            
        Returns:
            List словарей с информацией о зависимостях
        """
        dependencies = []
        
        try:
            import json
            data = json.loads(content)
            
            # Извлекаем основные зависимости
            if "dependencies" in data:
                for name, version in data["dependencies"].items():
                    dependencies.append({
                        "name": name,
                        "version": version,
                        "type": "runtime"
                    })
            
            # Извлекаем зависимости для разработки
            if "devDependencies" in data:
                for name, version in data["devDependencies"].items():
                    dependencies.append({
                        "name": name,
                        "version": version,
                        "type": "development"
                    })
        
        except Exception as e:
            logger.error(f"Ошибка при парсинге package.json: {str(e)}")
        
        return dependencies
    
    def _parse_pom_xml(self, content: str) -> List[Dict[str, Any]]:
        """
        Парсит файл pom.xml для Maven (Java).
        
        Args:
            content: Содержимое файла
            
        Returns:
            List словарей с информацией о зависимостях
        """
        dependencies = []
        
        try:
            # Извлекаем зависимости с помощью регулярных выражений
            # Это упрощенный подход, для полного парсинга XML лучше использовать XML-парсер
            dependency_pattern = r"<dependency>.*?<groupId>(.*?)</groupId>.*?<artifactId>(.*?)</artifactId>.*?<version>(.*?)</version>.*?</dependency>"
            
            for match in re.finditer(dependency_pattern, content, re.DOTALL):
                group_id, artifact_id, version = match.groups()
                
                dependencies.append({
                    "name": f"{group_id}:{artifact_id}",
                    "version": version,
                    "type": "runtime"
                })
        
        except Exception as e:
            logger.error(f"Ошибка при парсинге pom.xml: {str(e)}")
        
        return dependencies
    
    def _parse_gradle(self, content: str) -> List[Dict[str, Any]]:
        """
        Парсит файл build.gradle для Gradle (Java).
        
        Args:
            content: Содержимое файла
            
        Returns:
            List словарей с информацией о зависимостях
        """
        dependencies = []
        
        try:
            # Извлекаем зависимости с помощью регулярных выражений
            dependency_pattern = r"(implementation|testImplementation|api|compileOnly|runtimeOnly)\s+['\"]([^'\"]+)['\"]"
            
            for match in re.finditer(dependency_pattern, content):
                scope, dependency_string = match.groups()
                
                # Определяем тип зависимости
                dep_type = "runtime"
                if "test" in scope.lower():
                    dep_type = "test"
                elif "compile" in scope.lower():
                    dep_type = "compile"
                
                # Если есть разделение на группу и артефакт
                if ":" in dependency_string:
                    parts = dependency_string.split(":")
                    name = ":".join(parts[:-1])
                    version = parts[-1]
                else:
                    name = dependency_string
                    version = "unspecified"
                
                dependencies.append({
                    "name": name,
                    "version": version,
                    "type": dep_type
                })
        
        except Exception as e:
            logger.error(f"Ошибка при парсинге build.gradle: {str(e)}")
        
        return dependencies
    
    def _parse_gemfile(self, content: str) -> List[Dict[str, Any]]:
        """
        Парсит Gemfile для Ruby.
        
        Args:
            content: Содержимое файла
            
        Returns:
            List словарей с информацией о зависимостях
        """
        dependencies = []
        
        try:
            # Извлекаем зависимости с помощью регулярных выражений
            gem_pattern = r"gem\s+['\"]([^'\"]+)['\"](?:,\s*['\"]([^'\"]+)['\"])?"
            
            for match in re.finditer(gem_pattern, content):
                name, version = match.groups()
                
                dependencies.append({
                    "name": name,
                    "version": version or "latest",
                    "type": "runtime"
                })
        
        except Exception as e:
            logger.error(f"Ошибка при парсинге Gemfile: {str(e)}")
        
        return dependencies
    
    def _parse_cargo_toml(self, content: str) -> List[Dict[str, Any]]:
        """
        Парсит Cargo.toml для Rust.
        
        Args:
            content: Содержимое файла
            
        Returns:
            List словарей с информацией о зависимостях
        """
        dependencies = []
        
        try:
            # Ищем секцию [dependencies]
            in_dependencies = False
            
            for line in content.split("\n"):
                line = line.strip()
                
                if not line or line.startswith("#"):
                    continue
                
                if line == "[dependencies]":
                    in_dependencies = True
                    continue
                
                if line.startswith("[") and line.endswith("]"):
                    in_dependencies = False
                    continue
                
                if in_dependencies and "=" in line:
                    parts = line.split("=", 1)
                    name = parts[0].strip()
                    version_part = parts[1].strip()
                    
                    # Удаляем кавычки и фигурные скобки из версии
                    version_part = version_part.strip('",{}')
                    
                    if "version" in version_part:
                        version_match = re.search(r"version\s*=\s*[\'\"]([^\'\"]+)", version_part)
                        version = version_match.group(1) if version_match else "latest"
                    else:
                        version = version_part
                    
                    dependencies.append({
                        "name": name,
                        "version": version,
                        "type": "runtime"
                    })
        
        except Exception as e:
            logger.error(f"Ошибка при парсинге Cargo.toml: {str(e)}")
        
        return dependencies
    
    def _parse_go_mod(self, content: str) -> List[Dict[str, Any]]:
        """
        Парсит go.mod для Go.
        
        Args:
            content: Содержимое файла
            
        Returns:
            List словарей с информацией о зависимостях
        """
        dependencies = []
        
        try:
            # Ищем строки с require
            require_pattern = r"require\s+([^\s]+)\s+([^\s]+)"
            
            for match in re.finditer(require_pattern, content):
                name, version = match.groups()
                
                dependencies.append({
                    "name": name,
                    "version": version,
                    "type": "runtime"
                })
            
            # Ищем блоки require
            block_pattern = r"require\s+\((.*?)\)"
            block_matches = re.finditer(block_pattern, content, re.DOTALL)
            
            for block_match in block_matches:
                block = block_match.group(1)
                
                for line in block.split("\n"):
                    line = line.strip()
                    
                    if not line or line.startswith("//"):
                        continue
                    
                    parts = line.split()
                    if len(parts) >= 2:
                        name, version = parts[0], parts[1]
                        
                        dependencies.append({
                            "name": name,
                            "version": version,
                            "type": "runtime"
                        })
        
        except Exception as e:
            logger.error(f"Ошибка при парсинге go.mod: {str(e)}")
        
        return dependencies
    
    async def _extract_dependencies_with_claude(self, file_path: str, file_content: str) -> List[Dict[str, Any]]:
        """
        Использует Claude API для извлечения зависимостей из неизвестного формата файла.
        
        Args:
            file_path: Путь к файлу
            file_content: Содержимое файла
            
        Returns:
            List словарей с информацией о зависимостях
        """
        try:
            # Формируем промпт для Claude API
            prompt = f"""
            Извлеки список зависимостей из следующего файла:
            
            Файл: {file_path}
            
            ```
            {file_content}
            ```
            
            Представь результат в формате JSON-массива, где каждый элемент имеет следующую структуру:
            {{
                "name": "имя_зависимости",
                "version": "версия_зависимости",
                "type": "тип_зависимости" // (runtime, development, test и т.д.)
            }}
            
            Выведи только JSON-массив без дополнительных пояснений.
            """
            
            # Вызываем Claude API
            response = await self.claude_api.send_request(prompt)
            
            # Извлекаем JSON из ответа
            json_str = self._extract_json_array(response)
            
            if json_str:
                import json
                dependencies = json.loads(json_str)
                return dependencies
            
            return []
        
        except Exception as e:
            logger.error(f"Ошибка при извлечении зависимостей с помощью Claude API: {str(e)}")
            return []
    
    def _extract_json_array(self, text: str) -> str:
        """
        Извлекает JSON-массив из текстового ответа Claude API.
        
        Args:
            text: Текст, содержащий JSON-массив
            
        Returns:
            Строка с JSON-массивом или пустая строка в случае ошибки
        """
        try:
            # Ищем открывающую и закрывающую квадратные скобки
            start_index = text.find("[")
            end_index = text.rfind("]")
            
            if start_index == -1 or end_index == -1 or start_index > end_index:
                return ""
            
            return text[start_index:end_index+1]
        
        except Exception as e:
            logger.error(f"Ошибка при извлечении JSON-массива: {str(e)}")
            return ""
    
    async def _get_dependency_recommendations(self, dependencies: List[Dict[str, Any]], tech_stack: Dict[str, Any]) -> str:
        """
        Получает рекомендации по зависимостям с использованием Claude API.
        
        Args:
            dependencies: Список зависимостей
            tech_stack: Информация о технологическом стеке
            
        Returns:
            Строка с рекомендациями
        """
        try:
            # Формируем промпт для Claude API
            main_languages = ", ".join(tech_stack.get("main_languages", []))
            frameworks = ", ".join(tech_stack.get("frameworks", []))
            
            deps_text = "\n".join([f"- {dep['name']} ({dep.get('version', 'unknown version')})" for dep in dependencies[:20]])
            
            prompt = f"""
            Проанализируй список зависимостей проекта и предоставь рекомендации.
            
            Технологический стек:
            - Основные языки: {main_languages or "Не определено"}
            - Фреймворки: {frameworks or "Не определено"}
            
            Основные зависимости (до 20 первых):
            {deps_text}
            
            Предоставь рекомендации по следующим аспектам:
            1. Устаревшие или потенциально небезопасные зависимости
            2. Возможные конфликты между зависимостями
            3. Рекомендуемые обновления или альтернативы
            4. Оптимизация зависимостей для улучшения производительности
            
            Форматируй ответ по разделам и дай конкретные, практичные рекомендации.
            """
            
            # Вызываем Claude API
            response = await self.claude_api.send_request(prompt)
            
            return response
        
        except Exception as e:
            logger.error(f"Ошибка при получении рекомендаций по зависимостям: {str(e)}")
            return "Не удалось сформировать рекомендации из-за ошибки."