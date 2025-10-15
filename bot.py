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
                    joined_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            ''')
            
            # Таблица каналов для проверки подписки (и публичные, и приватные)
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS subscription_channels (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    channel_username TEXT,
                    channel_url TEXT,
                    channel_name TEXT,
                    channel_type TEXT DEFAULT 'public', -- 'public' или 'private'
                    added_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            ''')
            
            # Таблица каналов с рефералками (каналы для выдачи после проверки)
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS referral_channels (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    channel_url TEXT NOT NULL,
                    channel_name TEXT,
                    added_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP
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

    # Методы для каналов подписки (публичные и приватные)
    def add_subscription_channel(self, channel_username, channel_url, channel_name, channel_type='public'):
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            cursor.execute('''
                INSERT OR REPLACE INTO subscription_channels 
                (channel_username, channel_url, channel_name, channel_type)
                VALUES (?, ?, ?, ?)
            ''', (channel_username, channel_url, channel_name, channel_type))
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

    # Методы для каналов с рефералками (каналы для выдачи после проверки)
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
        await update.message.reply_text("🚫 Сервис временно недоступен")
        return
        
    user = update.effective_user
    
    # Добавление пользователя в базу
    db.add_user(
        user_id=user.id,
        username=user.username,
        full_name=user.full_name
    )

    # Проверка подписки на каналы
    subscription_status = await check_subscriptions(update, context)
    
    if subscription_status["all_subscribed"]:
        await show_success_message(update, context)
    else:
        await show_subscription_request(update, context, subscription_status["missing_channels"])

async def check_subscriptions(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    bot = context.bot
    channels = db.get_subscription_channels()
    
    result = {
        "all_subscribed": True,
        "missing_channels": []
    }
    
    if not channels:
        # Если каналов для подписки нет, пропускаем проверку
        return result
    
    for channel in channels:
        channel_id, channel_username, channel_url, channel_name, channel_type, _ = channel
        
        if channel_type == 'public':
            # Проверка подписки на публичные каналы
            try:
                # Убираем @ если есть
                clean_username = channel_username.lstrip('@')
                
                chat_member = await bot.get_chat_member(
                    chat_id=f"@{clean_username}",
                    user_id=user.id
                )
                subscribed = chat_member.status in ['member', 'administrator', 'creator']
                
                if not subscribed:
                    result["all_subscribed"] = False
                    result["missing_channels"].append({
                        "name": channel_name,
                        "type": "public",
                        "url": f"https://t.me/{clean_username}"
                    })
                    
            except Exception as e:
                logger.error(f"Ошибка проверки подписки на {channel_username}: {e}")
                result["all_subscribed"] = False
                result["missing_channels"].append({
                    "name": channel_name,
                    "type": "public",
                    "url": f"https://t.me/{clean_username}"
                })
        
        elif channel_type == 'private':
            # Для приватных каналов мы не можем проверить подписку автоматически
            # Считаем, что пользователь не подписан (нужно будет вручную подтвердить)
            result["all_subscribed"] = False
            result["missing_channels"].append({
                "name": channel_name,
                "type": "private",
                "url": channel_url
            })
    
    return result

async def show_success_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    referral_channels = db.get_referral_channels()
    
    if not referral_channels:
        message = "✨ Отлично! Вы подписаны на все каналы"
        if update.callback_query:
            await update.callback_query.edit_message_text(message)
        else:
            await update.message.reply_text(message)
        return
    
    # Получаем первую реферальную ссылку
    channel = referral_channels[0]
    channel_id, channel_url, channel_name, _ = channel
    
    text = f"""
🎉 **Доступ открыт!**

💎 **Ваша ссылка:**
{channel_url}

⚡ Нажмите на кнопку ниже, чтобы перейти
    """
    
    keyboard = [
        [InlineKeyboardButton(f"🚀 Перейти в {channel_name}", url=channel_url)],
        [InlineKeyboardButton("🔄 Проверить подписку", callback_data="check_subs")]
    ]
    
    if update.effective_user.id == ADMIN_ID:
        keyboard.append([InlineKeyboardButton("⚙️ Панель управления", callback_data="admin_panel")])
    
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    if update.callback_query:
        await update.callback_query.edit_message_text(text, reply_markup=reply_markup, parse_mode='Markdown')
    else:
        await update.message.reply_text(text, reply_markup=reply_markup, parse_mode='Markdown')

async def show_subscription_request(update: Update, context: ContextTypes.DEFAULT_TYPE, missing_channels=None):
    channels = db.get_subscription_channels()
    
    if not channels:
        # Если нет каналов для подписки, сразу показываем успешное сообщение
        await show_success_message(update, context)
        return
    
    keyboard = []
    
    # Создаем кнопки для каждого канала
    for channel_info in missing_channels:
        if channel_info["type"] == "public":
            keyboard.append([
                InlineKeyboardButton(
                    f"📺 Подписаться на {channel_info['name']}",
                    url=channel_info["url"]
                )
            ])
        elif channel_info["type"] == "private":
            keyboard.append([
                InlineKeyboardButton(
                    f"🔗 Перейти в {channel_info['name']}",
                    url=channel_info["url"]
                )
            ])
    
    keyboard.append([InlineKeyboardButton("✅ Я подписался", callback_data="check_subs")])
    
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    if missing_channels:
        public_channels = [ch["name"] for ch in missing_channels if ch["type"] == "public"]
        private_channels = [ch["name"] for ch in missing_channels if ch["type"] == "private"]
        
        text = "📋 **Для получения доступа необходимо:**\n\n"
        
        if public_channels:
            text += f"• Подписаться на каналы: **{', '.join(public_channels)}**\n"
        
        if private_channels:
            text += f"• Присоединиться к каналам: **{', '.join(private_channels)}**\n"
        
        text += "\n👇 Нажмите на кнопки ниже"
    else:
        text = "📋 Для получения доступа необходимо подписаться на каналы:"
    
    if update.callback_query:
        await update.callback_query.edit_message_text(text, reply_markup=reply_markup, parse_mode='Markdown')
    else:
        await update.message.reply_text(text, reply_markup=reply_markup, parse_mode='Markdown')

async def button_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    
    user = update.effective_user
    
    if query.data == "check_subs":
        # Обновляем статус пользователя в базе
        db.add_user(
            user_id=user.id,
            username=user.username,
            full_name=user.full_name
        )
        
        subscription_status = await check_subscriptions(update, context)
        
        if subscription_status["all_subscribed"]:
            await show_success_message(update, context)
        else:
            await show_subscription_request(update, context, subscription_status["missing_channels"])
    
    elif query.data == "admin_panel":
        if update.effective_user.id == ADMIN_ID:
            await show_admin_panel(update, context)

    elif query.data == "manage_subscription_channels":
        if update.effective_user.id == ADMIN_ID:
            await show_manage_subscription_channels(update, context)

    elif query.data == "manage_referral_channels":
        if update.effective_user.id == ADMIN_ID:
            await show_manage_referral_channels(update, context)

    elif query.data == "add_public_channel":
        if update.effective_user.id == ADMIN_ID:
            context.user_data['awaiting_channel'] = True
            context.user_data['channel_type'] = 'public'
            await query.edit_message_text(
                "➕ **Добавить публичный канал**\n\n"
                "Введите в формате:\n"
                "`@username Название`\n\n"
                "**Пример:**\n"
                "`@my_channel Мой канал`",
                parse_mode='Markdown'
            )

    elif query.data == "add_private_channel":
        if update.effective_user.id == ADMIN_ID:
            context.user_data['awaiting_channel'] = True
            context.user_data['channel_type'] = 'private'
            await query.edit_message_text(
                "➕ **Добавить канал по ссылке**\n\n"
                "Введите в формате:\n"
                "`ссылка Название`\n\n"
                "**Пример:**\n"
                "`https://t.me/my_channel Мой канал`",
                parse_mode='Markdown'
            )

    elif query.data == "add_referral_channel":
        if update.effective_user.id == ADMIN_ID:
            context.user_data['awaiting_channel'] = True
            context.user_data['channel_type'] = 'referral'
            await query.edit_message_text(
                "💎 **Добавить финальный канал**\n\n"
                "Введите в формате:\n"
                "`ссылка Название`\n\n"
                "**Пример:**\n"
                "`https://t.me/final_channel Основной канал`",
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
                await query.edit_message_text(f"✅ Канал {channel[3]} удален!")
            else:
                await query.edit_message_text("❌ Ошибка при удалении!")
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
                await query.edit_message_text("❌ Ошибка при удалении!")
            await show_manage_referral_channels(update, context)

    elif query.data == "back_to_admin":
        if update.effective_user.id == ADMIN_ID:
            await show_admin_panel(update, context)

    elif query.data == "back_to_main":
        await show_success_message(update, context)

async def show_admin_panel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if db is None:
        await update.callback_query.edit_message_text("❌ База данных недоступна")
        return
        
    total_users = len(db.get_all_users())
    subscription_channels = db.get_subscription_channels()
    referral_channels = db.get_referral_channels()
    
    public_count = len([ch for ch in subscription_channels if ch[4] == 'public'])
    private_count = len([ch for ch in subscription_channels if ch[4] == 'private'])
    
    text = f"""
⚙️ **Панель управления**

📊 **Статистика:**
• 👥 Пользователей: {total_users}
• 📺 Каналов для проверки: {len(subscription_channels)}
  ├ Публичные: {public_count}
  └ По ссылке: {private_count}
• 💎 Финальных каналов: {len(referral_channels)}

**Доступные действия:**
    """
    
    keyboard = [
        [InlineKeyboardButton("📺 Управление каналами для проверки", callback_data="manage_subscription_channels")],
        [InlineKeyboardButton("💎 Управление финальными каналами", callback_data="manage_referral_channels")],
        [InlineKeyboardButton("◀️ Назад", callback_data="back_to_main")]
    ]
    
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    if update.callback_query:
        await update.callback_query.edit_message_text(text, reply_markup=reply_markup, parse_mode='Markdown')
    else:
        await update.message.reply_text(text, reply_markup=reply_markup, parse_mode='Markdown')

async def show_manage_subscription_channels(update: Update, context: ContextTypes.DEFAULT_TYPE):
    channels = db.get_subscription_channels()
    
    text = "📺 **Каналы для проверки подписки:**\n\n"
    
    if channels:
        for channel in channels:
            channel_id, channel_username, channel_url, channel_name, channel_type, _ = channel
            if channel_type == 'public':
                text += f"• 📹 {channel_name} (@{channel_username})\n"
            else:
                text += f"• 🔗 {channel_name}\n"
    else:
        text += "ℹ️ Нет добавленных каналов\n"
    
    keyboard = [
        [InlineKeyboardButton("➕ Публичный канал", callback_data="add_public_channel")],
        [InlineKeyboardButton("➕ Канал по ссылке", callback_data="add_private_channel")]
    ]
    
    # Кнопки удаления для каждого канала
    for channel in channels:
        channel_id, channel_username, channel_url, channel_name, channel_type, _ = channel
        keyboard.append([
            InlineKeyboardButton(f"🗑️ Удалить {channel_name}", callback_data=f"delete_subscription_channel_{channel[0]}")
        ])
    
    keyboard.append([InlineKeyboardButton("◀️ Назад", callback_data="admin_panel")])
    
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    if update.callback_query:
        await update.callback_query.edit_message_text(text, reply_markup=reply_markup, parse_mode='Markdown')
    else:
        await update.message.reply_text(text, reply_markup=reply_markup, parse_mode='Markdown')

async def show_manage_referral_channels(update: Update, context: ContextTypes.DEFAULT_TYPE):
    channels = db.get_referral_channels()
    
    text = "💎 **Финальные каналы (после проверки):**\n\n"
    
    if channels:
        for channel in channels:
            text += f"• {channel[2]}\n"
    else:
        text += "ℹ️ Нет добавленных каналов\n"
    
    keyboard = [
        [InlineKeyboardButton("➕ Добавить финальный канал", callback_data="add_referral_channel")]
    ]
    
    # Кнопки удаления для каждого канала
    for channel in channels:
        keyboard.append([
            InlineKeyboardButton(f"🗑️ Удалить {channel[2]}", callback_data=f"delete_referral_channel_{channel[0]}")
        ])
    
    keyboard.append([InlineKeyboardButton("◀️ Назад", callback_data="admin_panel")])
    
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    if update.callback_query:
        await update.callback_query.edit_message_text(text, reply_markup=reply_markup, parse_mode='Markdown')
    else:
        await update.message.reply_text(text, reply_markup=reply_markup, parse_mode='Markdown')

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != ADMIN_ID:
        return
        
    if context.user_data.get('awaiting_channel'):
        channel_type = context.user_data.get('channel_type')
        
        try:
            text = update.message.text.strip()
            
            if channel_type == 'public':
                # Формат для публичных каналов: @username Название
                if text.startswith('@'):
                    parts = text.split(' ', 1)
                    if len(parts) == 2:
                        channel_username = parts[0]
                        channel_name = parts[1]
                        
                        if db.add_subscription_channel(channel_username, f"https://t.me/{channel_username.lstrip('@')}", channel_name, 'public'):
                            await update.message.reply_text(f"✅ Канал {channel_name} добавлен!")
                        else:
                            await update.message.reply_text("❌ Ошибка при добавлении!")
                    else:
                        await update.message.reply_text("❌ Неверный формат! Используйте: `@username Название`", parse_mode='Markdown')
                else:
                    await update.message.reply_text("❌ Username должен начинаться с @")
                
                context.user_data['awaiting_channel'] = False
                await show_manage_subscription_channels(update, context)
                
            elif channel_type == 'private':
                # Формат для каналов по ссылке: ссылка Название
                parts = text.split(' ', 1)
                if len(parts) == 2:
                    channel_url = parts[0]
                    channel_name = parts[1]
                    
                    # Проверяем, что ссылка валидная
                    if channel_url.startswith('http://') or channel_url.startswith('https://') or channel_url.startswith('t.me/'):
                        if db.add_subscription_channel(None, channel_url, channel_name, 'private'):
                            await update.message.reply_text(f"✅ Канал {channel_name} добавлен!")
                        else:
                            await update.message.reply_text("❌ Ошибка при добавлении!")
                    else:
                        await update.message.reply_text("❌ Ссылка должна начинаться с http://, https:// или t.me/")
                else:
                    await update.message.reply_text("❌ Неверный формат! Используйте: `ссылка Название`")
                
                context.user_data['awaiting_channel'] = False
                await show_manage_subscription_channels(update, context)
                
            elif channel_type == 'referral':
                # Формат для финальных каналов: ссылка Название
                parts = text.split(' ', 1)
                if len(parts) == 2:
                    channel_url = parts[0]
                    channel_name = parts[1]
                    
                    # Проверяем, что ссылка валидная
                    if channel_url.startswith('http://') or channel_url.startswith('https://') or channel_url.startswith('t.me/'):
                        if db.add_referral_channel(channel_url, channel_name):
                            await update.message.reply_text(f"✅ Финальный канал {channel_name} добавлен!")
                        else:
                            await update.message.reply_text("❌ Ошибка при добавлении!")
                    else:
                        await update.message.reply_text("❌ Ссылка должна начинаться с http://, https:// или t.me/")
                else:
                    await update.message.reply_text("❌ Неверный формат! Используйте: `ссылка Название`")
                
                context.user_data['awaiting_channel'] = False
                await show_manage_referral_channels(update, context)
            
        except Exception as e:
            await update.message.reply_text(f"❌ Ошибка: {str(e)}")
            context.user_data['awaiting_channel'] = False

async def check_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Команда для принудительной проверки подписки"""
    subscription_status = await check_subscriptions(update, context)
    
    if subscription_status["all_subscribed"]:
        await show_success_message(update, context)
    else:
        await update.message.reply_text("❌ Вы не подписаны на все необходимые каналы!")
        await show_subscription_request(update, context, subscription_status["missing_channels"])

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
