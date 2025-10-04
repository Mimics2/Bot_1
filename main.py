# main.py

from telegram.ext import Application, CommandHandler, MessageHandler, filters, ConversationHandler
from telegram import Update 
# Импортируем ВСЕ константы и КЛАВИАТУРЫ из config.py
from config import (
    TELEGRAM_BOT_TOKEN, logger, CHOOSING_ACTION, CHOOSING_THEME, 
    CHOOSING_GENRE, GETTING_TOPIC, GETTING_CORRECTION, GETTING_ACCESS_CODE,
    main_keyboard, theme_keyboard, genre_keyboard
)
# Импортируем функции из handlers.py (handle_access_code теперь там)
from handlers import start, choose_action, choose_theme, choose_genre, generate_post, correct_post, cancel, handle_access_code

# 🔥 НОВЫЕ ЯВНЫЕ СПИСКИ КНОПОК
MAIN_ACTIONS = ["🆕 Начать новый пост", "⚙️ Корректировать предыдущий"]
THEME_ACTIONS = ["Бизнес", "Технологии", "Путешествия", "Здоровье", "Личный бренд", "Другая тема"]
GENRE_ACTIONS = ["Информационный (обучение)", "Продающий (AIDA)", "Развлекательный (лайфхак)", "Сторителлинг (личная история)", "Провокация (хайп)"]


def main() -> None:
    """Основная функция для запуска бота."""
    
    logger.info("Starting bot application...")
    
    application = Application.builder().token(TELEGRAM_BOT_TOKEN).build()

    conv_handler = ConversationHandler(
        entry_points=[CommandHandler("start", start)],
        states={
            CHOOSING_ACTION: [
                # 🔥 Используем явный список действий
                MessageHandler(filters.Text(MAIN_ACTIONS), choose_action)
            ],
            GETTING_ACCESS_CODE: [
                MessageHandler(filters.TEXT & ~filters.COMMAND, handle_access_code)
            ],
            CHOOSING_THEME: [
                # Фильтруем все кнопки темы И кнопку "⬅️ Назад"
                MessageHandler(filters.Text(THEME_ACTIONS + ["⬅️ Назад"]), choose_theme)
            ],
            CHOOSING_GENRE: [
                # Фильтруем все кнопки жанра И кнопку "⬅️ Назад"
                MessageHandler(filters.Text(GENRE_ACTIONS + ["⬅️ Назад"]), choose_genre)
            ],
            GETTING_TOPIC: [
                MessageHandler(filters.TEXT & ~filters.COMMAND, generate_post)
            ],
            GETTING_CORRECTION: [
                 MessageHandler(filters.TEXT & ~filters.COMMAND, correct_post)
            ],
        },
        fallbacks=[MessageHandler(filters.Text(["❌ Отмена"]), cancel)],
        allow_reentry=True
    )

    application.add_handler(conv_handler)
    
    logger.info("🤖 Бот запущен и готов к работе...")
    
    application.run_polling(allowed_updates=Update.ALL_TYPES)

if __name__ == '__main__':
    main()
