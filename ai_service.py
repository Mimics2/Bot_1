# ai_service.py

from google import genai
from google.genai.errors import APIError
# 🔥 ИЗМЕНЕНО: Импортируем список ключей (хотя в config.py сейчас один, лучше подготовиться)
from config import GEMINI_API_KEY, logger, GEMINI_API_KEYS
import itertools
import time 

# Создаем глобальный итератор для циклического выбора ключей (Round-Robin)
# GEMINI_API_KEYS должен быть определен в config.py как список
try:
    key_cycle = itertools.cycle(GEMINI_API_KEYS)
except NameError:
    # Если GEMINI_API_KEYS не определен как список, используем одиночный ключ
    key_cycle = itertools.cycle([GEMINI_API_KEY])


# Ваш MASTER-ПРОМПТ 
MASTER_PROMPT = """
# MASTER-ПРОМПТ: PRO-КОПИРАЙТЕР 5.1
[... (Полный текст вашего промпта) ...]
"""

async def call_gemini_api(prompt: str, model: str = 'gemini-2.5-flash') -> str:
    """Центральная функция для обращения к Gemini API с ротацией ключей."""
    
    # Определение списка ключей (если key_cycle был создан на основе списка)
    if hasattr(key_cycle, 'next'): # Проверка, что это итератор
        keys = GEMINI_API_KEYS if 'GEMINI_API_KEYS' in globals() else [GEMINI_API_KEY]
    else:
        keys = [GEMINI_API_KEY]
        
    max_retries = len(keys)
    
    for attempt in range(max_retries):
        
        # 1. Получаем следующий ключ 
        current_api_key = next(key_cycle)
        logger.info(f"🔑 Попытка {attempt + 1}/{max_retries}. Используется ключ, начинающийся с {current_api_key[:10]}...")
        
        try:
            # 2. Инициализируем клиента с текущим ключом
            client = genai.Client(api_key=current_api_key)
            
            # 3. Выполняем асинхронный вызов API
            response = client.models.generate_content(
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
