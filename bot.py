import logging
import sqlite3
from telegram import (
    Update,
    InlineKeyboardButton,
    InlineKeyboardMarkup,
    BotCommand
)
from telegram.ext import (
    Application,
    CommandHandler,
    CallbackQueryHandler,
    ContextTypes
)

# Настройки
BOT_TOKEN = "YOUR_BOT_TOKEN"
ADMIN_ID = 123456789  # Ваш ID в Telegram
DB_PATH = "/data/bot.db"  # Путь к базе данных (на Railway используйте /data)

# Список каналов для проверки (username без @)
CHANNELS = [
    {"username": "private_channel1", "name": "Приватный канал 1"},
    {"username": "private_channel2", "name": "Приватный канал 2"}
]

# Настройка логирования
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)

class Database:
    def __init__(self, db_path):
        self.db_path = db_path
        self.init_db()

    def init_db(self):
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Таблица пользователей
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS users (
                user_id INTEGER PRIMARY KEY,
                username TEXT,
                full_name TEXT,
                referrer_id INTEGER,
                joined_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        # Таблица подписок
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS subscriptions (
                user_id INTEGER,
                channel_username TEXT,
                subscribed BOOLEAN DEFAULT FALSE,
                last_check TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                PRIMARY KEY (user_id, channel_username)
            )
        ''')
        
        conn.commit()
        conn.close()

    def add_user(self, user_id, username, full_name, referrer_id=None):
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute('''
            INSERT OR REPLACE INTO users (user_id, username, full_name, referrer_id)
            VALUES (?, ?, ?, ?)
        ''', (user_id, username, full_name, referrer_id))
        conn.commit()
        conn.close()

    def get_user(self, user_id):
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute('SELECT * FROM users WHERE user_id = ?', (user_id,))
        user = cursor.fetchone()
        conn.close()
        return user

    def update_subscription(self, user_id, channel_username, subscribed):
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute('''
            INSERT OR REPLACE INTO subscriptions (user_id, channel_username, subscribed, last_check)
            VALUES (?, ?, ?, CURRENT_TIMESTAMP)
        ''', (user_id, channel_username, subscribed))
        conn.commit()
        conn.close()

    def get_subscription_status(self, user_id, channel_username):
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute('''
            SELECT subscribed FROM subscriptions 
            WHERE user_id = ? AND channel_username = ?
        ''', (user_id, channel_username))
        result = cursor.fetchone()
        conn.close()
        return result[0] if result else False

# Инициализация базы данных
db = Database(DB_PATH)

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    referrer_id = None
    
    # Проверка реферальной ссылки
    if context.args:
        try:
            referrer_id = int(context.args[0])
        except ValueError:
            referrer_id = None

    # Добавление пользователя в базу
    db.add_user(
        user_id=user.id,
        username=user.username,
        full_name=user.full_name,
        referrer_id=referrer_id
    )

    # Проверка подписки
    if await check_subscriptions(update, context):
        await show_main_menu(update, context)
    else:
        await show_subscription_request(update, context)

async def check_subscriptions(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    bot = context.bot
    
    all_subscribed = True
    for channel in CHANNELS:
        try:
            chat_member = await bot.get_chat_member(
                chat_id=f"@{channel['username']}",
                user_id=user.id
            )
            subscribed = chat_member.status in ['member', 'administrator', 'creator']
            db.update_subscription(user.id, channel['username'], subscribed)
            
            if not subscribed:
                all_subscribed = False
        except Exception as e:
            logging.error(f"Ошибка проверки подписки: {e}")
            all_subscribed = False
    
    return all_subscribed

async def show_subscription_request(update: Update, context: ContextTypes.DEFAULT_TYPE):
    keyboard = []
    
    for channel in CHANNELS:
        keyboard.append([
            InlineKeyboardButton(
                f"📢 Подписаться на {channel['name']}",
                url=f"https://t.me/{channel['username']}"
            )
        ])
    
    keyboard.append([InlineKeyboardButton("✅ Я подписался", callback_data="check_subs")])
    
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    text = "📋 Для доступа к боту необходимо подписаться на наши каналы:"
    
    if update.callback_query:
        await update.callback_query.edit_message_text(text, reply_markup=reply_markup)
    else:
        await update.message.reply_text(text, reply_markup=reply_markup)

async def show_main_menu(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    referrer_count = 0  # Здесь можно добавить подсчет рефералов
    
    text = f"""
🎉 Добро пожаловать, {user.first_name}!

📊 Ваша реферальная ссылка:
`https://t.me/{(await context.bot.get_me()).username}?start={user.id}`

👥 Приглашено пользователей: {referrer_count}

Выберите действие:
    """
    
    keyboard = [
        [InlineKeyboardButton("🔗 Получить реферальную ссылку", callback_data="get_ref")],
        [InlineKeyboardButton("📊 Статистика", callback_data="stats")],
        [InlineKeyboardButton("🔍 Проверить подписку", callback_data="check_subs")]
    ]
    
    if user.id == ADMIN_ID:
        keyboard.append([InlineKeyboardButton("👑 Админ-панель", callback_data="admin_panel")])
    
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    if update.callback_query:
        await update.callback_query.edit_message_text(text, reply_markup=reply_markup, parse_mode='Markdown')
    else:
        await update.message.reply_text(text, reply_markup=reply_markup, parse_mode='Markdown')

async def button_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    
    if query.data == "check_subs":
        if await check_subscriptions(update, context):
            await show_main_menu(update, context)
        else:
            await show_subscription_request(update, context)
    
    elif query.data == "get_ref":
        user = update.effective_user
        ref_link = f"https://t.me/{(await context.bot.get_me()).username}?start={user.id}"
        await query.edit_message_text(
            f"🔗 Ваша реферальная ссылка:\n`{ref_link}`\n\nПоделитесь этой ссылкой с друзьями!",
            parse_mode='Markdown'
        )
    
    elif query.data == "stats":
        # Здесь можно добавить статистику
        await query.edit_message_text("📊 Статистика в разработке...")
    
    elif query.data == "admin_panel":
        if update.effective_user.id == ADMIN_ID:
            await show_admin_panel(update, context)

async def show_admin_panel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    # Статистика для админа
    total_users = len([db.get_user(user_id) for user_id in set([u[0] for u in db.get_all_users()])])
    
    text = f"""
👑 Админ-панель

📊 Общая статистика:
👥 Всего пользователей: {total_users}
📈 Активных подписок: {total_users}  # Здесь нужно добавить реальную логику

Доступные действия:
    """
    
    keyboard = [
        [InlineKeyboardButton("📊 Полная статистика", callback_data="full_stats")],
        [InlineKeyboardButton("📢 Рассылка", callback_data="broadcast")],
        [InlineKeyboardButton("◀️ Назад", callback_data="main_menu")]
    ]
    
    reply_markup = InlineKeyboardMarkup(keyboard)
    await update.callback_query.edit_message_text(text, reply_markup=reply_markup)

async def set_commands(application: Application):
    commands = [
        BotCommand("start", "Запустить бота"),
        BotCommand("stats", "Статистика"),
        BotCommand("referral", "Реферальная ссылка")
    ]
    await application.bot.set_my_commands(commands)

def main():
    application = Application.builder().token(BOT_TOKEN).build()
    
    # Обработчики команд
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("stats", show_main_menu))
    application.add_handler(CommandHandler("referral", show_main_menu))
    
    # Обработчики кнопок
    application.add_handler(CallbackQueryHandler(button_handler))
    
    # Установка команд бота
    application.post_init = set_commands
    
    # Запуск бота
    application.run_polling()

if __name__ == "__main__":
    main()
