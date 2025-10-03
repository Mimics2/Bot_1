# handlers.py

from telegram import Update, ReplyKeyboardMarkup, ReplyKeyboardRemove
from telegram.ext import ContextTypes, ConversationHandler
# Импортируем НОВОЕ состояние GETTING_ACCESS_CODE
from config import CHOOSING_THEME, CHOOSING_GENRE, GETTING_TOPIC, GETTING_CORRECTION, CHOOSING_ACTION, GETTING_ACCESS_CODE, logger 
from ai_service import MASTER_PROMPT, call_gemini_api
# Импортируем новую функцию для обработки кода
from payment_service import check_access, handle_access_code 

# --- КЛАВИАТУРЫ ---
main_keyboard = [["🆕 Начать новый пост", "⚙️ Корректировать предыдущий"], ["❌ Отмена"]]
theme_keyboard = [["Бизнес", "Технологии", "Путешествия", "Здоровье"], ["Личный бренд", "Другая тема", "⬅️ Назад"]]
genre_keyboard = [["Информационный (обучение)", "Продающий (AIDA)", "Развлекательный (лайфхак)"], ["Сторителлинг (личная история)", "Провокация (хайп)", "⬅️ Назад"]]


# ... (функции start, choose_theme, choose_genre, generate_post, correct_post, cancel остаются без изменений) ...

async def choose_action(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Обрабатывает выбор 'Начать новый пост' или 'Корректировать'."""
    text = update.message.text
    user_id = update.effective_user.id
    
    if text in ["🆕 Начать новый пост", "⚙️ Корректировать предыдущий"]:
        
        if not await check_access(user_id, update, context):
            # Если доступа нет, переходим в состояние ожидания кода
            await update.message.reply_text("Введите секретный код:", reply_markup=ReplyKeyboardRemove())
            return GETTING_ACCESS_CODE
            
        # Если доступ есть, продолжаем, как раньше
        if text == "🆕 Начать новый пост":
            await update.message.reply_text(
                "Отлично! Теперь выберите основную тему вашего поста:",
                reply_markup=ReplyKeyboardMarkup(theme_keyboard, one_time_keyboard=True, resize_keyboard=True)
            )
            return CHOOSING_THEME
        
        elif text == "⚙️ Корректировать предыдущий":
            await update.message.reply_text(
                "Пожалуйста, отправьте мне текст, который нужно скорректировать, "
                "и **подробно укажите**, что именно нужно изменить.",
                reply_markup=ReplyKeyboardRemove()
            )
            return GETTING_CORRECTION
    
    await update.message.reply_text("Пожалуйста, выберите действие на клавиатуре.")
    return CHOOSING_ACTION
