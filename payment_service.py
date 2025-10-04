# payment_service.py

import json
from datetime import datetime, timedelta
from telegram import Update, ReplyKeyboardRemove
from telegram.ext import ContextTypes
# ✅ Импортируем все необходимое явно, кроме CHOOSING_ACTION (избегаем циклического импорта)
from config import logger, SECRET_ACCESS_CODE, ACCESS_PRICE_DISPLAY 

# --- КОНФИГУРАЦИЯ ХРАНИЛИЩА ---
USERS_DATA_FILE = 'users_data.json'
TRIAL_DURATION_DAYS = 365 

# --- ФУНКЦИИ РАБОТЫ С ДАННЫМИ (JSON) ---

def load_users_data() -> dict:
    """Загружает данные о пользователях из JSON-файла."""
    try:
        with open(USERS_DATA_FILE, 'r', encoding='utf-8') as f:
            return json.load(f)
    except (FileNotFoundError, json.JSONDecodeError):
        return {}

def save_users_data(data: dict):
    """Сохраняет данные о пользователях в JSON-файл."""
    try:
        with open(USERS_DATA_FILE, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=4, ensure_ascii=False)
    except Exception as e:
        logger.error(f"Ошибка при сохранении данных в {USERS_DATA_FILE}: {e}")

# 🔥 Глобальная переменная для хранения данных (будет сохранять состояние)
USERS_DATA = load_users_data() 

# ... (activate_pro_access, check_access остаются, как в стабильной версии)

async def handle_access_code_flow(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Обрабатывает нажатие кнопки "PRO-доступ"."""
    from config import CHOOSING_ACTION # Импортируем здесь, чтобы избежать конфликтов
    
    user_id_str = str(update.effective_user.id)
    
    if user_id_str in USERS_DATA and USERS_DATA[user_id_str].get('expiration_date'):
        # Если доступ уже активен
        await update.message.reply_text("✅ У вас уже активен PRO-доступ до *{expiration_date}*.".format(**USERS_DATA[user_id_str]), parse_mode='Markdown')
        return CHOOSING_ACTION
    
    # Если доступа нет или он истек
    await update.message.reply_text(
        f"🔑 Введите **секретный код** для активации PRO-доступа (Цена: {ACCESS_PRICE_DISPLAY}).\n"
        "Или нажмите /start для отмены.",
        parse_mode='Markdown',
        reply_markup=ReplyKeyboardRemove()
    )
    return GETTING_ACCESS_CODE # Переходим в состояние ожидания кода


async def handle_access_code(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Проверяет введенный пользователем код доступа (ВЫЗЫВАЕТСЯ ИЗ main.py)."""
    from config import CHOOSING_ACTION # Импортируем здесь
    
    user_input = update.message.text.strip().upper() 
    user_id = update.effective_user.id
        
    if user_input == SECRET_ACCESS_CODE.upper():
        # Код верен
        activate_pro_access(user_id)
        await update.message.reply_text(
            "🥳 **ПОЗДРАВЛЯЮ! Доступ активирован.**\n"
            "Нажмите /start, чтобы начать работу.",
            parse_mode='Markdown',
            reply_markup=ReplyKeyboardRemove()
        )
        return CHOOSING_ACTION
        
    else:
        # Код неверен
        await update.message.reply_text(
            "❌ **Неверный код.** Пожалуйста, проверьте код и введите его еще раз."
        )
        return GETTING_ACCESS_CODE
