# payment_service.py

import json
from datetime import datetime, timedelta
from telegram import Update
from telegram.ext import ContextTypes
# 🔥 ИСПРАВЛЕНО: Только необходимые импорты
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

def activate_pro_access(user_id: int):
    """Добавляет пользователя в базу с PRO-тарифом."""
    user_id_str = str(user_id)
    start_date = datetime.now()
    expiration_date = start_date + timedelta(days=TRIAL_DURATION_DAYS)

    USERS_DATA[user_id_str] = {
        'telegram_id': user_id,
        'tariff_name': 'PRO-TRIAL', 
        'expiration_date': expiration_date.strftime("%Y-%m-%d"),
        'generations_left': -1 # Безлимит
    }
    save_users_data(USERS_DATA)

async def check_access(user_id: int, update: Update, context: ContextTypes.DEFAULT_TYPE) -> bool:
    """Проверяет, есть ли у пользователя активный доступ."""
    user_id_str = str(user_id)
    
    if user_id_str in USERS_DATA:
        user_info = USERS_DATA[user_id_str]
        
        expiration_date_str = user_info.get('expiration_date')
        if expiration_date_str:
            expiration_date = datetime.strptime(expiration_date_str, "%Y-%m-%d")
            if expiration_date >= datetime.now(): 
                return True
            else:
                # Срок истек
                del USERS_DATA[user_id_str]
                save_users_data(USERS_DATA)
        else: 
            return True # Если нет даты, считаем активным (бессрочный)
        
    # Если доступа нет, выводим сообщение с новым дизайном
    await update.message.reply_text(
        "🔒 **ДОСТУП ОГРАНИЧЕН.**\n"
        f"Для использования PRO-функций (Gemini) требуется активация.\n"
        f"Чтобы получить доступ, введите **секретный код** (Цена: {ACCESS_PRICE_DISPLAY}).",
        parse_mode='Markdown'
    )
    return False

# 🔥 УДАЛЕНО: handle_access_code - перенесена в handlers.py для корректной работы ConversationHandler.
