import logging
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Updater, CommandHandler, CallbackContext, MessageHandler, Filters

# Включаем логирование
logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO)
logger = logging.getLogger(__name__)

# Ваши каналы
OPEN_CHANNELS = ['@fsttswuy37']
CLOSED_CHANNELS = ['https://t.me/+t6ibtFPhTGVkN2Iy']
MY_CHANNEL_LINK = 'https://t.me/+t6ibtFPhTGVkN2Iy'

# Функция для проверки подписки
def check_subscription(update: Update, context: CallbackContext):
    user_id = update.effective_user.id
    chat_member_status = {}

    # Проверка подписки на каналы
    for channel in OPEN_CHANNELS + CLOSED_CHANNELS:
        chat_member = context.bot.get_chat_member(channel, user_id)
        chat_member_status[channel] = chat_member.status

    # Проверка подписки
    if all(status in ['member', 'administrator', 'creator'] for status in chat_member_status.values()):
        update.callback_query.answer(f"Вы подписаны на все необходимые каналы! Вот ссылка на мой канал: {MY_CHANNEL_LINK}")
    else:
        update.callback_query.answer("Вы еще не подписались на все необходимые каналы.")

# Функция для обработки команды /start
def start(update: Update, context: CallbackContext):
    keyboard = [
        [InlineKeyboardButton("Проверить подписки", callback_data='check_subscriptions')],
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    update.message.reply_text("Привет! Используйте кнопку ниже для проверки подписок.", reply_markup=reply_markup)

# Функция для обработки команды /setlink
def set_link(update: Update, context: CallbackContext):
    if context.args:
        global MY_CHANNEL_LINK
        MY_CHANNEL_LINK = context.args[0]
        update.message.reply_text(f"Ссылка на канал обновлена: {MY_CHANNEL_LINK}")
    else:
        update.message.reply_text("Пожалуйста, укажите новую ссылку.")

def main():
    # Замените 'YOUR_TOKEN' на токен вашего бота
    updater = Updater("7557745613:AAFTpWsCJ2bZMqD6GDwTynnqA8Nc-mRF1Rs")

    dp = updater.dispatcher
    dp.add_handler(CommandHandler("start", start))
    dp.add_handler(CommandHandler("setlink", set_link))
    dp.add_handler(MessageHandler(Filters.text & ~Filters.command, check_subscription))

    # Обработка нажатия на кнопку
    dp.add_handler(CallbackQueryHandler(check_subscription, pattern='check_subscriptions'))

    # Запускаем бота
    updater.start_polling()
    updater.idle()

if __name__ == '__main__':
    main()
