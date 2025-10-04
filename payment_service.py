# payment_service.py

import json
from datetime import datetime, timedelta

from telegram import Update, ReplyKeyboardRemove
from telegram.ext import ContextTypes
# ✅ ИСПРАВЛЕНИЕ: Удаляем импорт CHOOSING_ACTION внутри функции, чтобы избежать циклического импорта
from config import logger, SECRET_ACCESS_CODE, ACCESS_PRICE_DISPLAY, CHOOSING_ACTION 

# --- КОНФИГУРАЦИЯ ХРАНИЛИЩА ---
USERS_DATA_FILE = 'users_data.json'
TRIAL_DURATION_DAYS = 365 
TRIAL_GENERATION_LIMIT = -1 # -1 означает безлимит

# --- ФУНКЦИИ РАБОТЫ С ДАННЫМИ (JSON) ---

def load_users_data() -> dict:
    """Загружает данные о пользователях из JSON-файла."""
    try:
        with open(USERS_DATA_FILE, 'r', encoding='utf-8') as f:
            return json.load(f)
    except (FileNotFoundError, json.JSONDecodeError):
        with open(USERS_DATA_FILE, 'w', encoding='utf-8') as f:
            json.dump({}, f)
        return {}

def save_users_data(data: dict):
    """Сохраняет данные о пользователях в JSON-файл."""
    try:
        with open(USERS_DATA_FILE, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=4, ensure_ascii=False)
    except Exception as e:
        logger.error(f"Ошибка при сохранении данных в {USERS_DATA_FILE}: {e}")

USERS_DATA = load_users_data() # 🔥 Глобальная переменная для хранения данных

def activate_pro_access(user_id: int):
    """Добавляет пользователя в базу с PRO-тарифом."""
    user_id_str = str(user_id)
    
    start_date = datetime.now()
    expiration_date = start_date + timedelta(days=TRIAL_DURATION_DAYS)

    USERS_DATA[user_id_str] = {
        'telegram_id': user_id,
        'tariff_name': 'PRO-TRIAL', 
        'tariff_duration': TRIAL_DURATION_DAYS,
        'generations_left': TRIAL_GENERATION_LIMIT,
        'start_date': start_date.strftime("%Y-%m-%d"),
        'expiration_date': expiration_date.strftime("%Y-%m-%d"),
    }
    save_users_data(USERS_DATA)
    logger.info(f"Активирован PRO-доступ для пользователя {user_id} до {expiration_date.strftime('%Y-%m-%d')}.")


async def check_access(user_id: int, update: Update, context: ContextTypes.DEFAULT_TYPE) -> bool:
    """Проверяет, есть ли у пользователя активный доступ."""
    
    user_id_str = str(user_id)
    
    if user_id_str in USERS_DATA:
        user_info = USERS_DATA[user_id_str]
        
        # Проверка срока действия
        expiration_date_str = user_info.get('expiration_date')
        if expiration_date_str:
            expiration_date = datetime.strptime(expiration_date_str, "%Y-%m-%d")
            if expiration_date < datetime.now():
                # Срок истек
                del USERS_DATA[user_id_str]
                save_users_data(USERS_DATA)
                
        # Проверка лимитов (если запись еще существует)
        if user_id_str in USERS_DATA:
            generations_left = USERS_DATA[user_id_str].get('generations_left', 0)
            
            if generations_left == -1 or generations_left > 0:
                # Если безлимит (-1) или есть генерации
                return True 
        
    # Если доступа нет, просим ввести код
    await update.message.reply_text(
        "🔒 **Доступ ограничен.**\n"
        f"Для использования PRO-функций CopiBot (Gemini) требуется активация.\n"
        f"Чтобы получить доступ, введите **секретный код** или обратитесь к администратору (Цена: {ACCESS_PRICE_DISPLAY}).",
        parse_mode='Markdown'
    )
    return False


async def handle_access_code(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Проверяет введенный пользователем код доступа и активирует тариф."""
    
    user_input = update.message.text.strip().upper() 
    user_id = update.effective_user.id
    
    if user_input == SECRET_ACCESS_CODE.upper():
        # Код верен: даем доступ и возвращаемся в главное меню
        activate_pro_access(user_id)
        await update.message.reply_text(
            "🥳 **ПОЗДРАВЛЯЮ! Доступ активирован.**\n"
            f"У вас **БЕЗЛИМИТНЫЙ** доступ на **{TRIAL_DURATION_DAYS}** дней.\n"
            "Нажмите /start, чтобы начать работу.",
            parse_mode='Markdown',
            reply_markup=ReplyKeyboardRemove()
        )
        return CHOOSING_ACTION
        
    else:
        # Код неверен
        await update.message.reply_text(
            "❌ **Неверный код.** Пожалуйста, проверьте код и введите его еще раз. "
            "Или нажмите /start, чтобы отменить."
        )
        return GETTING_ACCESS_CODE
