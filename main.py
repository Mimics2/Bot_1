import asyncio
from aiogram import Bot, Dispatcher, types, F
from aiogram.enums import ChatMemberStatus, ParseMode
from aiogram.exceptions import TelegramBadRequest, TelegramForbiddenError
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
import sqlite3

# --- Настройка ---
# Вставьте сюда токен вашего бота, полученный от BotFather
BOT_TOKEN = "8335870133:AAHwcXoy3usOWT4Y9F8cSOPiHwX5OO33hI8" 

# Список ID каналов, на которые нужно проверить подписку
CHANNELS = [-1002910637134 # ID первого канала
]

# Ссылка-приглашение в ваш приватный канал или ссылку на ресурс
ACCESS_LINK = ""

# Список ID администраторов
ADMINS = [6646433980]  # ЗАМЕНИТЕ на свои ID!

# --- Состояния для FSM (Finite State Machine) ---
class BroadcastState(StatesGroup):
    waiting_for_message = State()

class ReferralState(StatesGroup):
    waiting_for_referral_data = State()

# --- Инициализация ---
bot = Bot(token=BOT_TOKEN, parse_mode=ParseMode.HTML)
dp = Dispatcher()

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
async def check_subscription(user_id: int):
    for channel_id in CHANNELS:
        try:
            member = await bot.get_chat_member(chat_id=channel_id, user_id=user_id)
            if member.status not in [ChatMemberStatus.MEMBER, ChatMemberStatus.ADMINISTRATOR, ChatMemberStatus.OWNER]:
                return False
        except TelegramBadRequest:
            print(f"Ошибка: Не могу получить информацию о пользователе в канале {channel_id}.")
            return False
    return True

# --- Обработчик команды /start ---
@dp.message(commands=["start"])
async def start_handler(message: types.Message):
    add_user_to_db(message.from_user.id)
    is_subscribed = await check_subscription(message.from_user.id)

    if is_subscribed:
        await message.answer(
            "Спасибо за подписку! ✅\n\n"
            f"Вот ваша ссылка для доступа: {ACCESS_LINK}"
        )
    else:
        conn = sqlite3.connect('bot_data.db')
        cursor = conn.cursor()
        cursor.execute("SELECT title, url FROM referrals")
        referrals = cursor.fetchall()
        conn.close()
        
        keyboard_buttons = []
        if referrals:
            for title, url in referrals:
                keyboard_buttons.append([types.InlineKeyboardButton(text=title, url=url)])

        keyboard_buttons.append([types.InlineKeyboardButton(text="Я подписался, проверить", callback_data="check_channels")])
        keyboard = types.InlineKeyboardMarkup(inline_keyboard=keyboard_buttons)

        await message.answer(
            "Для доступа к закрытому контенту, пожалуйста, подпишитесь на следующие каналы:",
            reply_markup=keyboard
        )

# --- Обработчик нажатия на кнопку "Я подписался, проверить" ---
@dp.callback_query(F.data == "check_channels")
async def check_channels_callback(callback_query: types.CallbackQuery):
    is_subscribed = await check_subscription(callback_query.from_user.id)
    
    if is_subscribed:
        await callback_query.message.edit_text(
            "Спасибо за подписку! ✅\n\n"
            f"Вот ваша ссылка для доступа: {ACCESS_LINK}"
        )
    else:
        await callback_query.answer("Вы ещё не подписались на все каналы. Пожалуйста, подпишитесь и нажмите кнопку снова.", show_alert=True)

# --- Админ-панель ---
@dp.message(F.from_user.id.in_(ADMINS), commands=["admin_panel"])
async def admin_panel(message: types.Message):
    keyboard = types.InlineKeyboardMarkup(
        inline_keyboard=[
            [types.InlineKeyboardButton(text="Создать рассылку", callback_data="broadcast")],
            [types.InlineKeyboardButton(text="Управление рефералами", callback_data="manage_referrals")]
        ]
    )
    await message.answer("Добро пожаловать в админ-панель!", reply_markup=keyboard)

# --- Рассылка ---
@dp.callback_query(F.data == "broadcast")
@dp.message(F.from_user.id.in_(ADMINS), commands=["broadcast"])
async def start_broadcast(message: types.Message, state: FSMContext):
    await message.answer("Отправьте сообщение для рассылки. Рассылка будет отправлена всем пользователям бота.")
    await state.set_state(BroadcastState.waiting_for_message)

@dp.message(BroadcastState.waiting_for_message, F.from_user.id.in_(ADMINS))
async def send_broadcast(message: types.Message, state: FSMContext):
    await state.clear()
    conn = sqlite3.connect('bot_data.db')
    cursor = conn.cursor()
    cursor.execute("SELECT user_id FROM users")
    users = [row[0] for row in cursor.fetchall()]
    conn.close()
    
    sent_count = 0
    blocked_count = 0
    for user_id in users:
        try:
            await bot.copy_message(chat_id=user_id, from_chat_id=message.chat.id, message_id=message.message_id)
            sent_count += 1
            await asyncio.sleep(0.05) # Задержка для предотвращения лимитов Telegram
        except TelegramForbiddenError:
            blocked_count += 1
            print(f"Пользователь {user_id} заблокировал бота.")
        except Exception as e:
            print(f"Ошибка при отправке сообщения пользователю {user_id}: {e}")

    await message.answer(f"Рассылка завершена!\nОтправлено: {sent_count}\nЗаблокировали: {blocked_count}")

# --- Управление рефералами ---
@dp.callback_query(F.data == "manage_referrals")
@dp.message(F.from_user.id.in_(ADMINS), commands=["manage_referrals"])
async def manage_referrals(message: types.Message):
    conn = sqlite3.connect('bot_data.db')
    cursor = conn.cursor()
    cursor.execute("SELECT id, title, url FROM referrals")
    referrals = cursor.fetchall()
    conn.close()

    keyboard_buttons = []
    if referrals:
        for ref_id, title, url in referrals:
            keyboard_buttons.append([types.InlineKeyboardButton(text=f"🗑️ {title}", callback_data=f"del_ref:{ref_id}")])
    
    keyboard_buttons.append([types.InlineKeyboardButton(text="➕ Добавить новую рефералку", callback_data="add_referral")])
    keyboard = types.InlineKeyboardMarkup(inline_keyboard=keyboard_buttons)

    await message.answer("<b>Управление реферальными кнопками:</b>\n\nНажмите на кнопку, чтобы удалить ее. Нажмите на ➕, чтобы добавить новую.", reply_markup=keyboard)

@dp.callback_query(F.data.startswith("del_ref:"))
async def delete_referral(callback_query: types.CallbackQuery):
    ref_id = int(callback_query.data.split(":")[1])
    conn = sqlite3.connect('bot_data.db')
    cursor = conn.cursor()
    cursor.execute("DELETE FROM referrals WHERE id = ?", (ref_id,))
    conn.commit()
    conn.close()
    await callback_query.answer("Рефералка удалена!", show_alert=True)
    await manage_referrals(callback_query.message)

@dp.callback_query(F.data == "add_referral")
async def add_referral_start(callback_query: types.CallbackQuery, state: FSMContext):
    await callback_query.message.answer("Отправьте название и ссылку реферальной кнопки в формате:\n\n<code>Название | ссылка</code>\n\nНапример:\n<code>Канал 1 | https://t.me/channel_1</code>", parse_mode=ParseMode.HTML)
    await state.set_state(ReferralState.waiting_for_referral_data)

@dp.message(ReferralState.waiting_for_referral_data)
async def add_referral_data(message: types.Message, state: FSMContext):
    await state.clear()
    try:
        title, url = message.text.split(" | ", 1)
        conn = sqlite3.connect('bot_data.db')
        cursor = conn.cursor()
        cursor.execute("INSERT INTO referrals (title, url) VALUES (?, ?)", (title, url,))
        conn.commit()
        conn.close()
        await message.answer("✅ Новая реферальная кнопка успешно добавлена!")
    except ValueError:
        await message.answer("⚠️ Неверный формат. Попробуйте еще раз в формате: Название | ссылка")

# --- Запуск бота ---
async def main():
    init_db()
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
