# ai_service.py

from google import genai
from google.genai.errors import APIError
# ❌ ИЗМЕНЕНО: Импортируем список ключей
from config import GEMINI_API_KEYS, logger
import itertools
import time 

# Создаем глобальный итератор для циклического выбора ключей (Round-Robin)
key_cycle = itertools.cycle(GEMINI_API_KEYS)


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
    """Центральная функция для обращения к Gemini API с ротацией ключей."""
    
    max_retries = len(GEMINI_API_KEYS)
    
    for attempt in range(max_retries):
        
        # 1. Получаем следующий ключ из глобального цикла
        current_api_key = next(key_cycle)
        logger.info(f"🔑 Попытка {attempt + 1}/{max_retries}. Используется ключ, начинающийся с {current_api_key[:10]}...")
        
        try:
            # 2. Инициализируем клиента с текущим ключом
            client = genai.Client(api_key=current_api_key)
            
            # 3. Выполняем асинхронный вызов API
            response = await client.models.generate_content_async( # ✅ ИСПРАВЛЕНО: Теперь используется async-метод
                model=model,
                contents=prompt
            )
            
            # 4. Если успех, возвращаем текст
            logger.info(f"✅ Успешная генерация с ключом {current_api_key[:10]}...")
            return response.text
            
        except APIError as e:
            # 5. Если ошибка API (например, лимит, или ключ недействителен)
            logger.error(f"❌ Ошибка API с ключом {current_api_key[:10]}...: {e}")
            
            if attempt == max_retries - 1:
                logger.error("Все доступные API ключи исчерпаны или не работают.")
                return "Извините, все наши генеративные сервисы сейчас перегружены или недоступны (ошибка API). Пожалуйста, попробуйте позже."
            
            time.sleep(1) # Пауза перед переключением на следующий ключ
            
        except Exception as e:
            # 6. Обработка других неожиданных ошибок
            logger.error(f"❌ Непредвиденная ошибка во время вызова API: {e}")
            return "Извините, произошла непредвиденная ошибка во время генерации текста."

    return "Не удалось получить ответ после всех попыток."
