# main.py

from telegram.ext import Application, CommandHandler, MessageHandler, filters, ConversationHandler
from telegram import Update 
# Импортируем ВСЕ константы и КЛАВИАТУРЫ из config.py
from config import (
    TELEGRAM_BOT_TOKEN, logger, CHOOSING_ACTION, CHOOSING_THEME, 
    CHOOSING_GENRE, GETTING_TOPIC, GETTING_CORRECTION, GETTING_ACCESS_CODE,
    main_keyboard, theme_keyboard, genre_keyboard
)
# Импортируем функции из handlers.py и payment_service.py
from handlers import start, choose_action, choose_theme, choose_genre, generate_post, correct_post, cancel 
from payment_service import handle_access_code # Импортируем функцию, которая обрабатывает код

# 🔥 ЯВНЫЕ СПИСКИ КНОПОК ДЛЯ СТАБИЛЬНЫХ ФИЛЬТРОВ
MAIN_ACTIONS = ["✨ Новый пост", "⚙️ Корректировка текста"]
THEME_ACTIONS = ["Бизнес", "Технологии", "Путешествия", "Здоровье", "Личный бренд", "Другая тема", "⬅️ Назад"]
GENRE_ACTIONS = ["Информационный (обучение)", "Продающий (AIDA)", "Развлекательный", "Сторителлинг", "Провокация", "⬅️ Назад"]


def main() -> None:
    """Основная функция для запуска бота."""
    
    logger.info("Starting bot application...")
    
    application = Application.builder().token(TELEGRAM_BOT_TOKEN).build()

    conv_handler = ConversationHandler(
        entry_points=[CommandHandler("start", start)],
        states={
            CHOOSING_ACTION: [
                # Фильтр для действий (исключаем "❌ Отмена", так как он в fallbacks)
                MessageHandler(filters.Text(MAIN_ACTIONS), choose_action)
            ],
            GETTING_ACCESS_CODE: [
                # Фильтр для кода доступа
                MessageHandler(filters.TEXT & ~filters.COMMAND, handle_access_code)
            ],
            CHOOSING_THEME: [
                # Фильтр для кнопок темы и кнопки "⬅️ Назад"
                MessageHandler(filters.Text(THEME_ACTIONS), choose_theme)
            ],
            CHOOSING_GENRE: [
                # Фильтр для кнопок жанра и кнопки "⬅️ Назад"
                MessageHandler(filters.Text(GENRE_ACTIONS), choose_genre)
            ],
            GETTING_TOPIC: [
                # Фильтр для пользовательского текста (тема/идея)
                MessageHandler(filters.TEXT & ~filters.COMMAND, generate_post)
            ],
            GETTING_CORRECTION: [
                 # Фильтр для пользовательского текста (коррекция)
                 MessageHandler(filters.TEXT & ~filters.COMMAND, correct_post)
            ],
        },
        # Fallbacks - обработка команды "Отмена"
        fallbacks=[
            MessageHandler(filters.Text(["❌ Отмена"]), cancel),
            CommandHandler("start", start)
        ],
        allow_reentry=True
    )

    application.add_handler(conv_handler)
    
    logger.info("🤖 Бот запущен и готов к работе...")
    
    application.run_polling(allowed_updates=Update.ALL_TYPES)

if __name__ == '__main__':
    main()
