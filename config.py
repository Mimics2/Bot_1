# config.py

import logging

# --- ТОКЕНЫ И КЛЮЧИ ---
TELEGRAM_BOT_TOKEN = '8428976532:AAElfrt3A7y3Q5Paq2-eVY9ACxQXKc9cSZE'
# 🔥 Ротация ключей
GEMINI_API_KEYS = [
    'AIzaSyBiZegB15BVFGIKW8L6-uhWFRYxb5PooyI', # Ваш первый ключ (текущий)
    'ВСТАВЬТЕ_СЮДА_ВТОРОЙ_КЛЮЧ', # Добавьте второй ключ
    'ВСТАВЬТЕ_СЮДА_ТРЕТИЙ_КЛЮЧ',  # Добавьте третий ключ
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
# Кнопки должны быть точно такими же, как в фильтрах main.py и handlers.py
main_keyboard = [["🆕 Начать новый пост", "⚙️ Корректировать предыдущий"], ["❌ Отмена"]]
theme_keyboard = [["Бизнес", "Технологии", "Путешествия", "Здоровье"], ["Личный бренд", "Другая тема", "⬅️ Назад"]]
genre_keyboard = [["Информационный (обучение)", "Продающий (AIDA)", "Развлекательный (лайфхак)"], ["Сторителлинг (личная история)", "Провокация (хайп)", "⬅️ Назад"]]
