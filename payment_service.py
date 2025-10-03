# payment_service.py

from telegram import Update
from telegram.ext import ContextTypes
# Импортируем SECRET_ACCESS_CODE и цену для отображения
from config import logger, SECRET_ACCESS_CODE, ACCESS_PRICE_DISPLAY 

# Mock-база данных для хранения ID пользователей с активным доступом
MOCK_SUBSCRIPTION_DB = set() 

async def check_access(user_id: int, update: Update, context: ContextTypes.DEFAULT_TYPE) -> bool:
    """Проверяет, есть ли у пользователя PRO-доступ."""
    
    if user_id in MOCK_SUBSCRIPTION_DB:
        return True
    
    # Если доступа нет, просим ввести код
    await update.message.reply_text(
        "🔒 **Доступ ограничен.**\n"
        f"Для использования PRO-функций CopiBot (Gemini) требуется активация.\n"
        f"Чтобы получить доступ, введите **секретный код** или обратитесь к администратору (Цена: {ACCESS_PRICE_DISPLAY}).",
        parse_mode='Markdown'
    )
    # Возвращаем False, чтобы вызвать переход в состояние ожидания кода
    return False

async def handle_access_code(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Проверяет введенный пользователем код доступа."""
    
    user_input = update.message.text.strip()
    user_id = update.effective_user.id
    
    if user_input == SECRET_ACCESS_CODE:
        # Код верен: даем доступ и завершаем состояние
        MOCK_SUBSCRIPTION_DB.add(user_id)
        await update.message.reply_text(
            "🥳 **ПОЗДРАВЛЯЮ! Доступ активирован.**\n"
            "Нажмите `/start`, чтобы начать работу.",
            parse_mode='Markdown'
        )
        return -1 # Возвращаемся в начало ConversationHandler (или используем start)
        
    else:
        # Код неверен: просим попробовать снова или отменить
        await update.message.reply_text(
            "❌ **Неверный код.** Пожалуйста, проверьте код и введите его еще раз. "
            "Или нажмите /start, чтобы отменить."
        )
        return -1 # Для простоты, возвращаем к началу.

