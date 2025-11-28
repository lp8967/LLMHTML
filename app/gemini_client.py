import google.generativeai as genai
import logging
import time
from app.config import GEMINI_API_KEY, LLM_MODEL, GEMINI_SAFETY_SETTINGS

logger = logging.getLogger(__name__)

class GeminiClient:
    def __init__(self):
        if not GEMINI_API_KEY:
            raise ValueError("GEMINI_API_KEY not found in environment variables")
        
        genai.configure(api_key=GEMINI_API_KEY)
        self.model = genai.GenerativeModel(LLM_MODEL)
        
        self.safety_settings = GEMINI_SAFETY_SETTINGS
        
        logger.info("Gemini client initialized successfully")
    
    def generate_response(self, prompt: str, temperature: float = 0.1) -> str:
        max_retries = 3
        retry_delay = 2
        
        for attempt in range(max_retries):
            try:
                response = self.model.generate_content(
                    prompt,
                    generation_config=genai.types.GenerationConfig(
                        temperature=temperature,
                        top_p=0.8,
                        top_k=40,
                        max_output_tokens=2048,
                    ),
                    safety_settings=self.safety_settings
                )
                
                if response.prompt_feedback.block_reason:
                    block_reason = response.prompt_feedback.block_reason
                    logger.warning(f"Content blocked: {block_reason}")
                    return f"I cannot answer this question due to content safety restrictions. Please try rephrasing your question."
                
                if not response.parts:
                    logger.warning("Empty response from Gemini")
                    return "I couldn't generate a response for this question. Please try again."
                
                return response.text
                
            except Exception as e:
                logger.warning(f"Gemini API attempt {attempt + 1} failed: {str(e)}")
                if attempt < max_retries - 1:
                    time.sleep(retry_delay * (attempt + 1))
                else:
                    logger.error(f"All Gemini API attempts failed: {str(e)}")
                    return "Sorry, I'm experiencing technical difficulties. Please try again later."

gemini_client = GeminiClient()