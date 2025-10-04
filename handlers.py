# handlers.py

from telegram import Update, ReplyKeyboardMarkup, ReplyKeyboardRemove
from telegram.ext import ContextTypes, ConversationHandler
# 🔥 ИСПРАВЛЕНИЕ: Явный импорт констант и клавиатур
from config import (
    logger, CHOOSING_ACTION, CHOOSING_THEME, CHOOSING_GENRE, 
    GETTING_TOPIC, GETTING_CORRECTION, GETTING_ACCESS_CODE,
    main_keyboard, theme_keyboard, genre_keyboard
)
from ai_service import MASTER_PROMPT, call_gemini_api
from payment_service import check_access, activate_pro_access # handle_access_code импортируется в main.py


# --- ОБРАБОТЧИКИ ДИАЛОГА ---

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Начинает диалог с новым дизайном приветствия."""
    user_name = update.effective_user.first_name if update.effective_user.first_name else "Гость"
    
    await update.message.reply_text(
        f"👋 Привет, *{user_name}*! Я CopiBot 🤖, ваш PRO-ассистент на базе *Gemini*.\n\n"
        "Выберите действие, чтобы начать создавать *высококонверсионный контент*:",
        parse_mode='Markdown',
        reply_markup=ReplyKeyboardMarkup(main_keyboard, one_time_keyboard=True, resize_keyboard=True)
    )
    context.user_data.clear() 
    return CHOOSING_ACTION

async def choose_action(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Обрабатывает выбор действия и проверяет PRO-доступ."""
    text = update.message.text
    user_id = update.effective_user.id
    
    if text == "❌ Отмена": return await cancel(update, context) 
    
    # --- Проверка доступа для всех PRO-функций ---
    if text in ["✨ Новый пост", "⚙️ Корректировка текста"]:
        
        # Если доступа нет, переходим в состояние ожидания кода
        if not await check_access(user_id, update, context):
            return GETTING_ACCESS_CODE
        
        # Если доступ есть
        if text == "✨ Новый пост":
            await update.message.reply_text(
                "✨ Отлично! Определитесь с *основной темой* для вашего контента:",
                parse_mode='Markdown',
                reply_markup=ReplyKeyboardMarkup(theme_keyboard, one_time_keyboard=True, resize_keyboard=True)
            )
            return CHOOSING_THEME
        
        elif text == "⚙️ Корректировка текста":
            await update.message.reply_text(
                "📝 Пришлите текст и **четкое указание**, что именно нужно изменить (например, 'Улучши тон, сделай текст короче и добавь эмодзи').",
                parse_mode='Markdown',
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
        f"✅ Тема *{text}* выбрана. Теперь выберите подходящий *жанр/стиль* написания:",
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
        f"🔥 Выбран жанр: *{text}*. \nВведите **конкретную подтему**, основную идею или черновик для поста. Чем подробнее, тем лучше результат.",
        parse_mode='Markdown',
        reply_markup=ReplyKeyboardRemove()
    )
    return GETTING_TOPIC

async def generate_post(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Генерирует пост с помощью Gemini и выводит результат."""
    
    await update.message.reply_text("⏳ *Генерирую контент...* Это займет несколько секунд.", parse_mode='Markdown')

    result_text = await call_gemini_api(MASTER_PROMPT.format(
        user_topic=update.message.text, theme=context.user_data.get('theme', 'Общая категория'), 
        genre=context.user_data.get('genre', 'Информационный'), 
        audience="Фрилансеры", post_length="Средний", 
        additional_wishes="Стиль: экспертный, дружелюбный, с эмодзи."
    ))
    
    if result_text.startswith("❌ ОШИБКА"): 
        await update.message.reply_text(result_text)
    else:
        # Улучшенный дизайн вывода
        await update.message.reply_text(
            "🌟 *ВАШ PRO-ПОСТ ГОТОВ!* 🚀\n\n"
            f"*Тема:* {context.user_data.get('theme')}\n*Жанр:* {context.user_data.get('genre')}\n\n"
            "---"
            f"\n\n{result_text}\n\n"
            "---"
            "\n\n✅ *Проверьте текст, скопируйте и опубликуйте.*",
            parse_mode='Markdown'
        )

    return await start(update, context)

async def correct_post(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Корректирует текст с помощью Gemini."""
    
    await update.message.reply_text("🔄 *Выполняю коррекцию текста...*", parse_mode='Markdown')

    correction_prompt = update.message.text
    prompt = ("Твоя задача — выполнить корректировку текста, основываясь на запросе пользователя. "
              f"Запрос и текст для коррекции: '{correction_prompt}'. "
              "Верни только исправленный и улучшенный текст. Не добавляй никаких пояснений, только результат.")
    
    result_text = await call_gemini_api(prompt)

    if result_text.startswith("❌ ОШИБКА"):
        await update.message.reply_text(result_text)
    else:
        await update.message.reply_text(
            "📝 *СКОРРЕКТИРОВАННЫЙ ТЕКСТ*:\n\n"
            "---"
            f"\n\n{result_text}\n\n"
            "---"
            "\n\n✅ *Готово к использованию.*",
            parse_mode='Markdown'
        )

    return await start(update, context)

async def cancel(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Отменяет диалог."""
    await update.message.reply_text(
        '⏸️ Операция отменена. Возвращаемся в главное меню.',
        reply_markup=ReplyKeyboardMarkup(main_keyboard, one_time_keyboard=True, resize_keyboard=True)
    )
    context.user_data.clear()
    return CHOOSING_ACTION
