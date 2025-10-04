# handlers.py

from telegram import Update, ReplyKeyboardMarkup, ReplyKeyboardRemove
from telegram.ext import ContextTypes, ConversationHandler
from config import (
    logger, CHOOSING_ACTION, CHOOSING_THEME, CHOOSING_GENRE, 
    GETTING_TOPIC, GETTING_CORRECTION, GETTING_ACCESS_CODE,
    main_keyboard, theme_keyboard, genre_keyboard
)
from ai_service import MASTER_PROMPT, call_gemini_api
from payment_service import check_access, handle_access_code, USERS_DATA, save_users_data 


# --- ОБРАБОТЧИКИ ДИАЛОГА ---

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Начинает диалог."""
    logger.info(f"Получена команда /start от пользователя: {update.effective_user.id}")
    
    await update.message.reply_text(
        "👋 Добро пожаловать в CopiBot на базе Gemini! Выберите, что будем делать:",
        # 🔥 Убедимся, что главное меню всегда отправляется
        reply_markup=ReplyKeyboardMarkup(main_keyboard, one_time_keyboard=True, resize_keyboard=True)
    )
    return CHOOSING_ACTION

async def choose_action(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Обрабатывает выбор 'Начать новый пост' или 'Корректировать'."""
    text = update.message.text
    user_id = update.effective_user.id
    
    # ... Логика проверки доступа ...
    if not await check_access(user_id, update, context):
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
            parse_mode='Markdown',
            reply_markup=ReplyKeyboardRemove()
        )
        return GETTING_CORRECTION
    
    return CHOOSING_ACTION

async def choose_theme(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Обрабатывает выбор темы и просит выбрать жанр."""
    text = update.message.text
    
    if text == "⬅️ Назад": 
        # 🔥 ИСПРАВЛЕНО: Явный возврат в главное меню
        await update.message.reply_text(
            "Возвращаемся в главное меню. Выберите, что будем делать:",
            reply_markup=ReplyKeyboardMarkup(main_keyboard, one_time_keyboard=True, resize_keyboard=True)
        )
        return CHOOSING_ACTION # <--- Ключевое изменение: возвращаем правильный STATE
    
    context.user_data['theme'] = text
    
    await update.message.reply_text(
        f"Вы выбрали тему: *{text}*.\nТеперь выберите жанр или стиль написания:",
        parse_mode='Markdown',
        reply_markup=ReplyKeyboardMarkup(genre_keyboard, one_time_keyboard=True, resize_keyboard=True)
    )
    return CHOOSING_GENRE

async def choose_genre(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Обрабатывает выбор жанра и просит ввести конкретную подтему."""
    text = update.message.text
    
    if text == "⬅️ Назад":
        # 🔥 ИСПРАВЛЕНО: Явный возврат в меню тем
        await update.message.reply_text(
            "Возвращаемся к выбору темы. Выберите основную тему вашего поста:", 
            reply_markup=ReplyKeyboardMarkup(theme_keyboard, one_time_keyboard=True, resize_keyboard=True)
        )
        return CHOOSING_THEME # <--- Ключевое изменение: возвращаем правильный STATE
        
    context.user_data['genre'] = text
    
    await update.message.reply_text(
        f"Вы выбрали жанр: *{text}*.\nТеперь, пожалуйста, введите **конкретную подтему**, основную идею или черновик для поста.",
        parse_mode='Markdown',
        reply_markup=ReplyKeyboardRemove()
    )
    return GETTING_TOPIC

async def generate_post(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    # ... (логика генерации поста) ...
    
    await update.message.reply_text("✍️ Ваш пост генерируется. Пожалуйста, подождите...")

    result_text = await call_gemini_api(prompt)
    
    # ... (логика списания генерации) ...
        
    await update.message.reply_text(
        f"✅ **ГОТОВЫЙ ПОСТ ({theme} / {genre})**:\n\n{result_text}",
        parse_mode='Markdown'
    )

    # 🔥 ИСПРАВЛЕНИЕ: Гарантируем возврат в CHOOSING_ACTION
    return await start(update, context)

async def correct_post(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    # ... (логика коррекции поста) ...
    
    await update.message.reply_text("🔄 Выполняю коррекцию текста...")

    result_text = await call_gemini_api(prompt)

    # ... (логика списания генерации) ...
    
    await update.message.reply_text(
        f"✅ **СКОРРЕКТИРОВАННЫЙ ТЕКСТ**:\n\n{result_text}",
        parse_mode='Markdown'
    )

    # 🔥 ИСПРАВЛЕНИЕ: Гарантируем возврат в CHOOSING_ACTION
    return await start(update, context)

async def cancel(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Отменяет диалог."""
    await update.message.reply_text(
        'Операция отменена. Чем я могу еще помочь?',
        reply_markup=ReplyKeyboardMarkup(main_keyboard, one_time_keyboard=True, resize_keyboard=True)
    )
    context.user_data.clear()
    return CHOOSING_ACTION
