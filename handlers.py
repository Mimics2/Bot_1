# handlers.py

from telegram import Update, ReplyKeyboardMarkup, ReplyKeyboardRemove
from telegram.ext import ContextTypes, ConversationHandler
# ✅ ИСПРАВЛЕНО: Два отдельных оператора импорта:
from config import *
from ai_service import MASTER_PROMPT, call_gemini_api
# ✅ ИСПРАВЛЕНО: Добавлен импорт USERS_DATA и save_users_data для списания лимитов
from payment_service import check_access, handle_access_code, USERS_DATA, save_users_data


# --- ОБРАБОТЧИКИ ДИАЛОГА ---

# ... (остальные функции start, choose_action, choose_theme, choose_genre)

async def generate_post(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Генерирует пост с помощью Gemini и выводит результат."""
    
    user_topic = update.message.text
    theme = context.user_data.get('theme', 'Общая категория')
    genre = context.user_data.get('genre', 'Информационный')
    user_id_str = str(update.effective_user.id) # Получаем ID пользователя
    
    # ... (Остальной код про audience, post_length, prompt)

    prompt = MASTER_PROMPT.format(
        user_topic=user_topic,
        theme=theme,
        genre=genre,
        audience=audience,
        post_length=post_length,
        additional_wishes=additional_wishes
    )
    
    # ❌ ИСПРАВЛЕНО: Добавлен индикатор работы
    await update.message.reply_text("✍️ Ваш пост генерируется. Пожалуйста, подождите...")

    result_text = await call_gemini_api(prompt)
    
    # --- ЛОГИКА СПИСАНИЯ ГЕНЕРАЦИИ ---
    # Списываем одну генерацию, только если это не безлимит (-1)
    if user_id_str in USERS_DATA and USERS_DATA[user_id_str]['generations_left'] > 0:
        USERS_DATA[user_id_str]['generations_left'] -= 1
        save_users_data(USERS_DATA) # Сохраняем изменения в файл
        
    # --- КОНЕЦ ЛОГИКИ СПИСАНИЯ ГЕНЕРАЦИИ ---
        
    await update.message.reply_text(
        f"✅ **ГОТОВЫЙ ПОСТ ({theme} / {genre})**:\n\n{result_text}",
        parse_mode='Markdown'
    )

    return await start(update, context)

async def correct_post(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Корректирует текст с помощью Gemini."""
    correction_prompt = update.message.text
    user_id_str = str(update.effective_user.id) # Получаем ID пользователя
    
    prompt = (
        f"Ты профессиональный редактор и корректор. Твоя задача — выполнить корректировку текста, "
        f"основываясь на запросе пользователя. Запрос и текст для коррекции: '{correction_prompt}'. "
        f"Верни только исправленный и улучшенный текст. Не добавляй никаких пояснений, только результат."
    )
    
    # ❌ ИСПРАВЛЕНО: Добавлен индикатор работы
    await update.message.reply_text("🔄 Выполняю коррекцию текста...")

    result_text = await call_gemini_api(prompt)

    # --- ЛОГИКА СПИСАНИЯ ГЕНЕРАЦИИ ---
    # Списываем одну генерацию, только если это не безлимит (-1)
    if user_id_str in USERS_DATA and USERS_DATA[user_id_str]['generations_left'] > 0:
        USERS_DATA[user_id_str]['generations_left'] -= 1
        save_users_data(USERS_DATA) # Сохраняем изменения в файл
        
    # --- КОНЕЦ ЛОГИКИ СПИСАНИЯ ГЕНЕРАЦИИ ---
    
    await update.message.reply_text(
        f"✅ **СКОРРЕКТИРОВАННЫЙ ТЕКСТ**:\n\n{result_text}",
        parse_mode='Markdown'
    )

    return await start(update, context)

# ... (функция cancel)
    
