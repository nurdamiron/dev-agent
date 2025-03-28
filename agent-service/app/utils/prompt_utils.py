# agent-service/app/utils/prompt_utils.py

import os
import logging
import json
from typing import Dict, Any, List, Optional
from pathlib import Path
from app.core.config import settings

logger = logging.getLogger(__name__)

def load_prompt(filename: str) -> str:
    """
    Загружает шаблон промпта из файла.
    
    Args:
        filename: Имя файла в директории промптов
        
    Returns:
        str: Содержимое промпта
    """
    try:
        # Определяем путь к файлу промпта
        prompt_path = Path(settings.PROMPTS_DIR) / filename
        
        with open(prompt_path, 'r', encoding='utf-8') as file:
            content = file.read()
        
        logger.info(f"Промпт '{filename}' успешно загружен")
        return content
    
    except Exception as e:
        logger.error(f"Ошибка при загрузке промпта '{filename}': {str(e)}")
        # Возвращаем базовый промпт в случае ошибки
        return "Ответь на следующий вопрос пользователя: {user_message}"

def format_context_for_prompt(context: Dict[str, Any]) -> str:
    """
    Форматирует контекст для вставки в промпт.
    
    Args:
        context: Словарь с контекстом
        
    Returns:
        str: Отформатированный контекст для вставки в промпт
    """
    formatted_context = []
    
    # Если есть информация о проекте
    if "project" in context:
        project = context["project"]
        formatted_context.append(f"## Информация о проекте\n")
        formatted_context.append(f"Название: {project.get('name', 'Неизвестно')}")
        formatted_context.append(f"Описание: {project.get('description', 'Нет описания')}")
        if "repository_url" in project:
            formatted_context.append(f"Репозиторий: {project['repository_url']}")
    
    # Если есть информация о файлах
    if "files" in context:
        formatted_context.append(f"\n## Контекст файлов\n")
        for file_info in context["files"]:
            formatted_context.append(f"### Файл: {file_info.get('path', 'Неизвестный файл')}")
            if "content" in file_info:
                formatted_context.append("```")
                formatted_context.append(file_info["content"])
                formatted_context.append("```")
            else:
                formatted_context.append("Содержимое файла не предоставлено.")
    
    # Если есть информация об ошибках
    if "error" in context:
        formatted_context.append(f"\n## Информация об ошибке\n")
        formatted_context.append("```")
        formatted_context.append(context["error"])
        formatted_context.append("```")
    
    # Если есть дополнительный контекст
    if "additional_context" in context:
        formatted_context.append(f"\n## Дополнительный контекст\n")
        additional = context["additional_context"]
        if isinstance(additional, dict):
            formatted_context.append(json.dumps(additional, ensure_ascii=False, indent=2))
        else:
            formatted_context.append(str(additional))
    
    return "\n".join(formatted_context)

def build_system_prompt(task_type: str, 
                       context: Optional[Dict[str, Any]] = None) -> str:
    """
    Создает системный промпт для Claude на основе типа задачи и контекста.
    
    Args:
        task_type: Тип задачи (code_analysis, code_generation, error_fixing и т.д.)
        context: Дополнительный контекст
        
    Returns:
        str: Системный промпт для Claude
    """
    base_prompt = (
        "Ты опытный AI-ассистент разработчика, специализирующийся на анализе кода, "
        "генерации кода и решении проблем программирования. "
        "Ты общаешься ясно и структурированно, предоставляя полезные и практичные ответы."
    )
    
    if task_type == "code_analysis":
        system_prompt = base_prompt + (
            "\n\nПри анализе кода фокусируйся на структуре, паттернах проектирования, "
            "потенциальных проблемах и возможностях улучшения. "
            "Дай подробное объяснение, как код работает, и предложи конкретные улучшения, "
            "где это уместно."
        )
    
    elif task_type == "code_generation":
        system_prompt = base_prompt + (
            "\n\nПри генерации кода пиши чистый, хорошо структурированный и документированный код. "
            "Следуй современным практикам программирования и учитывай предоставленный контекст. "
            "Поясняй ключевые части решения и обосновывай принятые решения."
        )
    
    elif task_type == "error_fixing":
        system_prompt = base_prompt + (
            "\n\nПри исправлении ошибок сначала идентифицируй корень проблемы, "
            "затем предложи конкретное исправление. "
            "Объясни, почему возникла ошибка и как твое решение её устраняет. "
            "Используй конкретные примеры кода с исправлениями."
        )
    
    elif task_type == "git_operation":
        system_prompt = base_prompt + (
            "\n\nПри работе с Git объясняй каждый шаг и команду, "
            "чтобы пользователь понимал, что происходит. "
            "Учитывай особенности репозитория и контекст проекта. "
            "Предлагай безопасные и эффективные решения."
        )
    
    else:  # general_question
        system_prompt = base_prompt + (
            "\n\nОтвечай на вопросы о программировании, инструментах, библиотеках "
            "и технологиях разработки ПО. Давай точную и актуальную информацию, "
            "при необходимости приводя примеры кода."
        )
    
    return system_prompt