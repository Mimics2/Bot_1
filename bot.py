import logging
import asyncio
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, CallbackQueryHandler, ContextTypes

# ========== КОНФИГУРАЦИЯ ==========
BOT_TOKEN = "7557745613:AAFTpWsCJ2bZMqD6GDwTynnqA8Nc-mRF1Rs"
admin_id = 6646433980

# Ссылка на приватный канал
PRIVATE_CHANNEL_LINK = "https://t.me/your_private_channel"  # ЗАМЕНИТЕ НА РЕАЛЬНУЮ ССЫЛКУ

# Каналы для проверки подписки
channels_to_subscribe = {
    "Первый канал": "@example_channel1",  # ЗАМЕНИТЕ
    "Второй канал": -1001234567890,       # ЗАМЕНИТЕ
}

# Настройка логирования
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# ========== КОМАНДА /START ==========
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    user = update.effective_user
    if not user:
        return
    
    # Проверяем подписку на каналы
    is_subscribed = True
    not_subscribed_channels = []
    
    for channel_name, channel_id in channels_to_subscribe.items():
        try:
            chat_member = await context.bot.get_chat_member(chat_id=channel_id, user_id=user.id)
            if chat_member.status in ["left", "kicked"]:
                is_subscribed = False
                not_subscribed_channels.append(channel_name)
        except Exception as e:
            logger.error(f"Ошибка при проверке канала {channel_name}: {e}")
            is_subscribed = False
            not_subscribed_channels.append(channel_name)

    if is_subscribed:
        # Пользователь подписан на все каналы - даем ссылку
        keyboard = [
            [InlineKeyboardButton("🔐 Перейти в приватный канал", url=PRIVATE_CHANNEL_LINK)]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await update.message.reply_text(
            "✅ Вы подписаны на все каналы! Вот ссылка на приватный канал:",
            reply_markup=reply_markup
        )
    else:
        # Показываем каналы для подписки
        keyboard = []
        for channel_name, channel_id in channels_to_subscribe.items():
            if isinstance(channel_id, int) and channel_id < 0:
                invite_link = f"https://t.me/+{abs(channel_id + 1000000000000)}"
            else:
                invite_link = f"https://t.me/{channel_id.lstrip('@')}"
            
            keyboard.append([InlineKeyboardButton(f"📢 {channel_name}", url=invite_link)])

        keyboard.append([InlineKeyboardButton("✅ Я подписался", callback_data="check_subs")])
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await update.message.reply_text(
            f"Для доступа к приватному каналу подпишитесь на следующие каналы:\n"
            f"Не подписаны: {', '.join(not_subscribed_channels)}",
            reply_markup=reply_markup
        )

# ========== ПРОВЕРКА ПОДПИСКИ ==========
async def button(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    query = update.callback_query
    await query.answer()
    
    if query.data == "check_subs":
        user = query.from_user
        is_subscribed = True
        not_subscribed_channels = []
        
        for channel_name, channel_id in channels_to_subscribe.items():
            try:
                chat_member = await context.bot.get_chat_member(chat_id=channel_id, user_id=user.id)
                if chat_member.status in ["left", "kicked"]:
                    is_subscribed = False
                    not_subscribed_channels.append(channel_name)
            except Exception as e:
                logger.error(f"Ошибка при проверке канала {channel_name}: {e}")
                is_subscribed = False
                not_subscribed_channels.append(channel_name)

        if is_subscribed:
            keyboard = [
                [InlineKeyboardButton("🔐 Перейти в приватный канал", url=PRIVATE_CHANNEL_LINK)]
            ]
            reply_markup = InlineKeyboardMarkup(keyboard)
            
            await query.edit_message_text(
                "✅ Проверка пройдена! Вот ссылка на приватный канал:",
                reply_markup=reply_markup
            )
        else:
            await query.answer(
                f"Вы не подписаны на: {', '.join(not_subscribed_channels)}", 
                show_alert=True
            )

# ========== АДМИН КОМАНДЫ ==========
async def add_channel(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if update.effective_user.id != admin_id:
        await update.message.reply_text("❌ Нет прав")
        return

    if len(context.args) < 2:
        await update.message.reply_text("Использование: /addchannel Название @username_or_id")
        return

    channel_name = " ".join(context.args[:-1])
    channel_id = context.args[-1]
    
    try:
        channel_id = int(channel_id)
    except ValueError:
        pass
    
    channels_to_subscribe[channel_name] = channel_id
    await update.message.reply_text(f"✅ Канал '{channel_name}' добавлен")

async def broadcast(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if update.effective_user.id != admin_id:
        await update.message.reply_text("❌ Нет прав")
        return

    if not context.args:
        await update.message.reply_text("Использование: /broadcast сообщение")
        return

    message = " ".join(context.args)
    await update.message.reply_text(f"📢 Рассылка: {message}")

# ========== ЗАПУСК БОТА ==========
def main():
    application = Application.builder().token(BOT_TOKEN).build()
    
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("addchannel", add_channel))
    application.add_handler(CommandHandler("broadcast", broadcast))
    application.add_handler(CallbackQueryHandler(button))
    
    application.run_polling()

if __name__ == "__main__":
    main()
