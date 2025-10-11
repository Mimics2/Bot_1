import telebot
from telebot import types
import sqlite3
import time

# --- Настройка ---
# Вставьте сюда токен вашего бота, полученный от BotFather
BOT_TOKEN = "8335870133:AAElDxFGCpn55PY8of1oSkAOEq8KsYFfdqM" 

# Список ID каналов для проверки подписки
# ВАЖНО: ID каналов начинаются с '-100'
CHANNELS = [
    -1003185824824  # ID второго канала
    # Добавьте столько каналов, сколько вам нужно
]

# Ссылки-приглашения для каждого канала
# ВАЖНО: Должен быть такой же порядок, как в списке CHANNELS
INVITE_LINKS = [
    https://t.me/+1FcsEhNqTnAxMWVi   # Ссылка-приглашение для второго канала
    # Добавьте ссылки для остальных каналов
]

# Ссылка-приглашение в ваш приватный канал или ссылку на ресурс
ACCESS_LINK = "https://t.me/+AbcDefGhiJkLmNoPqRs"

# Список ID администраторов
ADMINS = [6646433980]  # ЗАМЕНИТЕ на свои ID!

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
    for channel_id in CHANNELS:
        try:
            member = bot.get_chat_member(chat_id=channel_id, user_id=user_id)
            if member.status not in ['member', 'administrator', 'creator']:
                return False
        except Exception as e:
            print(f"Ошибка при проверке подписки: {e}")
            return False
    return True

# --- Обработчик команды /start ---
@bot.message_handler(commands=['start'])
def start_handler(message):
    add_user_to_db(message.from_user.id)
    is_subscribed = check_subscription(message.from_user.id)

    if is_subscribed:
        bot.send_message(
            message.chat.id,
            "Спасибо за подписку! ✅\n\n"
            f"Вот ваша ссылка для доступа: {ACCESS_LINK}",
            parse_mode='HTML'
        )
    else:
        conn = sqlite3.connect('bot_data.db')
        cursor = conn.cursor()
        cursor.execute("SELECT title, url FROM referrals")
        referrals = cursor.fetchall()
        conn.close()
        
        keyboard = types.InlineKeyboardMarkup()
        
        # ИСПРАВЛЕНИЕ: Используем INVITE_LINKS для кнопок каналов
        for i, link in enumerate(INVITE_LINKS):
            keyboard.add(types.InlineKeyboardButton(text=f"Канал {i+1}", url=link))
        
        # Добавляем реферальные кнопки
        if referrals:
            for title, url in referrals:
                keyboard.add(types.InlineKeyboardButton(text=title, url=url))

        # Добавляем кнопку "Проверить подписку"
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
        bot.edit_message_text(
            chat_id=call.message.chat.id,
            message_id=call.message.message_id,
            text="Спасибо за подписку! ✅\n\n"
            f"Вот ваша ссылка для доступа: {ACCESS_LINK}",
            parse_mode='HTML'
        )
    else:
        bot.answer_callback_query(call.id, "Вы ещё не подписались на все каналы. Пожалуйста, подпишитесь и нажмите кнопку снова.", show_alert=True)

# --- Админ-панель ---
@bot.message_handler(commands=['admin_panel'], func=lambda message: message.from_user.id in ADMINS)
def admin_panel(message):
    keyboard = types.InlineKeyboardMarkup()
    keyboard.add(types.InlineKeyboardButton(text="Создать рассылку", callback_data="broadcast"))
    keyboard.add(types.InlineKeyboardButton(text="Управление рефералами", callback_data="manage_referrals"))

    bot.send_message(
        message.chat.id,
        "Добро пожаловать в админ-панель!",
        reply_markup=keyboard,
        parse_mode='HTML'
    )

# --- Рассылка ---
@bot.callback_query_handler(func=lambda call: call.data == "broadcast")
def start_broadcast(call):
    bot.send_message(
        call.message.chat.id,
        "Отправьте сообщение для рассылки. Рассылка будет отправлена всем пользователям бота."
    )
    # Используем register_next_step_handler для получения следующего сообщения
    bot.register_next_step_handler(call.message, send_broadcast)

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
            time.sleep(0.05) # Задержка для предотвращения лимитов Telegram
        except telebot.apihelper.ApiTelegramException as e:
            if 'blocked by the user' in str(e):
                blocked_count += 1
                print(f"Пользователь {user_id} заблокировал бота.")
            else:
                print(f"Ошибка при отправке сообщения пользователю {user_id}: {e}")
        except Exception as e:
            print(f"Неизвестная ошибка: {e}")

    bot.send_message(
        message.chat.id,
        f"Рассылка завершена!\nОтправлено: {sent_count}\nЗаблокировали: {blocked_count}"
    )

# --- Управление рефералами ---
@bot.callback_query_handler(func=lambda call: call.data == "manage_referrals")
def manage_referrals(call):
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
        call.message.chat.id,
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
    manage_referrals(call)

@bot.callback_query_handler(func=lambda call: call.data == "add_referral")
def add_referral_start(call):
    bot.send_message(
        call.message.chat.id,
        "Отправьте название и ссылку реферальной кнопки в формате:\n\n<code>Название | ссылка</code>\n\nНапример:\n<code>Канал 1 | https://t.me/channel_1</code>",
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
