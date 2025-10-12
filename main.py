import telebot
from telebot import types
import sqlite3
import time

# --- Настройка ---
# Вставьте сюда токен вашего бота, полученный от BotFather
BOT_TOKEN = "7557745613:AAFTpWsCJ2bZMqD6GDwTynnqA8Nc-mRF1Rs" 

# Список ID администраторов
ADMINS = [6646433980]

# --- Инициализация ---
bot = telebot.TeleBot(BOT_TOKEN)

# --- Вспомогательная функция для работы с БД ---
def init_db():
    conn = sqlite3.connect('bot_data.db')
    cursor = conn.cursor()
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS users (
            user_id INTEGER PRIMARY KEY
        )
    """)
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS channels (
            channel_id TEXT PRIMARY KEY,
            invite_link TEXT
        )
    """)
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS referrals (
            id INTEGER PRIMARY KEY,
            title TEXT,
            url TEXT
        )
    """)
    conn.commit()
    conn.close()

def add_user_to_db(user_id):
    conn = sqlite3.connect('bot_data.db')
    cursor = conn.cursor()
    cursor.execute("INSERT OR IGNORE INTO users (user_id) VALUES (?)", (user_id,))
    conn.commit()
    conn.close()

# --- Вспомогательная функция для проверки подписки ---
def check_subscription(user_id):
    conn = sqlite3.connect('bot_data.db')
    cursor = conn.cursor()
    cursor.execute("SELECT channel_id FROM channels")
    channels = [row[0] for row in cursor.fetchall()]
    conn.close()
    
    # Если в базе данных нет каналов, возвращаем True, чтобы не блокировать доступ
    if not channels:
        return True

    for channel_id in channels:
        try:
            # ИСПРАВЛЕНИЕ: Принудительное преобразование ID канала в число
            member = bot.get_chat_member(chat_id=int(channel_id), user_id=user_id)
            if member.status not in ['member', 'administrator', 'creator']:
                print(f"Пользователь {user_id} не является участником канала {channel_id}.")
                return False
        except Exception as e:
            print(f"Ошибка при проверке подписки для пользователя {user_id} в канале {channel_id}: {e}")
            return False
    return True

# --- Команда /menu ---
@bot.message_handler(commands=['menu'])
def show_menu(message):
    keyboard = types.ReplyKeyboardMarkup(row_width=1, resize_keyboard=True)
    keyboard.add(types.KeyboardButton(text="/admin_panel"))
    keyboard.add(types.KeyboardButton(text="/start"))
    bot.send_message(message.chat.id, "Выберите опцию:", reply_markup=keyboard)

# --- Обработчик команды /start ---
@bot.message_handler(commands=['start'])
def start_handler(message):
    add_user_to_db(message.from_user.id)
    is_subscribed = check_subscription(message.from_user.id)

    if is_subscribed:
        bot.send_message(
            message.chat.id,
            "Спасибо за подписку! ✅\n\n"
            f"Вот ваша ссылка для доступа: https://t.me/+AbcDefGhiJkLmNoPqRs",
            parse_mode='HTML'
        )
    else:
        conn = sqlite3.connect('bot_data.db')
        cursor = conn.cursor()
        cursor.execute("SELECT invite_link FROM channels")
        invite_links = [row[0] for row in cursor.fetchall()]
        cursor.execute("SELECT title, url FROM referrals")
        referrals = cursor.fetchall()
        conn.close()
        
        keyboard = types.InlineKeyboardMarkup()
        
        for i, link in enumerate(invite_links):
            keyboard.add(types.InlineKeyboardButton(text=f"Канал {i+1}", url=link))
        
        if referrals:
            for title, url in referrals:
                keyboard.add(types.InlineKeyboardButton(text=title, url=url))

        keyboard.add(types.InlineKeyboardButton(text="Я подписался, проверить", callback_data="check_channels"))

        bot.send_message(
            message.chat.id,
            "Для доступа к закрытому контенту, пожалуйста, подпишитесь на следующие каналы:",
            reply_markup=keyboard,
            parse_mode='HTML'
        )

# --- Обработчик нажатия на кнопку "Я подписался, проверить" ---
@bot.callback_query_handler(func=lambda call: call.data == "check_channels")
def check_channels_callback(call):
    is_subscribed = check_subscription(call.from_user.id)
    
    if is_subscribed:
        bot.send_message(
            call.message.chat.id,
            "Спасибо за подписку! ✅\n\n"
            f"Вот ваша ссылка для доступа: https://t.me/+AbcDefGhiJkLmNoPqRs",
            parse_mode='HTML'
        )
    else:
        bot.answer_callback_query(call.id, "Вы ещё не подписались на все каналы. Пожалуйста, подпишитесь и нажмите кнопку снова.", show_alert=True)

# --- Админ-панель ---
@bot.message_handler(commands=['admin_panel'], func=lambda message: message.from_user.id in ADMINS)
def admin_panel(message):
    keyboard = types.InlineKeyboardMarkup()
    keyboard.add(types.InlineKeyboardButton(text="Список каналов", callback_data="channels_list"))
    keyboard.add(types.InlineKeyboardButton(text="Добавить канал", callback_data="add_channel"))
    keyboard.add(types.InlineKeyboardButton(text="Удалить канал", callback_data="delete_channel"))
    keyboard.add(types.InlineKeyboardButton(text="Создать рассылку", callback_data="broadcast"))
    keyboard.add(types.InlineKeyboardButton(text="Управление рефералами", callback_data="manage_referrals"))

    bot.send_message(
        message.chat.id,
        "Добро пожаловать в админ-панель!",
        reply_markup=keyboard,
        parse_mode='HTML'
    )

# --- Управление каналами ---
@bot.callback_query_handler(func=lambda call: call.data == "channels_list")
def channels_list(call):
    conn = sqlite3.connect('bot_data.db')
    cursor = conn.cursor()
    cursor.execute("SELECT channel_id, invite_link FROM channels")
    channels = cursor.fetchall()
    conn.close()

    if not channels:
        bot.send_message(call.message.chat.id, "Список каналов пуст.")
        return

    text = "<b>Список обязательных каналов:</b>\n\n"
    for i, (channel_id, invite_link) in enumerate(channels):
        text += f"{i+1}. ID: <code>{channel_id}</code>\n   Ссылка: {invite_link}\n\n"
    
    bot.send_message(call.message.chat.id, text, parse_mode='HTML')

@bot.callback_query_handler(func=lambda call: call.data == "add_channel")
def add_channel_start(call):
    bot.send_message(call.message.chat.id, "Отправьте ID канала и ссылку-приглашение в формате:\n\n<code>-100... | https://t.me/+...</code>", parse_mode='HTML')
    bot.register_next_step_handler(call.message, add_channel_data)

def add_channel_data(message):
    try:
        channel_id, invite_link = message.text.split(" | ", 1)
        conn = sqlite3.connect('bot_data.db')
        cursor = conn.cursor()
        cursor.execute("INSERT OR IGNORE INTO channels (channel_id, invite_link) VALUES (?, ?)", (channel_id, invite_link,))
        conn.commit()
        conn.close()
        bot.send_message(message.chat.id, "✅ Канал успешно добавлен!")
    except ValueError:
        bot.send_message(message.chat.id, "⚠️ Неверный формат. Попробуйте еще раз в формате: -100... | https://t.me/+...")

@bot.callback_query_handler(func=lambda call: call.data == "delete_channel")
def delete_channel_start(call):
    bot.send_message(call.message.chat.id, "Отправьте ID канала, который хотите удалить:")
    bot.register_next_step_handler(call.message, delete_channel_data)

def delete_channel_data(message):
    try:
        channel_id = message.text
        conn = sqlite3.connect('bot_data.db')
        cursor = conn.cursor()
        cursor.execute("DELETE FROM channels WHERE channel_id = ?", (channel_id,))
        conn.commit()
        conn.close()
        bot.send_message(message.chat.id, "✅ Канал успешно удален!")
    except Exception as e:
        bot.send_message(message.chat.id, f"⚠️ Произошла ошибка при удалении канала: {e}")

# --- Рассылка ---
@bot.callback_query_handler(func=lambda call: call.data == "broadcast")
@bot.message_handler(commands=['broadcast'], func=lambda message: message.from_user.id in ADMINS)
def start_broadcast(message):
    bot.send_message(message.chat.id, "Отправьте сообщение для рассылки. Рассылка будет отправлена всем пользователям бота.")
    bot.register_next_step_handler(message, send_broadcast)

def send_broadcast(message):
    conn = sqlite3.connect('bot_data.db')
    cursor = conn.cursor()
    cursor.execute("SELECT user_id FROM users")
    users = [row[0] for row in cursor.fetchall()]
    conn.close()
    
    sent_count = 0
    blocked_count = 0
    for user_id in users:
        try:
            bot.copy_message(chat_id=user_id, from_chat_id=message.chat.id, message_id=message.message_id)
            sent_count += 1
            time.sleep(0.05)
        except telebot.apihelper.ApiTelegramException as e:
            if 'blocked by the user' in str(e):
                blocked_count += 1
                print(f"Пользователь {user_id} заблокировал бота.")
            else:
                print(f"Ошибка при отправке сообщения пользователю {user_id}: {e}")
        except Exception as e:
            print(f"Неизвестная ошибка: {e}")

    bot.send_message(message.chat.id, f"Рассылка завершена!\nОтправлено: {sent_count}\nЗаблокировали: {blocked_count}")

# --- Управление рефералами ---
@bot.callback_query_handler(func=lambda call: call.data == "manage_referrals")
@bot.message_handler(commands=['manage_referrals'], func=lambda message: message.from_user.id in ADMINS)
def manage_referrals(message):
    conn = sqlite3.connect('bot_data.db')
    cursor = conn.cursor()
    cursor.execute("SELECT id, title FROM referrals")
    referrals = cursor.fetchall()
    conn.close()

    keyboard = types.InlineKeyboardMarkup()
    if referrals:
        for ref_id, title in referrals:
            keyboard.add(types.InlineKeyboardButton(text=f"🗑️ {title}", callback_data=f"del_ref:{ref_id}"))
    
    keyboard.add(types.InlineKeyboardButton(text="➕ Добавить новую рефералку", callback_data="add_referral"))

    bot.send_message(
        message.chat.id,
        "<b>Управление реферальными кнопками:</b>\n\nНажмите на кнопку, чтобы удалить ее. Нажмите на ➕, чтобы добавить новую.",
        reply_markup=keyboard,
        parse_mode='HTML'
    )

@bot.callback_query_handler(func=lambda call: call.data.startswith("del_ref:"))
def delete_referral(call):
    ref_id = int(call.data.split(":")[1])
    conn = sqlite3.connect('bot_data.db')
    cursor = conn.cursor()
    cursor.execute("DELETE FROM referrals WHERE id = ?", (ref_id,))
    conn.commit()
    conn.close()
    bot.answer_callback_query(call.id, "Рефералка удалена!")
    manage_referrals(call.message)

@bot.callback_query_handler(func=lambda call: call.data == "add_referral")
def add_referral_start(call):
    bot.send_message(
        call.message.chat.id,
        "Отправьте название и ссылку реферальной кнопки в формате:\\n\\n<code>Название | ссылка</code>\\n\\nНапример:\\n<code>Канал 1 | https://t.me/channel_1</code>",
        parse_mode='HTML'
    )
    bot.register_next_step_handler(call.message, add_referral_data)

def add_referral_data(message):
    try:
        title, url = message.text.split(" | ", 1)
        conn = sqlite3.connect('bot_data.db')
        cursor = conn.cursor()
        cursor.execute("INSERT INTO referrals (title, url) VALUES (?, ?)", (title, url,))
        conn.commit()
        conn.close()
        bot.send_message(message.chat.id, "✅ Новая реферальная кнопка успешно добавлена!")
    except ValueError:
        bot.send_message(message.chat.id, "⚠️ Неверный формат. Попробуйте еще раз в формате: Название | ссылка")

# --- Запуск бота ---
if __name__ == "__main__":
    init_db()
    bot.polling(none_stop=True)
