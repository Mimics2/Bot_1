# handlers.py

from telegram import Update, ReplyKeyboardMarkup, ReplyKeyboardRemove
from telegram.ext import ContextTypes, ConversationHandler
# ✅ Явный импорт всех необходимых констант (УДАЛЕНО: from config import *)
from config import (
    logger, CHOOSING_ACTION, CHOOSING_THEME, CHOOSING_GENRE, 
    GETTING_TOPIC, GETTING_CORRECTION, GETTING_ACCESS_CODE,
    main_keyboard, theme_keyboard, genre_keyboard
)
from ai_service import MASTER_PROMPT, call_gemini_api
# ✅ Импортируем функции и хранилище из payment_service
from payment_service import check_access, USERS_DATA, save_users_data


# --- ОБРАБОТЧИКИ ДИАЛОГА ---

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Начинает диалог."""
    logger.info(f"Получена команда /start от пользователя: {update.effective_user.id}")
    
    await update.message.reply_text(
        "👋 Добро пожаловать в CopiBot на базе Gemini! Выберите, что будем делать:",
        reply_markup=ReplyKeyboardMarkup(main_keyboard, one_time_keyboard=True, resize_keyboard=True)
    )
    return CHOOSING_ACTION

async def choose_action(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Обрабатывает выбор 'Начать новый пост' или 'Корректировать'."""
    text = update.message.text
    user_id = update.effective_user.id
    
    if text in ["🆕 Начать новый пост", "⚙️ Корректировать предыдущий"]:
        
        # 1. Проверка доступа
        if not await check_access(user_id, update, context):
            await update.message.reply_text("Введите секретный код:", reply_markup=ReplyKeyboardRemove())
            return GETTING_ACCESS_CODE
            
        # 2. Если доступ есть, продолжаем
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
    
    return CHOOSING_ACTION

async def generate_post(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Генерирует пост с помощью Gemini и выводит результат."""
    user_topic = update.message.text
    theme = context.user_data.get('theme', 'Общая категория')
    genre = context.user_data.get('genre', 'Информационный')
    user_id_str = str(update.effective_user.id) 
    
    audience = "Фрилансеры"
    post_length = "Средний"
    additional_wishes = "Используй стиль, который мы обсуждали (много эмодзи, минимум запятых, от первого лица)."
    
    prompt = MASTER_PROMPT.format(user_topic=user_topic, theme=theme, genre=genre, audience=audience, post_length=post_length, additional_wishes=additional_wishes)
    
    await update.message.reply_text("✍️ Ваш пост генерируется. Пожалуйста, подождите...")

    result_text = await call_gemini_api(prompt)
    
    if result_text.startswith("❌ ОШИБКА"):
        await update.message.reply_text(result_text)
    else:
        # Логика списания лимитов
        if user_id_str in USERS_DATA and USERS_DATA[user_id_str].get('generations_left', 0) > 0:
            USERS_DATA[user_id_str]['generations_left'] -= 1
            save_users_data(USERS_DATA) 
            
        await update.message.reply_text(
            f"✅ **ГОТОВЫЙ ПОСТ ({theme} / {genre})**:\n\n{result_text}",
            parse_mode='Markdown'
        )

    return await start(update, context)


async def correct_post(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Корректирует текст с помощью Gemini."""
    correction_prompt = update.message.text
    user_id_str = str(update.effective_user.id)
    
    prompt = (
        f"Ты профессиональный редактор и корректор. Запрос: '{correction_prompt}'. "
        f"Верни только исправленный и улучшенный текст. Не добавляй пояснений."
    )
    
    await update.message.reply_text("🔄 Выполняю коррекцию текста...")

    result_text = await call_gemini_api(prompt)

    if result_text.startswith("❌ ОШИБКА"):
        await update.message.reply_text(result_text)
    else:
        # Логика списания лимитов
        if user_id_str in USERS_DATA and USERS_DATA[user_id_str].get('generations_left', 0) > 0:
            USERS_DATA[user_id_str]['generations_left'] -= 1
            save_users_data(USERS_DATA) 

        await update.message.reply_text(
            f"✅ **СКОРРЕКТИРОВАННЫЙ ТЕКСТ**:\n\n{result_text}",
            parse_mode='Markdown'
        )

    return await start(update, context)

async def cancel(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Отменяет диалог."""
    await update.message.reply_text(
        'Операция отменена. Чем я могу еще помочь?',
        reply_markup=ReplyKeyboardMarkup(main_keyboard, one_time_keyboard=True, resize_keyboard=True)
    )
    context.user_data.clear()
    return CHOOSING_ACTION
