# ai_service.py

from google import genai
from google.genai.errors import APIError
from config import GEMINI_API_KEY, logger

# Ваш MASTER-ПРОМПТ (оформлен как многострочная строка для удобства)
MASTER_PROMPT = """
# MASTER-ПРОМПТ: PRO-КОПИРАЙТЕР 5.1
[... (Оставьте ваш полный промпт здесь) ...]
"""

async def call_gemini_api(prompt: str, model: str = 'gemini-2.5-flash') -> str:
    """Центральная функция для обращения к Gemini API. Добавлена обработка ошибок."""
    try:
        # 🔥 ПРОВЕРКА КЛЮЧА
        if not GEMINI_API_KEY or 'AIzaSy' not in GEMINI_API_KEY:
            raise APIError("Ключ API отсутствует или выглядит недействительным.")
            
        client = genai.Client(api_key=GEMINI_API_KEY)
        
        response = client.models.generate_content(
            model=model,
            contents=prompt,
        )

        return response.text

    except APIError as e:
        logger.error(f"Ошибка Gemini API: {e}")
        return "❌ ОШИБКА API: Не удалось получить ответ от ИИ. Вероятно, ваш **ключ API недействителен** или истек срок действия. Пожалуйста, замените его в config.py."
    except Exception as e:
        logger.error(f"Неизвестная ошибка при вызове Gemini: {e}")
        return f"❌ ОШИБКА: Произошла непредвиденная ошибка при генерации: {e}"
