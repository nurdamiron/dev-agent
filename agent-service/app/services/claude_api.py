import os
import json
import logging
import time
import anthropic
from typing import Dict, List, Any, Optional
from tenacity import retry, stop_after_attempt, wait_exponential, retry_if_exception_type

class ClaudeAPI:
    """
    Класс для взаимодействия с API Claude.
    """
    
    def __init__(self, api_key: Optional[str] = None, model: str = "claude-3-7-sonnet-20250219"):
        """
        Инициализирует экземпляр ClaudeAPI.
        
        Args:
            api_key: API-ключ для Claude. Если не указан, берется из переменной окружения ANTHROPIC_API_KEY.
            model: Модель Claude для использования.
        """
        self.logger = logging.getLogger(__name__)
        
        # Получаем API-ключ
        self.api_key = api_key or os.environ.get("CLAUDE_API_KEY")
        if not self.api_key:
            self.logger.error("API-ключ не найден. Укажите его в параметре api_key или в переменной окружения CLAUDE_API_KEY.")
            raise ValueError("API-ключ не найден")
        
        # Инициализируем клиент Claude API
        self.model = model
        self.client = anthropic.Client(api_key=self.api_key)
        
        # Хранилище для беседы (опционально, для сохранения контекста)
        self.conversation_history = []
        
        self.logger.info(f"ClaudeAPI инициализирован с моделью {model}")
    
    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=2, max=10),
        retry=retry_if_exception_type((anthropic.RateLimitError, anthropic.APITimeoutError)),
        reraise=True
    )
    async def send_request(self, prompt: str, max_tokens: int = 4000, use_conversation_history: bool = False) -> str:
        """
        Отправляет запрос к API Claude и возвращает ответ.
        
        Args:
            prompt: Текст промпта для отправки.
            max_tokens: Максимальное количество токенов в ответе.
            use_conversation_history: Использовать ли историю беседы для контекста.
            
        Returns:
            str: Ответ от API Claude.
        """
        self.logger.info(f"Отправка запроса к Claude API (модель: {self.model})")
        
        try:
            # Подготовка сообщений
            messages = []
            
            # Добавляем историю беседы, если требуется
            if use_conversation_history and self.conversation_history:
                messages = self.conversation_history.copy()
            
            # Добавляем текущий промпт
            messages.append({"role": "user", "content": prompt})
            
            # Отправляем запрос
            start_time = time.time()
            
            response = await self.client.messages.create(
                model=self.model,
                max_tokens=max_tokens,
                messages=messages
            )
            
            elapsed_time = time.time() - start_time
            self.logger.info(f"Запрос выполнен за {elapsed_time:.2f} секунд")
            
            # Извлекаем текст ответа
            answer_text = response.content[0].text
            
            # Сохраняем сообщения в историю беседы, если требуется
            if use_conversation_history:
                self.conversation_history.append({"role": "user", "content": prompt})
                self.conversation_history.append({"role": "assistant", "content": answer_text})
            
            return answer_text
        
        except Exception as e:
            self.logger.error(f"Ошибка при запросе к API: {str(e)}")
            raise ValueError(f"Ошибка запроса к API Claude: {str(e)}")