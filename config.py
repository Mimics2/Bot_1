# config.py

import logging

# --- ТОКЕНЫ И КЛЮЧИ ---
# 🔥 ВАЖНО: ЗАМЕНИТЕ ЭТОТ КЛЮЧ НА ВАШ РАБОЧИЙ!
TELEGRAM_BOT_TOKEN = '8428976532:AAElfrt3A7y3Q5Paq2-eVY9ACQXLNc9cSZE' # Пример
GEMINI_API_KEY = 'AIzaSyDl7tZKAXGX6kgDkHIzhVj3M6CV6UDN7qU' 

# --- НАСТРОЙКИ ДОСТУПА ПО КОДУ ---
SECRET_ACCESS_CODE = "PROCOPY2025" 
ACCESS_PRICE_DISPLAY = "1 USD"      

# --- НАСТРОЙКИ ЛОГИРОВАНИЯ ---
LOG_FORMAT = '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
logging.basicConfig(format=LOG_FORMAT, level=logging.INFO)
logger = logging.getLogger(__name__)

# --- СОСТОЯНИЯ ДИАЛОГА ---
(CHOOSING_ACTION, CHOOSING_THEME, CHOOSING_GENRE, GETTING_TOPIC, GETTING_CORRECTION, GETTING_ACCESS_CODE) = range(6)

# --- КЛАВИАТУРЫ (НОВЫЙ ДИЗАЙН) ---
main_keyboard = [["✨ Новый пост", "⚙️ Корректировка текста"], ["❌ Отмена"]]
theme_keyboard = [["Бизнес", "Технологии", "Путешествия"], ["Здоровье", "Личный бренд", "Другая тема"], ["⬅️ Назад"]]
genre_keyboard = [["Информационный (обучение)", "Продающий (AIDA)"], ["Развлекательный", "Сторителлинг", "Провокация"], ["⬅️ Назад"]]
