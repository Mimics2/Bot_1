# payment_service.py

from telegram import Update
from telegram.ext import ContextTypes
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
    # Возвращаем False, чтобы сообщить handlers.py о необходимости перехода в GETTING_ACCESS_CODE
    return False

async def handle_access_code(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Проверяет введенный пользователем код доступа."""
    
    user_input = update.message.text.strip().upper() # Приводим к верхнему регистру для гибкости
    user_id = update.effective_user.id
    
    # Импортируем CHOOSING_ACTION из config для возврата в главное меню
    from config import CHOOSING_ACTION
    
    if user_input == SECRET_ACCESS_CODE.upper():
        # Код верен: даем доступ и возвращаемся в главное меню
        MOCK_SUBSCRIPTION_DB.add(user_id)
        await update.message.reply_text(
            "🥳 **ПОЗДРАВЛЯЮ! Доступ активирован.**\n"
            "Нажмите /start, чтобы начать работу.",
            parse_mode='Markdown'
        )
        return CHOOSING_ACTION
        
    else:
        # Код неверен: просим попробовать снова
        await update.message.reply_text(
            "❌ **Неверный код.** Пожалуйста, проверьте код и введите его еще раз. "
            "Или нажмите /start, чтобы отменить."
        )
        # Остаемся в этом состоянии, пока пользователь не введет /start или правильный код
        return -1 
