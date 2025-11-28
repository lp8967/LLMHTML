from google.ai import generativelanguage as genai
import logging
import time
import os
from app.config import GEMINI_API_KEY

logger = logging.getLogger(__name__)

class GeminiClient:
    def __init__(self):
        if not GEMINI_API_KEY:
            raise ValueError("GEMINI_API_KEY not found in environment variables")
        
        # 🟢 Инициализация клиента с использованием нового API
        self.client = genai.Client(api_key=GEMINI_API_KEY)
        self.model = "gemini-2.5-flash"  # Прямое указание стабильной версии модели
        
        logger.info(f"Gemini client initialized with model: {self.model}")
    
    def generate_response(self, prompt: str, temperature: float = 0.1) -> str:
        max_retries = 3
        retry_delay = 2
        
        for attempt in range(max_retries):
            try:
                # 🟢 Правильный вызов через новое API
                response = self.client.models.generate_content(
                    model=self.model,
                    contents=prompt
                )
                
                # 🟢 Получение текста ответа
                if hasattr(response, 'text') and response.text:
                    return response.text
                else:
                    logger.warning("Empty or unexpected response from Gemini")
                    return "I couldn't generate a response for this question. Please try again."
                
            except Exception as e:
                logger.warning(f"Gemini API attempt {attempt + 1} failed: {str(e)}")
                if attempt < max_retries - 1:
                    time.sleep(retry_delay * (attempt + 1))
                else:
                    logger.error(f"All Gemini API attempts failed: {str(e)}")
                    return "Sorry, I'm experiencing technical difficulties. Please try again later."

gemini_client = GeminiClient()

