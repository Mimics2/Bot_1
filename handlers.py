# handlers.py

from telegram import Update, ReplyKeyboardMarkup, ReplyKeyboardRemove
from telegram.ext import ContextTypes, ConversationHandler
# ✅ ИСПРАВЛЕНО: Явный импорт всех необходимых констант
from config import (
    logger, CHOOSING_ACTION, CHOOSING_THEME, CHOOSING_GENRE, 
    GETTING_TOPIC, GETTING_CORRECTION, GETTING_ACCESS_CODE,
    main_keyboard, theme_keyboard, genre_keyboard
)
from ai_service import MASTER_PROMPT, call_gemini_api
# ✅ Импортируем функции и хранилище из payment_service
from payment_service import check_access, handle_access_code_flow, USERS_DATA, save_users_data


# --- ОБРАБОТЧИКИ ДИАЛОГА ---

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Начинает диалог с новым дизайном приветствия."""
    user_name = update.effective_user.first_name if update.effective_user.first_name else "Гость"
    
    await update.message.reply_text(
        f"👋 Привет, *{user_name}*! Я CopiBot, ваш личный ассистент на базе Gemini.\n\n"
        "Выберите действие, чтобы начать работу с контентом:",
        parse_mode='Markdown',
        reply_markup=ReplyKeyboardMarkup(main_keyboard, one_time_keyboard=True, resize_keyboard=True)
    )
    return CHOOSING_ACTION

async def choose_action(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Обрабатывает выбор действия и проверяет PRO-доступ."""
    text = update.message.text
    user_id = update.effective_user.id
    
    if text == "❌ Отмена": return await cancel(update, context) # Отмена
    
    # --- Проверка доступа для всех PRO-функций ---
    if text in ["✨ Новый пост", "⚙️ Корректировать текст"]:
        
        # Если доступа нет, перенаправляем на проверку доступа
        if not await check_access(user_id, update, context):
            await update.message.reply_text("Введите секретный код для доступа:", reply_markup=ReplyKeyboardRemove())
            return GETTING_ACCESS_CODE
        
        # Если доступ есть, продолжаем
        if text == "✨ Новый пост":
            await update.message.reply_text(
                "🚀 Отлично! Определитесь с *основной темой* для вашего контента:",
                parse_mode='Markdown',
                reply_markup=ReplyKeyboardMarkup(theme_keyboard, one_time_keyboard=True, resize_keyboard=True)
            )
            return CHOOSING_THEME
        
        elif text == "⚙️ Корректировать текст":
            await update.message.reply_text(
                "📝 Пришлите мне текст и **четкое указание**, что нужно изменить. Например: 'Улучши тон, сделай текст короче и добавь эмодзи'.",
                parse_mode='Markdown',
                reply_markup=ReplyKeyboardRemove()
            )
            return GETTING_CORRECTION
            
    elif text == "🔑 PRO-доступ":
        # Если нажата кнопка "PRO-доступ" - запускаем flow проверки/получения доступа
        return await handle_access_code_flow(update, context)
    
    # Заглушка, если нажато что-то не то
    await update.message.reply_text("Пожалуйста, выберите действие на клавиатуре.")
    return CHOOSING_ACTION


async def choose_theme(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Обрабатывает выбор темы и просит выбрать жанр."""
    text = update.message.text
    
    if text == "⬅️ Назад": return await start(update, context) 
    
    context.user_data['theme'] = text
    
    await update.message.reply_text(
        f"Тема: *{text}* выбрана. Теперь выберите подходящий *жанр/стиль*:",
        parse_mode='Markdown',
        reply_markup=ReplyKeyboardMarkup(genre_keyboard, one_time_keyboard=True, resize_keyboard=True)
    )
    return CHOOSING_GENRE

# ... (choose_genre остается почти без изменений)

async def generate_post(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Генерирует пост с помощью Gemini и выводит результат с новым дизайном."""
    
    # ... (Сбор данных) ...
    
    await update.message.reply_text("⏳ Идет генерация контента. Обычно это занимает 10-20 секунд. Пожалуйста, подождите...")

    result_text = await call_gemini_api(MASTER_PROMPT.format(
        user_topic=update.message.text, theme=context.user_data.get('theme', 'Общая категория'), 
        genre=context.user_data.get('genre', 'Информационный'), 
        audience="Фрилансеры", post_length="Средний", 
        additional_wishes="Стиль: экспертный, дружелюбный, с эмодзи."
    ))
    
    # 🔥 ОБРАБОТКА ОШИБКИ ИЛИ УСПЕХА
    if result_text.startswith("❌ ОШИБКА"):
        await update.message.reply_text(result_text)
    else:
        # Улучшенный дизайн вывода:
        await update.message.reply_text(
            "🌟 *ВАШ КОНТЕНТ ГОТОВ!* 🚀\n\n"
            "---"
            f"\n\n{result_text}\n\n"
            "---"
            "\n\n✅ *Проверьте текст, скопируйте и опубликуйте.*",
            parse_mode='Markdown'
        )

    return await start(update, context)

# ... (correct_post остается почти без изменений)

async def cancel(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Отменяет диалог."""
    await update.message.reply_text(
        '⏸️ Операция отменена. Возвращаемся в главное меню.',
        reply_markup=ReplyKeyboardMarkup(main_keyboard, one_time_keyboard=True, resize_keyboard=True)
    )
    context.user_data.clear()
    return CHOOSING_ACTION
