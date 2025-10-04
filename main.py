# main.py

from telegram.ext import Application, CommandHandler, MessageHandler, filters, ConversationHandler
from telegram import Update 
# ✅ ИСПРАВЛЕНО: logger убран из общего импорта и импортируется отдельно
from config import (
    TELEGRAM_BOT_TOKEN, CHOOSING_ACTION, CHOOSING_THEME, 
    CHOOSING_GENRE, GETTING_TOPIC, GETTING_CORRECTION, GETTING_ACCESS_CODE,
    main_keyboard, theme_keyboard, genre_keyboard
)
# ✅ ДОБАВЛЕНО: Явный импорт logger
from config import logger
# Импортируем функции из handlers.py и payment_service.py
from handlers import start, choose_action, choose_theme, choose_genre, generate_post, correct_post, cancel 
from payment_service import handle_access_code

def main() -> None:
    """Основная функция для запуска бота."""
    
    logger.info("Starting bot application...")
    
    application = Application.builder().token(TELEGRAM_BOT_TOKEN).build()

    conv_handler = ConversationHandler(
        entry_points=[CommandHandler("start", start)],
        states={
            CHOOSING_ACTION: [
                # 🔥 ИСПРАВЛЕНИЕ: Используем явный список текстов кнопок для надежности
                MessageHandler(filters.Text(["🆕 Начать новый пост", "⚙️ Корректировать предыдущий"]), choose_action)
            ],
            GETTING_ACCESS_CODE: [
                MessageHandler(filters.TEXT & ~filters.COMMAND, handle_access_code)
            ],
            CHOOSING_THEME: [
                MessageHandler(filters.Text([item for sublist in theme_keyboard for item in sublist if item != "⬅️ Назад"]), choose_theme)
            ],
            CHOOSING_GENRE: [
                MessageHandler(filters.Text([item for sublist in genre_keyboard for item in sublist if item != "⬅️ Назад"]), choose_genre)
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
