# main.py

from telegram.ext import Application, CommandHandler, MessageHandler, filters, ConversationHandler
from telegram import Update 
from config import (
    TELEGRAM_BOT_TOKEN, CHOOSING_ACTION, CHOOSING_THEME, 
    CHOOSING_GENRE, GETTING_TOPIC, GETTING_CORRECTION, GETTING_ACCESS_CODE,
    main_keyboard, theme_keyboard, genre_keyboard
)
from config import logger
from handlers import start, choose_action, choose_theme, choose_genre, generate_post, correct_post, cancel 
from payment_service import handle_access_code

# 🔥 Вспомогательные функции для создания надежных списков кнопок
# Эти функции теперь просто возвращают заранее определенные списки, избегая list comprehensions.
def get_main_actions():
    return ["🆕 Начать новый пост", "⚙️ Корректировать предыдущий"]

def get_theme_actions():
    return ["Бизнес", "Технологии", "Путешествия", "Здоровье", "Личный бренд", "Другая тема"]

def get_genre_actions():
    return ["Информационный (обучение)", "Продающий (AIDA)", "Развлекательный (лайфхак)", "Сторителлинг (личная история)", "Провокация (хайп)"]


def main() -> None:
    """Основная функция для запуска бота."""
    
    logger.info("Starting bot application...")
    
    application = Application.builder().token(TELEGRAM_BOT_TOKEN).build()

    conv_handler = ConversationHandler(
        entry_points=[CommandHandler("start", start)],
        states={
            CHOOSING_ACTION: [
                # ✅ ИСПРАВЛЕНО: Явный список для основных действий
                MessageHandler(filters.Text(get_main_actions()), choose_action)
            ],
            GETTING_ACCESS_CODE: [
                MessageHandler(filters.TEXT & ~filters.COMMAND, handle_access_code)
            ],
            CHOOSING_THEME: [
                # ✅ ИСПРАВЛЕНО: Обрабатываем все кнопки ТЕМЫ и кнопку НАЗАД
                MessageHandler(filters.Text(get_theme_actions() + ["⬅️ Назад"]), choose_theme)
            ],
            CHOOSING_GENRE: [
                # ✅ ИСПРАВЛЕНО: Обрабатываем все кнопки ЖАНРА и кнопку НАЗАД
                MessageHandler(filters.Text(get_genre_actions() + ["⬅️ Назад"]), choose_genre)
            ],
            GETTING_TOPIC: [
                MessageHandler(filters.TEXT & ~filters.COMMAND, generate_post)
            ],
            GETTING_CORRECTION: [
                 MessageHandler(filters.TEXT & ~filters.COMMAND, correct_post)
            ],
        },
        # Обработчик кнопки "Отмена" всегда срабатывает
        fallbacks=[MessageHandler(filters.Text(["❌ Отмена"]), cancel)],
        allow_reentry=True
    )

    application.add_handler(conv_handler)
    
    logger.info("🤖 Бот запущен и готов к работе...")
    
    application.run_polling(allowed_updates=Update.ALL_TYPES)

if __name__ == '__main__':
    main()
