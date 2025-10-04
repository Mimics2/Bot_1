# config.py

import logging

# --- ТОКЕНЫ И КЛЮЧИ ---
TELEGRAM_BOT_TOKEN = '8428976532:AAElfrt3A7y3Q5Paq2-eVY9ACxQXKc9cSZE'
GEMINI_API_KEY = 'AIzaSyBiZegB15BVFGIKW8L6-uhWFRYxb5PooyI' 
# 🔥 ДОБАВЛЕН СПИСОК КЛЮЧЕЙ для ротации в ai_service.py
GEMINI_API_KEYS = [
    'AIzaSyBiZegB15BVFGIKW8L6-uhWFRYxb5PooyI', # Ваш первый ключ (текущий)
    'AIzaSyDl7tZKAXGX6kgDkHIzhVj3M6CV6UDN7qU', 
    'AIzaSyBPRdMzd2aEixi29aNPKPJxDuNho-_j8ys',  
]

# --- НАСТРОЙКИ ДОСТУПА ПО КОДУ ---
SECRET_ACCESS_CODE = "PROCOPY2025" 
ACCESS_PRICE_DISPLAY = "1 USD"

# --- НАСТРОЙКИ ЛОГИРОВАНИЯ ---
LOG_FORMAT = '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
logging.basicConfig(format=LOG_FORMAT, level=logging.INFO)
logger = logging.getLogger(__name__)

# --- СОСТОЯНИЯ ДИАЛОГА ---
(CHOOSING_THEME, CHOOSING_GENRE, GETTING_TOPIC, GETTING_CORRECTION, CHOOSING_ACTION, GETTING_ACCESS_CODE) = range(6)

# --- КЛАВИАТУРЫ ---
main_keyboard = [["🆕 Начать новый пост", "⚙️ Корректировать предыдущий"], ["❌ Отмена"]]
theme_keyboard = [["Бизнес", "Технологии", "Путешествия", "Здоровье"], ["Личный бренд", "Другая тема", "⬅️ Назад"]]
genre_keyboard = [["Информационный (обучение)", "Продающий (AIDA)", "Развлекательный (лайфхак)"], ["Сторителлинг (личная история)", "Провокация (хайп)", "⬅️ Назад"]]
