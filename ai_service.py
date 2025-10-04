# ai_service.py

from google import genai
from google.genai.errors import APIError
from config import GEMINI_API_KEYS, logger
import itertools
import time 

key_cycle = itertools.cycle(GEMINI_API_KEYS)

MASTER_PROMPT = """
# MASTER-ПРОМПТ: PRO-КОПИРАЙТЕР 5.1
[... (Полный текст вашего промпта) ...]
"""

async def call_gemini_api(prompt: str, model: str = 'gemini-2.5-flash') -> str:
    """Центральная функция для обращения к Gemini API с ротацией ключей."""
    
    max_retries = len(GEMINI_API_KEYS)
    
    for attempt in range(max_retries):
        
        current_api_key = next(key_cycle)
        logger.info(f"🔑 Попытка {attempt + 1}/{max_retries}. Используется ключ, начинающийся с {current_api_key[:10]}...")
        
        try:
            client = genai.Client(api_key=current_api_key)
            
            response = await client.models.generate_content_async(
                model=model,
                contents=prompt
            )
            
            logger.info(f"✅ Успешная генерация с ключом {current_api_key[:10]}...")
            return response.text
            
        except APIError as e:
            logger.error(f"❌ Ошибка API с ключом {current_api_key[:10]}...: {e}")
            
            if attempt == max_retries - 1:
                logger.error("Все доступные API ключи исчерпаны или не работают.")
                return "Извините, все наши генеративные сервисы сейчас перегружены или недоступны (ошибка API). Пожалуйста, попробуйте позже."
            
            time.sleep(1)
            
        except Exception as e:
            logger.error(f"❌ Непредвиденная ошибка во время вызова API: {e}")
            return "Извините, произошла непредвиденная ошибка во время генерации текста."

    return "Не удалось получить ответ после всех попыток."
