# ai_service.py

from google import genai
from google.genai.errors import APIError
from config import GEMINI_API_KEY, logger

# Ваш MASTER-ПРОМПТ (оформлен как многострочная строка для удобства)
MASTER_PROMPT = """
# MASTER-ПРОМПТ: PRO-КОПИРАЙТЕР 5.1

## 1. РОЛЬ И ПРИНЦИПЫ (ROLE & PRINCIPLES)
[... (Полный текст вашего промпта) ...]
## 2. АНАЛИТИЧЕСКИЙ ЭТАП (Chain-of-Thought / CoT)
[... (Полный текст вашего промпта) ...]
## 3. ВХОДНЫЕ ДАННЫЕ ОТ ПОЛЬЗОВАТЕЛЯ (INPUT)
[... (Полный текст вашего промпта) ...]
1.  **Тема/Идея/Черновик (Пользовательский ввод):** {user_topic}
2.  **Основная Категория (Выбор кнопки):** {theme}
3.  **Жанр/Стиль (Выбор кнопки):** {genre}
4.  **Целевая аудитория (ЦА):** {audience}
5.  **Длина и Стиль:** {post_length}
6.  **Дополнительные пожелания:** {additional_wishes}
[... (Полный текст вашего промпта) ...]
## 5. ФОРМАТ ОТВЕТА (OUTPUT FORMAT)
[... (Полный текст вашего промпта) ...]
"""

async def call_gemini_api(prompt: str, model: str = 'gemini-2.5-flash') -> str:
    """Центральная функция для обращения к Gemini API."""
    try:
        client = genai.Client(api_key=GEMINI_API_KEY)
        response = client.models.generate_content(
            model=model,
            contents=prompt,
        )
        return response.text
    except APIError as e:
        logger.error(f"Gemini API Error: {e}")
        return "❌ Ошибка API Gemini. Проверьте ваш API ключ."
    except Exception as e:
        logger.error(f"General AI Error: {e}")
        return "❌ Произошла общая ошибка при генерации."

# ВАЖНО: Функции generate_post и correct_post перенесены в handlers.py 
# для сохранения логики ConversationHandler.
