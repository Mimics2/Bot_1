# main.py

from telegram.ext import Application, CommandHandler, MessageHandler, filters, ConversationHandler
from config import TELEGRAM_BOT_TOKEN, logger, CHOOSING_ACTION
# Импортируем клавиатуру и все обработчики из handlers, чтобы ConversationHandler мог работать
from handlers import start, choose_action, choose_theme, choose_genre, generate_post, correct_post, cancel, main_keyboard, theme_keyboard, genre_keyboard
from payment_service import activate_pro_command

def main() -> None:
    """Основная функция для запуска бота."""
    
    logger.info("Starting bot application...")
    
    application = Application.builder().token(TELEGRAM_BOT_TOKEN).build()

    # Создаем обработчик диалога (ConversationHandler)
    conv_handler = ConversationHandler(
        entry_points=[CommandHandler("start", start)],
        states={
            CHOOSING_ACTION: [
                MessageHandler(filters.Text([item for sublist in main_keyboard for item in sublist if item != "❌ Отмена"]), choose_action)
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
        fallbacks=[MessageHandler(filters.Text(["❌ Отмена"]), cancel)],
        allow_reentry=True
    )

    application.add_handler(conv_handler)
    
    # Добавляем тестовую команду для активации PRO-доступа
    application.add_handler(CommandHandler("activate_pro", activate_pro_command))
    
    logger.info("🤖 Бот запущен и готов к работе...")
    
    application.run_polling(allowed_updates=Update.ALL_TYPES)

if __name__ == '__main__':
    # Ошибка в Traceback указывает, что запуск происходил из 'main.py'
    # Поэтому оставляем точку входа здесь.
    main()
