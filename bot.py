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
            
            # Таблица каналов для проверки подписки (публичные)
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS subscription_channels (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    channel_username TEXT UNIQUE,
                    channel_name TEXT,
                    added_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            ''')
            
            # Таблица каналов с рефералками (приватные)
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS referral_channels (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    channel_url TEXT NOT NULL,
                    channel_name TEXT,
                    added_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            ''')
            
            # Таблица подписок (только для публичных каналов)
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS subscriptions (
                    user_id INTEGER,
                    channel_id INTEGER,
                    subscribed BOOLEAN DEFAULT FALSE,
                    last_check TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    PRIMARY KEY (user_id, channel_id),
                    FOREIGN KEY (channel_id) REFERENCES subscription_channels (id)
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

    # Методы для каналов подписки (публичные)
    def add_subscription_channel(self, channel_username, channel_name):
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            cursor.execute('''
                INSERT OR REPLACE INTO subscription_channels (channel_username, channel_name)
                VALUES (?, ?)
            ''', (channel_username, channel_name))
            conn.commit()
            conn.close()
            return True
        except Exception as e:
            logger.error(f"Ошибка добавления канала для подписки: {e}")
            return False

    def remove_subscription_channel(self, channel_id):
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            cursor.execute('DELETE FROM subscription_channels WHERE id = ?', (channel_id,))
            cursor.execute('DELETE FROM subscriptions WHERE channel_id = ?', (channel_id,))
            conn.commit()
            conn.close()
            return True
        except Exception as e:
            logger.error(f"Ошибка удаления канала для подписки: {e}")
            return False

    def get_subscription_channels(self):
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            cursor.execute('SELECT * FROM subscription_channels ORDER BY id')
            channels = cursor.fetchall()
            conn.close()
            return channels
        except Exception as e:
            logger.error(f"Ошибка получения каналов для подписки: {e}")
            return []

    # Методы для каналов с рефералками (приватные)
    def add_referral_channel(self, channel_url, channel_name):
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            cursor.execute('''
                INSERT OR REPLACE INTO referral_channels (channel_url, channel_name)
                VALUES (?, ?)
            ''', (channel_url, channel_name))
            conn.commit()
            conn.close()
            return True
        except Exception as e:
            logger.error(f"Ошибка добавления канала с рефералкой: {e}")
            return False

    def remove_referral_channel(self, channel_id):
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            cursor.execute('DELETE FROM referral_channels WHERE id = ?', (channel_id,))
            conn.commit()
            conn.close()
            return True
        except Exception as e:
            logger.error(f"Ошибка удаления канала с рефералкой: {e}")
            return False

    def get_referral_channels(self):
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            cursor.execute('SELECT * FROM referral_channels ORDER BY id')
            channels = cursor.fetchall()
            conn.close()
            return channels
        except Exception as e:
            logger.error(f"Ошибка получения каналов с рефералками: {e}")
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

    # Проверка подписки на публичные каналы
    if await check_subscriptions(update, context):
        await show_referral_message(update, context)
        await show_main_menu(update, context)
    else:
        await show_subscription_request(update, context)

async def check_subscriptions(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    bot = context.bot
    channels = db.get_subscription_channels()
    
    if not channels:
        # Если каналов для подписки нет, пропускаем проверку
        return True
    
    all_subscribed = True
    missing_channels = []
    
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
                missing_channels.append(channel_name)
                
        except Exception as e:
            logger.error(f"Ошибка проверки подписки на {channel_username}: {e}")
            all_subscribed = False
            missing_channels.append(channel_name)
    
    if not all_subscribed and missing_channels:
        if update.callback_query:
            await update.callback_query.message.reply_text(
                f"❌ Вы не подписаны на следующие каналы: {', '.join(missing_channels)}"
            )
        else:
            await update.message.reply_text(
                f"❌ Вы не подписаны на следующие каналы: {', '.join(missing_channels)}"
            )
    
    return all_subscribed

async def show_referral_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    
    # Проверяем, показывали ли уже рефералку этому пользователю
    if not db.has_referral_been_shown(user.id):
        referral_channels = db.get_referral_channels()
        
        if not referral_channels:
            await update.message.reply_text("✅ Вы подписаны на все каналы!")
            return
        
        text = """
🎉 Спасибо за подписку! 

🔐 **Присоединяйтесь к нашим приватным каналам:**
Подайте заявку по ссылкам ниже 👇
        """
        
        keyboard = []
        
        for channel in referral_channels:
            channel_id, channel_url, channel_name, _ = channel
            keyboard.append([InlineKeyboardButton(f"🔐 {channel_name}", url=channel_url)])
        
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        if update.callback_query:
            await update.callback_query.message.reply_text(text, reply_markup=reply_markup)
        else:
            await update.message.reply_text(text, reply_markup=reply_markup)
        
        # Помечаем, что рефералка показана
        db.set_referral_shown(user.id)

async def show_subscription_request(update: Update, context: ContextTypes.DEFAULT_TYPE):
    channels = db.get_subscription_channels()
    
    if not channels:
        # Если нет каналов для подписки, сразу показываем рефералки
        await show_referral_message(update, context)
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
    
    text = "📋 Для доступа к приватным каналам необходимо подписаться на наши публичные каналы:"
    
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

    elif query.data == "manage_subscription_channels":
        if update.effective_user.id == ADMIN_ID:
            await show_manage_subscription_channels(update, context)

    elif query.data == "manage_referral_channels":
        if update.effective_user.id == ADMIN_ID:
            await show_manage_referral_channels(update, context)

    elif query.data == "add_subscription_channel":
        if update.effective_user.id == ADMIN_ID:
            context.user_data['awaiting_channel'] = True
            context.user_data['channel_type'] = 'subscription'
            await query.edit_message_text(
                "📝 Введите данные публичного канала для проверки подписки:\n"
                "`@username Название канала`\n\n"
                "Пример:\n"
                "`@my_channel Мой публичный канал`",
                parse_mode='Markdown'
            )

    elif query.data == "add_referral_channel":
        if update.effective_user.id == ADMIN_ID:
            context.user_data['awaiting_channel'] = True
            context.user_data['channel_type'] = 'referral'
            await query.edit_message_text(
                "📝 Введите данные приватного канала с рефералкой:\n"
                "`ссылка Название канала`\n\n"
                "Пример:\n"
                "`https://t.me/private_channel Мой приватный канал`",
                parse_mode='Markdown'
            )

    elif query.data.startswith("delete_subscription_channel_"):
        if update.effective_user.id == ADMIN_ID:
            channel_id = int(query.data.replace("delete_subscription_channel_", ""))
            channel = None
            channels = db.get_subscription_channels()
            for ch in channels:
                if ch[0] == channel_id:
                    channel = ch
                    break
            
            if channel and db.remove_subscription_channel(channel_id):
                await query.edit_message_text(f"✅ Канал {channel[2]} удален!")
            else:
                await query.edit_message_text("❌ Ошибка при удалении канала!")
            await show_manage_subscription_channels(update, context)

    elif query.data.startswith("delete_referral_channel_"):
        if update.effective_user.id == ADMIN_ID:
            channel_id = int(query.data.replace("delete_referral_channel_", ""))
            channel = None
            channels = db.get_referral_channels()
            for ch in channels:
                if ch[0] == channel_id:
                    channel = ch
                    break
            
            if channel and db.remove_referral_channel(channel_id):
                await query.edit_message_text(f"✅ Канал {channel[2]} удален!")
            else:
                await query.edit_message_text("❌ Ошибка при удалении канала!")
            await show_manage_referral_channels(update, context)

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
    subscription_channels = db.get_subscription_channels()
    referral_channels = db.get_referral_channels()
    
    text = f"""
👑 Админ-панель

📊 Статистика:
👥 Всего пользователей: {total_users}
📢 Публичных каналов: {len(subscription_channels)}
🔐 Приватных каналов: {len(referral_channels)}

Доступные действия:
    """
    
    keyboard = [
        [InlineKeyboardButton("📢 Управление публичными каналами", callback_data="manage_subscription_channels")],
        [InlineKeyboardButton("🔐 Управление приватными каналами", callback_data="manage_referral_channels")],
        [InlineKeyboardButton("📊 Статистика пользователей", callback_data="user_stats")],
        [InlineKeyboardButton("◀️ Назад", callback_data="back_to_main")]
    ]
    
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    if update.callback_query:
        await update.callback_query.edit_message_text(text, reply_markup=reply_markup)
    else:
        await update.message.reply_text(text, reply_markup=reply_markup)

async def show_manage_subscription_channels(update: Update, context: ContextTypes.DEFAULT_TYPE):
    channels = db.get_subscription_channels()
    
    text = "📢 Управление публичными каналами (для проверки подписки):\n\n"
    
    if channels:
        for channel in channels:
            text += f"• {channel[2]} (@{channel[1]})\n"
    else:
        text += "ℹ️ Нет добавленных каналов\n"
    
    keyboard = [
        [InlineKeyboardButton("➕ Добавить публичный канал", callback_data="add_subscription_channel")]
    ]
    
    # Кнопки удаления для каждого канала
    for channel in channels:
        keyboard.append([
            InlineKeyboardButton(f"❌ Удалить {channel[2]}", callback_data=f"delete_subscription_channel_{channel[0]}")
        ])
    
    keyboard.append([InlineKeyboardButton("◀️ Назад", callback_data="admin_panel")])
    
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    if update.callback_query:
        await update.callback_query.edit_message_text(text, reply_markup=reply_markup)
    else:
        await update.message.reply_text(text, reply_markup=reply_markup)

async def show_manage_referral_channels(update: Update, context: ContextTypes.DEFAULT_TYPE):
    channels = db.get_referral_channels()
    
    text = "🔐 Управление приватными каналами (реферальные ссылки):\n\n"
    
    if channels:
        for channel in channels:
            text += f"• {channel[2]}: {channel[1]}\n"
    else:
        text += "ℹ️ Нет добавленных каналов\n"
    
    keyboard = [
        [InlineKeyboardButton("➕ Добавить приватный канал", callback_data="add_referral_channel")]
    ]
    
    # Кнопки удаления для каждого канала
    for channel in channels:
        keyboard.append([
            InlineKeyboardButton(f"❌ Удалить {channel[2]}", callback_data=f"delete_referral_channel_{channel[0]}")
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
        channel_type = context.user_data.get('channel_type')
        
        try:
            text = update.message.text.strip()
            
            if channel_type == 'subscription':
                # Формат для публичных каналов: @username Название
                if text.startswith('@'):
                    parts = text.split(' ', 1)
                    if len(parts) == 2:
                        channel_username = parts[0]
                        channel_name = parts[1]
                        
                        if db.add_subscription_channel(channel_username, channel_name):
                            await update.message.reply_text(f"✅ Публичный канал {channel_name} добавлен!")
                        else:
                            await update.message.reply_text("❌ Ошибка при добавлении канала!")
                    else:
                        await update.message.reply_text("❌ Неверный формат! Используйте: `@username Название канала`", parse_mode='Markdown')
                else:
                    await update.message.reply_text("❌ Username канала должен начинаться с @")
                
                context.user_data['awaiting_channel'] = False
                await show_manage_subscription_channels(update, context)
                
            elif channel_type == 'referral':
                # Формат для приватных каналов: ссылка Название
                parts = text.split(' ', 1)
                if len(parts) == 2:
                    channel_url = parts[0]
                    channel_name = parts[1]
                    
                    # Проверяем, что ссылка валидная
                    if channel_url.startswith('http://') or channel_url.startswith('https://') or channel_url.startswith('t.me/'):
                        if db.add_referral_channel(channel_url, channel_name):
                            await update.message.reply_text(f"✅ Приватный канал {channel_name} добавлен!")
                        else:
                            await update.message.reply_text("❌ Ошибка при добавлении канала!")
                    else:
                        await update.message.reply_text("❌ Ссылка должна начинаться с http://, https:// или t.me/")
                else:
                    await update.message.reply_text("❌ Неверный формат! Используйте: `ссылка Название канала`")
                
                context.user_data['awaiting_channel'] = False
                await show_manage_referral_channels(update, context)
            
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
