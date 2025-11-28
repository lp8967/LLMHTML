import google.generativeai as genai
import logging
import time
import os
from app.config import GEMINI_API_KEY

logger = logging.getLogger(__name__)

class GeminiClient:
    def __init__(self):
        if not GEMINI_API_KEY:
            raise ValueError("GEMINI_API_KEY not found in environment variables")
        
        # 🟢 ПРАВИЛЬНАЯ ИНИЦИАЛИЗАЦИЯ
        genai.configure(api_key=GEMINI_API_KEY)
        self.model = genai.GenerativeModel('gemini-2.0-flash')  # Используем стабильную модель
        
        logger.info(f"Gemini client initialized with model: gemini-2.0-flash")
    
    def generate_response(self, prompt: str, temperature: float = 0.1) -> str:
        max_retries = 3
        retry_delay = 2
        
        for attempt in range(max_retries):
            try:
                # 🟢 ПРАВИЛЬНЫЙ ВЫЗОВ
                response = self.model.generate_content(
                    prompt,
                    generation_config=genai.types.GenerationConfig(
                        temperature=temperature,
                        top_p=0.8,
                        top_k=40,
                        max_output_tokens=2048,
                    )
                )
                
                if response.text:
                    return response.text
                else:
                    logger.warning("Empty response from Gemini")
                    return "I couldn't generate a response for this question. Please try again."
                
            except Exception as e:
                logger.warning(f"Gemini API attempt {attempt + 1} failed: {str(e)}")
                if attempt < max_retries - 1:
                    time.sleep(retry_delay * (attempt + 1))
                else:
                    logger.error(f"All Gemini API attempts failed: {str(e)}")
                    return "Sorry, I'm experiencing technical difficulties. Please try again later."

gemini_client = GeminiClient()
