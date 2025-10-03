# handlers.py

from telegram import Update, ReplyKeyboardMarkup, ReplyKeyboardRemove
from telegram.ext import ContextTypes, ConversationHandler
from config import * # Импортируем все константы
from ai_service import MASTER_PROMPT, call_gemini_api
from payment_service import check_access

# --- КЛАВИАТУРЫ ---
main_keyboard = [["🆕 Начать новый пост", "⚙️ Корректировать предыдущий"], ["❌ Отмена"]]
theme_keyboard = [["Бизнес", "Технологии", "Путешествия", "Здоровье"], ["Личный бренд", "Другая тема", "⬅️ Назад"]]
genre_keyboard = [["Информационный (обучение)", "Продающий (AIDA)", "Развлекательный (лайфхак)"], ["Сторителлинг (личная история)", "Провокация (хайп)", "⬅️ Назад"]]


# --- ОБРАБОТЧИКИ ДИАЛОГА ---

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Начинает диалог."""
    await update.message.reply_text(
        "👋 Добро пожаловать в CopiBot на базе Gemini! Выберите, что будем делать:",
        reply_markup=ReplyKeyboardMarkup(main_keyboard, one_time_keyboard=True, resize_keyboard=True)
    )
    return CHOOSING_ACTION

async def choose_action(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Обрабатывает выбор 'Начать новый пост' или 'Корректировать'."""
    text = update.message.text
    
    if text == "🆕 Начать новый пост":
        # Проверяем доступ перед началом работы
        if not await check_access(update.effective_user.id, update, context):
            return CHOOSING_ACTION # Остаемся в этом состоянии, пока не оплатит
            
        await update.message.reply_text(
            "Отлично! Теперь выберите основную тему вашего поста:",
            reply_markup=ReplyKeyboardMarkup(theme_keyboard, one_time_keyboard=True, resize_keyboard=True)
        )
        return CHOOSING_THEME
    
    elif text == "⚙️ Корректировать предыдущий":
        if not await check_access(update.effective_user.id, update, context):
            return CHOOSING_ACTION
            
        await update.message.reply_text(
            "Пожалуйста, отправьте мне текст, который нужно скорректировать, "
            "и **подробно укажите**, что именно нужно изменить (стиль, тон, грамматика).",
            reply_markup=ReplyKeyboardRemove()
        )
        return GETTING_CORRECTION
    
    await update.message.reply_text("Пожалуйста, выберите действие на клавиатуре.")
    return CHOOSING_ACTION

async def choose_theme(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Обрабатывает выбор темы и просит выбрать жанр."""
    text = update.message.text
    
    if text == "⬅️ Назад": return await start(update, context)
    
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
        await update.message.reply_text("Выберите основную тему вашего поста:", reply_markup=ReplyKeyboardMarkup(theme_keyboard, one_time_keyboard=True, resize_keyboard=True))
        return CHOOSING_THEME 
        
    context.user_data['genre'] = text
    
    await update.message.reply_text(
        f"Вы выбрали жанр: *{text}*.\nТеперь, пожалуйста, введите **конкретную подтему**, основную идею или черновик для поста.",
        parse_mode='Markdown',
        reply_markup=ReplyKeyboardRemove()
    )
    return GETTING_TOPIC

async def generate_post(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Генерирует пост с помощью Gemini и выводит результат."""
    
    # 1. Сбор данных
    user_topic = update.message.text
    theme = context.user_data.get('theme', 'Общая категория')
    genre = context.user_data.get('genre', 'Информационный')
    
    # Фиксированные данные для промпта (можно сделать ввод через кнопки)
    audience = "Фрилансеры, работающие из дома, которые ищут мотивацию и продуктивность."
    post_length = "Средний (2-3 абзаца, с маркированными списками)."
    additional_wishes = "Добавить провокационный заголовок, использовать дружелюбный, но экспертный тон и не писать 'и вот почему'."

    # 2. Формирование финального промпта
    prompt = MASTER_PROMPT.format(
        user_topic=user_topic,
        theme=theme,
        genre=genre,
        audience=audience,
        post_length=post_length,
        additional_wishes=additional_wishes
    )
    
    await update.message.reply_text("✍️ Ваш пост генерируется. Пожалуйста, подождите...")

    # 3. Вызов AI
    result_text = await call_gemini_api(prompt)
    
    # 4. Отправка результата
    await update.message.reply_text(
        f"✅ **ГОТОВЫЙ ПОСТ ({theme} / {genre})**:\n\n{result_text}",
        parse_mode='Markdown'
    )

    return await start(update, context)

async def correct_post(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Корректирует текст с помощью Gemini."""
    correction_prompt = update.message.text
    
    prompt = (
        f"Ты профессиональный редактор и корректор. Твоя задача — выполнить корректировку текста, "
        f"основываясь на запросе пользователя. Запрос и текст для коррекции: '{correction_prompt}'. "
        f"Верни только исправленный и улучшенный текст. Не добавляй никаких пояснений, только результат."
    )
    
    await update.message.reply_text("🔄 Выполняю коррекцию текста...")

    result_text = await call_gemini_api(prompt)

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
