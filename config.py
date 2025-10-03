# config.py

import logging

# --- ТОКЕНЫ И КЛЮЧИ ---
# Ваш токен Telegram от BotFather
TELEGRAM_BOT_TOKEN = '8428976532:AAElfrt3A7y3Q5Paq2-eVY9ACxQXKc9cSZE'
# Ваш ключ Gemini API
GEMINI_API_KEY = 'AIzaSyBXaEujyx80xYCaZ6ByraBad4hqyJQr6WQ' 

# --- НАСТРОЙКИ WELLPAY (ЗАГЛУШКИ) ---
# Для реальной интеграции WellPay здесь будут боевые ключи
WELLPAY_SHOP_ID = 'YOUR_WELLPAY_SHOP_ID' 
WELLPAY_API_KEY = 'YOUR_WELLPAY_API_KEY' 
SUBSCRIPTION_PRICE = 999  # Цена подписки в рублях

# --- НАСТРОЙКИ ЛОГИРОВАНИЯ ---
LOG_FORMAT = '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
logging.basicConfig(format=LOG_FORMAT, level=logging.INFO)
logger = logging.getLogger(__name__)

# --- СОСТОЯНИЯ ДИАЛОГА ---
(CHOOSING_THEME, CHOOSING_GENRE, GETTING_TOPIC, GETTING_CORRECTION, CHOOSING_ACTION) = range(5)
