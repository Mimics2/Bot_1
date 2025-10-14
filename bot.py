import logging
import sqlite3
import os
from telegram import (
    Update,
    InlineKeyboardButton,
    InlineKeyboardMarkup,
    BotCommand
)
from telegram.ext import (
    Updater,
    CommandHandler,
    CallbackQueryHandler,
    CallbackContext
)

# Настройки
BOT_TOKEN = os.getenv("BOT_TOKEN", "YOUR_BOT_TOKEN")
ADMIN_ID = int(os.getenv("ADMIN_ID", "123456789"))  # Ваш ID в Telegram

# Используем относительный путь для Railway
DB_PATH = os.path.join(os.path.dirname(__file__), "bot.db")

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
logger = logging.getLogger(__name__)

class Database:
    def __init__(self, db_path):
        self.db_path = db_path
        logger.info(f"Инициализация базы данных по пути: {db_path}")
        self.init_db()

    def init_db(self):
        try:
            # Создаем директорию если нужно
            os.makedirs(os.path.dirname(self.db_path), exist_ok=True)
            
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
            logger.info("База данных успешно инициализирована")
        except Exception as e:
            logger.error(f"Ошибка инициализации базы данных: {e}")
            raise

    def add_user(self, user_id, username, full_name, referrer_id=None):
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            cursor.execute('''
                INSERT OR REPLACE INTO users (user_id, username, full_name, referrer_id)
                VALUES (?, ?, ?, ?)
            ''', (user_id, username, full_name, referrer_id))
            conn.commit()
            conn.close()
        except Exception as e:
            logger.error(f"Ошибка добавления пользователя: {e}")

    def get_user(self, user_id):
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            cursor.execute('SELECT * FROM users WHERE user_id = ?', (user_id,))
            user = cursor.fetchone()
            conn.close()
            return user
        except Exception as e:
            logger.error(f"Ошибка получения пользователя: {e}")
            return None

    def update_subscription(self, user_id, channel_username, subscribed):
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            cursor.execute('''
                INSERT OR REPLACE INTO subscriptions (user_id, channel_username, subscribed, last_check)
                VALUES (?, ?, ?, CURRENT_TIMESTAMP)
            ''', (user_id, channel_username, subscribed))
            conn.commit()
            conn.close()
        except Exception as e:
            logger.error(f"Ошибка обновления подписки: {e}")

    def get_subscription_status(self, user_id, channel_username):
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            cursor.execute('''
                SELECT subscribed FROM subscriptions 
                WHERE user_id = ? AND channel_username = ?
            ''', (user_id, channel_username))
            result = cursor.fetchone()
            conn.close()
            return result[0] if result else False
        except Exception as e:
            logger.error(f"Ошибка получения статуса подписки: {e}")
            return False

    def get_all_users(self):
        """Получить всех пользователей (для админа)"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            cursor.execute('SELECT user_id FROM users')
            users = cursor.fetchall()
            conn.close()
            return users
        except Exception as e:
            logger.error(f"Ошибка получения всех пользователей: {e}")
            return []

# Инициализация базы данных
try:
    db = Database(DB_PATH)
    logger.info("База данных успешно загружена")
except Exception as e:
    logger.error(f"Критическая ошибка инициализации БД: {e}")
    # Создаем заглушку чтобы бот мог запуститься
    db = None

def start(update: Update, context: CallbackContext):
    if db is None:
        update.message.reply_text("❌ Бот временно недоступен. Попробуйте позже.")
        return
        
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
    if check_subscriptions(update, context):
        show_main_menu(update, context)
    else:
        show_subscription_request(update, context)

def check_subscriptions(update: Update, context: CallbackContext):
    user = update.effective_user
    bot = context.bot
    
    all_subscribed = True
    for channel in CHANNELS:
        try:
            chat_member = bot.get_chat_member(
                chat_id=f"@{channel['username']}",
                user_id=user.id
            )
            subscribed = chat_member.status in ['member', 'administrator', 'creator']
            db.update_subscription(user.id, channel['username'], subscribed)
            
            if not subscribed:
                all_subscribed = False
        except Exception as e:
            logging.error(f"Ошибка проверки подписки на {channel['username']}: {e}")
            all_subscribed = False
    
    return all_subscribed

def show_subscription_request(update: Update, context: CallbackContext):
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
        update.callback_query.edit_message_text(text, reply_markup=reply_markup)
    else:
        update.message.reply_text(text, reply_markup=reply_markup)

def show_main_menu(update: Update, context: CallbackContext):
    user = update.effective_user
    
    text = f"""
🎉 Добро пожаловать, {user.first_name}!

📊 Ваша реферальная ссылка:
`https://t.me/{context.bot.username}?start={user.id}`

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
        update.callback_query.edit_message_text(text, reply_markup=reply_markup, parse_mode='Markdown')
    else:
        update.message.reply_text(text, reply_markup=reply_markup, parse_mode='Markdown')

def button_handler(update: Update, context: CallbackContext):
    query = update.callback_query
    query.answer()
    
    if query.data == "check_subs":
        if check_subscriptions(update, context):
            show_main_menu(update, context)
        else:
            show_subscription_request(update, context)
    
    elif query.data == "get_ref":
        user = update.effective_user
        ref_link = f"https://t.me/{context.bot.username}?start={user.id}"
        query.edit_message_text(
            f"🔗 Ваша реферальная ссылка:\n`{ref_link}`\n\nПоделитесь этой ссылкой с друзьями!",
            parse_mode='Markdown'
        )
    
    elif query.data == "stats":
        query.edit_message_text("📊 Статистика в разработке...")
    
    elif query.data == "admin_panel":
        if update.effective_user.id == ADMIN_ID:
            show_admin_panel(update, context)

def show_admin_panel(update: Update, context: CallbackContext):
    if db is None:
        update.callback_query.edit_message_text("❌ База данных недоступна")
        return
        
    total_users = len(db.get_all_users())
    
    text = f"""
👑 Админ-панель

📊 Общая статистика:
👥 Всего пользователей: {total_users}

Доступные действия:
    """
    
    keyboard = [
        [InlineKeyboardButton("📊 Полная статистика", callback_data="full_stats")],
        [InlineKeyboardButton("📢 Рассылка", callback_data="broadcast")],
        [InlineKeyboardButton("◀️ Назад", callback_data="main_menu")]
    ]
    
    reply_markup = InlineKeyboardMarkup(keyboard)
    update.callback_query.edit_message_text(text, reply_markup=reply_markup)

def set_commands(updater):
    commands = [
        BotCommand("start", "Запустить бота"),
        BotCommand("stats", "Статистика"),
        BotCommand("referral", "Реферальная ссылка")
    ]
    updater.bot.set_my_commands(commands)

def main():
    if db is None:
        logger.error("Не удалось инициализировать базу данных. Бот не может быть запущен.")
        return
        
    updater = Updater(token=BOT_TOKEN, use_context=True)
    dispatcher = updater.dispatcher
    
    # Обработчики команд
    dispatcher.add_handler(CommandHandler("start", start))
    dispatcher.add_handler(CommandHandler("stats", show_main_menu))
    dispatcher.add_handler(CommandHandler("referral", show_main_menu))
    
    # Обработчики кнопок
    dispatcher.add_handler(CallbackQueryHandler(button_handler))
    
    # Установка команд бота
    set_commands(updater)
    
    # Запуск бота
    logger.info("Бот запускается...")
    updater.start_polling()
    updater.idle()

if __name__ == "__main__":
    main()
