# main.py

from telegram.ext import Application, CommandHandler, MessageHandler, filters, ConversationHandler
from telegram import Update 
# ✅ Импортируем ВСЕ константы и КЛАВИАТУРЫ из config.py
from config import (
    TELEGRAM_BOT_TOKEN, CHOOSING_ACTION, CHOOSING_THEME, 
    CHOOSING_GENRE, GETTING_TOPIC, GETTING_CORRECTION, GETTING_ACCESS_CODE,
    main_keyboard, theme_keyboard, genre_keyboard
)
# ✅ Импортируем logger отдельно, чтобы избежать конфликта при циклическом импорте
from config import logger

# Импортируем функции из handlers.py и payment_service.py
from handlers import start, choose_action, choose_theme, choose_genre, generate_post, correct_post, cancel 
from payment_service import handle_access_code

# 🔥 ИСПРАВЛЕНИЕ: Явно задаем тексты кнопок для надежности (нет list comprehension)
MAIN_ACTIONS = ["🆕 Начать новый пост", "⚙️ Корректировать предыдущий"]
FALLBACK_CANCEL = ["❌ Отмена"]
THEME_ACTIONS_ALL = ["Бизнес", "Технологии", "Путешествия", "Здоровье", "Личный бренд", "Другая тема", "⬅️ Назад"]
GENRE_ACTIONS_ALL = ["Информационный (обучение)", "Продающий (AIDA)", "Развлекательный (лайфхак)", "Сторителлинг (личная история)", "Провокация (хайп)", "⬅️ Назад"]


def main() -> None:
    """Основная функция для запуска бота."""
    
    logger.info("Starting bot application...")
    
    application = Application.builder().token(TELEGRAM_BOT_TOKEN).build()

    conv_handler = ConversationHandler(
        entry_points=[CommandHandler("start", start)],
        states={
            CHOOSING_ACTION: [
                # ✅ Фильтр для главных действий 
                MessageHandler(filters.Text(MAIN_ACTIONS), choose_action)
            ],
            GETTING_ACCESS_CODE: [
                MessageHandler(filters.TEXT & ~filters.COMMAND, handle_access_code)
            ],
            CHOOSING_THEME: [
                # ✅ Фильтр для всех кнопок тем и "Назад"
                MessageHandler(filters.Text(THEME_ACTIONS_ALL), choose_theme)
            ],
            CHOOSING_GENRE: [
                # ✅ Фильтр для всех кнопок жанров и "Назад"
                MessageHandler(filters.Text(GENRE_ACTIONS_ALL), choose_genre)
            ],
            GETTING_TOPIC: [
                MessageHandler(filters.TEXT & ~filters.COMMAND, generate_post)
            ],
            GETTING_CORRECTION: [
                 MessageHandler(filters.TEXT & ~filters.COMMAND, correct_post)
            ],
        },
        # Обработчик кнопки "Отмена" всегда срабатывает
        fallbacks=[MessageHandler(filters.Text(FALLBACK_CANCEL), cancel)],
        allow_reentry=True
    )

    application.add_handler(conv_handler)
    
    logger.info("🤖 Бот запущен и готов к работе...")
    
    application.run_polling(allowed_updates=Update.ALL_TYPES)

if __name__ == '__main__':
    main()
