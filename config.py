# config.py

import logging

# --- ТОКЕНЫ И КЛЮЧИ ---
TELEGRAM_BOT_TOKEN = '8428976532:AAElfrt3A7y3Q5Paq2-eVY9ACxQXKc9cSZE'
GEMINI_API_KEY = 'AIzaSyBXaEujyx80xYCaZ6ByraBad4hqyJQr6WQ' 

# --- НАСТРОЙКИ ДОСТУПА ПО КОДУ ---
SECRET_ACCESS_CODE = "PROCOPY2025" # 🔥 ВАШ СЕКРЕТНЫЙ КОД
ACCESS_PRICE_DISPLAY = "1 USD"      # Для сообщения пользователю

# --- НАСТРОЙКИ ЛОГИРОВАНИЯ ---
LOG_FORMAT = '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
logging.basicConfig(format=LOG_FORMAT, level=logging.INFO)
logger = logging.getLogger(__name__)

# --- СОСТОЯНИЯ ДИАЛОГА (Добавлено GETTING_ACCESS_CODE) ---
(CHOOSING_THEME, CHOOSING_GENRE, GETTING_TOPIC, GETTING_CORRECTION, CHOOSING_ACTION, GETTING_ACCESS_CODE) = range(6)
