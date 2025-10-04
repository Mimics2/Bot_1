# ai_service.py

from google import genai
from google.genai.errors import APIError
from config import GEMINI_API_KEY, logger

# Ваш MASTER-ПРОМПТ остается здесь, без изменений.
MASTER_PROMPT = """
# MASTER-ПРОМПТ: PRO-КОПИРАЙТЕР 5.1
[... (Полный текст вашего промпта) ...]
"""

async def call_gemini_api(prompt: str, model: str = 'gemini-2.5-flash') -> str:
    """Центральная функция для обращения к Gemini API с надежной обработкой ошибок."""
    try:
        # 1. Проверка на недействительный ключ
        if not GEMINI_API_KEY or 'ВАШ_РЕАЛЬНЫЙ' in GEMINI_API_KEY:
            raise APIError("❌ ОШИБКА: Ключ API не установлен в config.py.")
            
        client = genai.Client(api_key=GEMINI_API_KEY)
        
        response = client.models.generate_content(
            model=model,
            contents=prompt,
        )
        return response.text

    except APIError as e:
        logger.error(f"❌ Ошибка Gemini API (API key/Timeout): {e}")
        # Возвращаем понятное сообщение вместо зависания
        return "❌ ОШИБКА API: Не удалось получить ответ от ИИ. Вероятно, ваш **ключ API недействителен** или произошел таймаут (бот завис)."
    except Exception as e:
        logger.error(f"❌ Общая ошибка AI: {e}")
        return f"❌ ОШИБКА: Произошла непредвиденная ошибка при генерации: {e}"
