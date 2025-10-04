# ai_service.py

from google import genai
from google.genai.errors import APIError
# Импорт config происходит в handlers.py и main.py
# Здесь импортируем только то, что нужно для API
from config import GEMINI_API_KEY, logger 

# Ваш MASTER-ПРОМПТ остается без изменений
MASTER_PROMPT = """
# MASTER-ПРОМПТ: PRO-КОПИРАЙТЕР 5.1
[... (Полный текст вашего промпта) ...]
"""

async def call_gemini_api(prompt: str, model: str = 'gemini-2.5-flash') -> str:
    """Центральная функция для обращения к Gemini API с обработкой ошибок."""
    try:
        # 1. Проверка на заведомо недействительный/стандартный ключ
        if not GEMINI_API_KEY or 'AIzaSy' in GEMINI_API_KEY[:6] and len(GEMINI_API_KEY) < 30:
            raise APIError("Ключ API отсутствует или выглядит недействительным.")
            
        client = genai.Client(api_key=GEMINI_API_KEY)
        
        # 2. Вызов API
        response = client.models.generate_content(
            model=model,
            contents=prompt,
        )
        return response.text
        
    except APIError as e:
        logger.error(f"❌ Ошибка Gemini API (API key/Timeout): {e}")
        # Возвращаем стандартизированное сообщение для пользователя
        return "❌ ОШИБКА API: Не удалось получить ответ от ИИ. Вероятно, ваш **ключ API недействителен** или произошел таймаут (бот завис)."
    except Exception as e:
        logger.error(f"❌ Общая ошибка AI: {e}")
        return f"❌ ОШИБКА: Произошла непредвиденная ошибка при генерации: {e}"
