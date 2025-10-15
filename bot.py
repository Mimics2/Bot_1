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
    Application,
    CommandHandler,
    CallbackQueryHandler,
    ContextTypes,
    MessageHandler,
    filters
)

# Настройки
BOT_TOKEN = os.getenv("BOT_TOKEN", "YOUR_BOT_TOKEN")
ADMIN_ID = int(os.getenv("ADMIN_ID", "123456789"))  # Ваш ID в Telegram
YOUR_CHANNEL_REFERRAL = "https://t.me/your_channel"  # Замените на вашу реферальную ссылку

# Используем относительный путь для Railway
DB_PATH = os.path.join(os.path.dirname(__file__), "bot.db")

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
                    joined_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    referral_shown BOOLEAN DEFAULT FALSE
                )
            ''')
            
            # Таблица каналов для проверки
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS channels (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    channel_username TEXT UNIQUE,
                    channel_name TEXT,
                    added_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            ''')
            
            # Таблица подписок
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS subscriptions (
                    user_id INTEGER,
                    channel_id INTEGER,
                    subscribed BOOLEAN DEFAULT FALSE,
                    last_check TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    PRIMARY KEY (user_id, channel_id),
                    FOREIGN KEY (channel_id) REFERENCES channels (id)
                )
            ''')
            
            conn.commit()
            conn.close()
            logger.info("База данных успешно инициализирована")
        except Exception as e:
            logger.error(f"Ошибка инициализации базы данных: {e}")
            raise

    def add_user(self, user_id, username, full_name):
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            cursor.execute('''
                INSERT OR IGNORE INTO users (user_id, username, full_name)
                VALUES (?, ?, ?)
            ''', (user_id, username, full_name))
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

    def set_referral_shown(self, user_id):
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            cursor.execute('''
                UPDATE users SET referral_shown = TRUE WHERE user_id = ?
            ''', (user_id,))
            conn.commit()
            conn.close()
        except Exception as e:
            logger.error(f"Ошибка обновления статуса рефералки: {e}")

    def has_referral_been_shown(self, user_id):
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            cursor.execute('SELECT referral_shown FROM users WHERE user_id = ?', (user_id,))
            result = cursor.fetchone()
            conn.close()
            return result[0] if result else False
        except Exception as e:
            logger.error(f"Ошибка проверки статуса рефералки: {e}")
            return False

    def add_channel(self, channel_username, channel_name):
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            cursor.execute('''
                INSERT OR REPLACE INTO channels (channel_username, channel_name)
                VALUES (?, ?)
            ''', (channel_username, channel_name))
            conn.commit()
            conn.close()
            return True
        except Exception as e:
            logger.error(f"Ошибка добавления канала: {e}")
            return False

    def remove_channel(self, channel_id):
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            cursor.execute('DELETE FROM channels WHERE id = ?', (channel_id,))
            cursor.execute('DELETE FROM subscriptions WHERE channel_id = ?', (channel_id,))
            conn.commit()
            conn.close()
            return True
        except Exception as e:
            logger.error(f"Ошибка удаления канала: {e}")
            return False

    def get_channels(self):
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            cursor.execute('SELECT * FROM channels ORDER BY id')
            channels = cursor.fetchall()
            conn.close()
            return channels
        except Exception as e:
            logger.error(f"Ошибка получения каналов: {e}")
            return []

    def update_subscription(self, user_id, channel_id, subscribed):
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            cursor.execute('''
                INSERT OR REPLACE INTO subscriptions (user_id, channel_id, subscribed, last_check)
                VALUES (?, ?, ?, CURRENT_TIMESTAMP)
            ''', (user_id, channel_id, subscribed))
            conn.commit()
            conn.close()
        except Exception as e:
            logger.error(f"Ошибка обновления подписки: {e}")

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
    db = None

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if db is None:
        await update.message.reply_text("❌ Бот временно недоступен. Попробуйте позже.")
        return
        
    user = update.effective_user
    
    # Добавление пользователя в базу
    db.add_user(
        user_id=user.id,
        username=user.username,
        full_name=user.full_name
    )

    # Проверка подписки
    if await check_subscriptions(update, context):
        await show_referral_message(update, context)
        await show_main_menu(update, context)
    else:
        await show_subscription_request(update, context)

async def check_subscriptions(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    bot = context.bot
    channels = db.get_channels()
    
    if not channels:
        # Если каналов нет, пропускаем проверку
        return True
    
    all_subscribed = True
    
    for channel in channels:
        channel_id, channel_username, channel_name, _ = channel
        try:
            # Убираем @ если есть
            clean_username = channel_username.lstrip('@')
            
            chat_member = await bot.get_chat_member(
                chat_id=f"@{clean_username}",
                user_id=user.id
            )
            subscribed = chat_member.status in ['member', 'administrator', 'creator']
            db.update_subscription(user.id, channel_id, subscribed)
            
            if not subscribed:
                all_subscribed = False
                
        except Exception as e:
            logger.error(f"Ошибка проверки подписки на {channel_username}: {e}")
            all_subscribed = False
    
    return all_subscribed

async def show_referral_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    
    # Проверяем, показывали ли уже рефералку этому пользователю
    if not db.has_referral_been_shown(user.id):
        text = f"""
🎉 Спасибо за подписку! 

👉 **Присоединяйтесь к нашему основному каналу:**
{YOUR_CHANNEL_REFERRAL}

Там вы найдете:
• Эксклюзивный контент
• Новости и обновления
• Полезные материалы
        """
        
        keyboard = [
            [InlineKeyboardButton("📢 Перейти в канал", url=YOUR_CHANNEL_REFERRAL)]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        if update.callback_query:
            await update.callback_query.message.reply_text(text, reply_markup=reply_markup)
        else:
            await update.message.reply_text(text, reply_markup=reply_markup)
        
        # Помечаем, что рефералка показана
        db.set_referral_shown(user.id)

async def show_subscription_request(update: Update, context: ContextTypes.DEFAULT_TYPE):
    channels = db.get_channels()
    
    if not channels:
        await update.message.reply_text("ℹ️ На данный момент нет каналов для подписки.")
        await show_main_menu(update, context)
        return
    
    keyboard = []
    
    for channel in channels:
        channel_id, channel_username, channel_name, _ = channel
        clean_username = channel_username.lstrip('@')
        keyboard.append([
            InlineKeyboardButton(
                f"📢 Подписаться на {channel_name}",
                url=f"https://t.me/{clean_username}"
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
    
    text = f"""
🎉 Добро пожаловать, {user.first_name}!

Доступные команды:
/start - Главное меню
/check - Проверить подписку

Выберите действие:
    """
    
    keyboard = [
        [InlineKeyboardButton("🔍 Проверить подписку", callback_data="check_subs")]
    ]
    
    if user.id == ADMIN_ID:
        keyboard.append([InlineKeyboardButton("👑 Админ-панель", callback_data="admin_panel")])
    
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    if update.callback_query:
        await update.callback_query.edit_message_text(text, reply_markup=reply_markup)
    else:
        await update.message.reply_text(text, reply_markup=reply_markup)

async def button_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    
    if query.data == "check_subs":
        if await check_subscriptions(update, context):
            await show_referral_message(update, context)
            await show_main_menu(update, context)
        else:
            await show_subscription_request(update, context)
    
    elif query.data == "admin_panel":
        if update.effective_user.id == ADMIN_ID:
            await show_admin_panel(update, context)

    elif query.data == "manage_channels":
        if update.effective_user.id == ADMIN_ID:
            await show_manage_channels(update, context)

    elif query.data == "add_channel":
        if update.effective_user.id == ADMIN_ID:
            context.user_data['awaiting_channel'] = True
            await query.edit_message_text(
                "📝 Введите данные канала в формате:\n"
                "`@username Название канала`\n\n"
                "Пример:\n"
                "`@my_channel Мой канал`",
                parse_mode='Markdown'
            )

    elif query.data.startswith("delete_channel_"):
        if update.effective_user.id == ADMIN_ID:
            channel_id = int(query.data.replace("delete_channel_", ""))
            channel = None
            channels = db.get_channels()
            for ch in channels:
                if ch[0] == channel_id:
                    channel = ch
                    break
            
            if channel and db.remove_channel(channel_id):
                await query.edit_message_text(f"✅ Канал {channel[2]} удален!")
            else:
                await query.edit_message_text("❌ Ошибка при удалении канала!")
            await show_manage_channels(update, context)

    elif query.data == "back_to_admin":
        if update.effective_user.id == ADMIN_ID:
            await show_admin_panel(update, context)

    elif query.data == "back_to_main":
        await show_main_menu(update, context)

async def show_admin_panel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if db is None:
        await update.callback_query.edit_message_text("❌ База данных недоступна")
        return
        
    total_users = len(db.get_all_users())
    channels = db.get_channels()
    
    text = f"""
👑 Админ-панель

📊 Статистика:
👥 Всего пользователей: {total_users}
📢 Каналов для проверки: {len(channels)}
🔗 Реферальная ссылка: {YOUR_CHANNEL_REFERRAL}

Доступные действия:
    """
    
    keyboard = [
        [InlineKeyboardButton("📢 Управление каналами", callback_data="manage_channels")],
        [InlineKeyboardButton("📊 Статистика пользователей", callback_data="user_stats")],
        [InlineKeyboardButton("◀️ Назад", callback_data="back_to_main")]
    ]
    
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    if update.callback_query:
        await update.callback_query.edit_message_text(text, reply_markup=reply_markup)
    else:
        await update.message.reply_text(text, reply_markup=reply_markup)

async def show_manage_channels(update: Update, context: ContextTypes.DEFAULT_TYPE):
    channels = db.get_channels()
    
    text = "📢 Управление каналами:\n\n"
    
    if channels:
        for channel in channels:
            text += f"• {channel[2]} (@{channel[1]})\n"
    else:
        text += "ℹ️ Нет добавленных каналов\n"
    
    keyboard = [
        [InlineKeyboardButton("➕ Добавить канал", callback_data="add_channel")]
    ]
    
    # Кнопки удаления для каждого канала
    for channel in channels:
        keyboard.append([
            InlineKeyboardButton(f"❌ Удалить {channel[2]}", callback_data=f"delete_channel_{channel[0]}")
        ])
    
    keyboard.append([InlineKeyboardButton("◀️ Назад", callback_data="admin_panel")])
    
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    if update.callback_query:
        await update.callback_query.edit_message_text(text, reply_markup=reply_markup)
    else:
        await update.message.reply_text(text, reply_markup=reply_markup)

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != ADMIN_ID:
        return
        
    if context.user_data.get('awaiting_channel'):
        try:
            text = update.message.text.strip()
            if text.startswith('@'):
                parts = text.split(' ', 1)
                if len(parts) == 2:
                    channel_username = parts[0]
                    channel_name = parts[1]
                    
                    if db.add_channel(channel_username, channel_name):
                        await update.message.reply_text(f"✅ Канал {channel_name} добавлен!")
                    else:
                        await update.message.reply_text("❌ Ошибка при добавлении канала!")
                else:
                    await update.message.reply_text("❌ Неверный формат! Используйте: `@username Название канала`", parse_mode='Markdown')
            else:
                await update.message.reply_text("❌ Username канала должен начинаться с @")
            
            context.user_data['awaiting_channel'] = False
            await show_manage_channels(update, context)
            
        except Exception as e:
            await update.message.reply_text(f"❌ Ошибка: {str(e)}")
            context.user_data['awaiting_channel'] = False

async def check_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Команда для принудительной проверки подписки"""
    if await check_subscriptions(update, context):
        await show_referral_message(update, context)
        await update.message.reply_text("✅ Вы подписаны на все необходимые каналы!")
        await show_main_menu(update, context)
    else:
        await update.message.reply_text("❌ Вы не подписаны на все необходимые каналы!")
        await show_subscription_request(update, context)

async def set_commands(application: Application):
    commands = [
        BotCommand("start", "Запустить бота"),
        BotCommand("check", "Проверить подписку")
    ]
    await application.bot.set_my_commands(commands)

def main():
    if db is None:
        logger.error("Не удалось инициализировать базу данных. Бот не может быть запущен.")
        return
        
    application = Application.builder().token(BOT_TOKEN).build()
    
    # Обработчики команд
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("check", check_command))
    
    # Обработчики кнопок
    application.add_handler(CallbackQueryHandler(button_handler))
    
    # Обработчик текстовых сообщений (для добавления каналов)
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
    
    # Установка команд бота
    application.post_init = set_commands
    
    # Запуск бота
    logger.info("Бот запускается...")
    application.run_polling()

if __name__ == "__main__":
    main()
