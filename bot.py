import logging
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, CallbackQueryHandler, ContextTypes

# Настройки
BOT_TOKEN = "YOUR_BOT_TOKEN"
ADMIN_ID = 6646433980  # Ваш ID

# Список каналов для проверки. Используйте @username для публичных или ID для приватных.
CHANNELS = {
    "Крипто-новости": "@crypto_news",
    "Трейдинг ликбез": -1001234567890,  # Пример ID приватного канала
}

PRIVATE_CHANNEL_LINK = "https://t.me/your_private_channel"  # Ваша ссылка

# Команда /start
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    user = update.effective_user
    not_subscribed = []

    # Проверяем подписку на каждый канал
    for channel_name, channel_id in CHANNELS.items():
        try:
            chat_member = await context.bot.get_chat_member(chat_id=channel_id, user_id=user.id)
            if chat_member.status in ["left", "kicked"]:
                not_subscribed.append(channel_name)
        except Exception as e:
            logging.error(f"Ошибка проверки канала {channel_name}: {e}")
            not_subscribed.append(channel_name)

    # Если подписан на все - даем ссылку
    if not not_subscribed:
        keyboard = [[InlineKeyboardButton("🔐 Перейти в приватный канал", url=PRIVATE_CHANNEL_LINK)]]
        reply_markup = InlineKeyboardMarkup(keyboard)
        await update.message.reply_text("Поздравляем! Вот ссылка на приватный канал:", reply_markup=reply_markup)
    else:
        # Показываем кнопки для подписки
        keyboard = []
        for channel_name, channel_id in CHANNELS.items():
            # Формируем ссылку-приглашение
            if isinstance(channel_id, int) and channel_id < 0:
                invite_link = f"https://t.me/+{abs(channel_id + 1000000000000)}"  # Для приватных каналов
            else:
                invite_link = f"https://t.me/{channel_id.lstrip('@')}"  # Для публичных каналов
            keyboard.append([InlineKeyboardButton(f"Подписаться: {channel_name}", url=invite_link)])
        
        keyboard.append([InlineKeyboardButton("✅ Я подписался", callback_data="check_subscription")])
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await update.message.reply_text(
            "Для доступа необходимо подписаться на следующие каналы:",
            reply_markup=reply_markup
        )

# Обработка нажатия кнопки "Я подписался"
async def button(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    query = update.callback_query
    await query.answer()
    
    if query.data == "check_subscription":
        user = query.from_user
        not_subscribed = []

        for channel_name, channel_id in CHANNELS.items():
            try:
                chat_member = await context.bot.get_chat_member(chat_id=channel_id, user_id=user.id)
                if chat_member.status in ["left", "kicked"]:
                    not_subscribed.append(channel_name)
            except Exception as e:
                logging.error(f"Ошибка проверки канала {channel_name}: {e}")
                not_subscribed.append(channel_name)

        if not_subscribed:
            await query.answer(f"Вы не подписаны на: {', '.join(not_subscribed)}", show_alert=True)
        else:
            keyboard = [[InlineKeyboardButton("🔐 Перейти в приватный канал", url=PRIVATE_CHANNEL_LINK)]]
            reply_markup = InlineKeyboardMarkup(keyboard)
            await query.edit_message_text("Поздравляем! Вот ссылка на приватный канал:", reply_markup=reply_markup)

def main():
    application = Application.builder().token(BOT_TOKEN).build()
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CallbackQueryHandler(button))
    application.run_polling()

if __name__ == "__main__":
    main()
