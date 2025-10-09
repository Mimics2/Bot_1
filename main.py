import asyncio
import logging
from aiogram import Bot, Dispatcher, types, F
from aiogram.enums import ParseMode
from aiogram.filters import CommandStart, Command
from aiogram.fsm.storage.memory import MemoryStorage
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup

# Настройка логирования для вывода ошибок
logging.basicConfig(level=logging.INFO)

# Твой токен бота, полученный от BotFather
BOT_TOKEN = "8335870133:AAHWCXOY3USOWT4Y9F8CSOPIHWX5OO33HI8"
# Твой ID администратора
ADMINS = [6646433980]

# ID приватного канала для проверки подписки
# Замени этот ID на реальный ID своего канала.
# Как его узнать: добавь @userinfobot в свой канал, и он покажет ID канала
CHANNEL_ID = -1001234567890

# Инициализация бота и диспетчера
bot = Bot(token=BOT_TOKEN, parse_mode=ParseMode.HTML)
storage = MemoryStorage()
dp = Dispatcher(storage=storage)

# Состояния для конечного автомата (FSM)
class AdminStates(StatesGroup):
    """Состояния для админ-команд"""
    waiting_for_message = State()
    waiting_for_button_text = State()
    waiting_for_button_url = State()

# Переменные для хранения данных
all_users = set()  # Хранилище ID пользователей для рассылки
button_data = {}  # Хранилище для кнопки

# Middleware для проверки на админа
@dp.message(F.from_user.id.in_(ADMINS))
@dp.callback_query(F.from_user.id.in_(ADMINS))
async def admin_only_check(event: types.Message | types.CallbackQuery, next_handler):
    """Пропускает команды, только если пользователь — админ."""
    return await next_handler(event)

# ----------------- Команды для администратора -----------------

@dp.message(Command("send_message"))
async def start_broadcast(message: types.Message, state: FSMContext):
    """Начинает процесс рассылки сообщения."""
    await message.reply("Отправьте сообщение, которое нужно разослать всем пользователям. Для отмены отправьте /cancel")
    await state.set_state(AdminStates.waiting_for_message)

@dp.message(AdminStates.waiting_for_message)
async def process_broadcast_message(message: types.Message, state: FSMContext):
    """Обрабатывает и рассылает сообщение."""
    if message.text == "/cancel":
        await message.reply("Рассылка отменена.")
        await state.clear()
        return

    success_count = 0
    fail_count = 0
    message_content = message.text

    for user_id in all_users:
        try:
            await bot.send_message(user_id, message_content, parse_mode=ParseMode.HTML)
            success_count += 1
            await asyncio.sleep(0.05)  # Задержка для предотвращения лимитов Telegram
        except Exception as e:
            logging.error(f"Не удалось отправить сообщение пользователю {user_id}: {e}")
            fail_count += 1

    await message.reply(f"Рассылка завершена!\n"
                        f"Успешно отправлено: {success_count}\n"
                        f"Не удалось отправить (пользователи заблокировали бота): {fail_count}")
    await state.clear()

@dp.message(Command("set_button"))
async def start_set_button(message: types.Message, state: FSMContext):
    """Начинает процесс создания кнопки."""
    await message.reply("Введите текст, который будет на кнопке.")
    await state.set_state(AdminStates.waiting_for_button_text)

@dp.message(AdminStates.waiting_for_button_text)
async def process_button_text(message: types.Message, state: FSMContext):
    await state.update_data(text=message.text)
    await message.reply("Теперь введите URL-адрес для этой кнопки (например, https://t.me/yours).")
    await state.set_state(AdminStates.waiting_for_button_url)

@dp.message(AdminStates.waiting_for_button_url)
async def process_button_url(message: types.Message, state: FSMContext):
    data = await state.get_data()
    button_data["text"] = data["text"]
    button_data["url"] = message.text
    await message.reply(f"Кнопка '{button_data['text']}' с URL '{button_data['url']}' сохранена.")
    await state.clear()

# ----------------- Команды для всех пользователей -----------------

@dp.message(CommandStart())
async def cmd_start(message: types.Message):
    """Обработчик команды /start для всех пользователей."""
    user_id = message.from_user.id
    all_users.add(user_id)
    
    # Создание кнопки, если она настроена
    reply_markup = None
    if button_data:
        keyboard = types.InlineKeyboardMarkup(inline_keyboard=[
            [types.InlineKeyboardButton(text=button_data["text"], url=button_data["url"])]
        ])
        reply_markup = keyboard

    await message.reply(f"Привет, {message.from_user.first_name}! Я готов помочь.\n"
                        f"Здесь может быть текст, предлагающий подписаться на канал.",
                        reply_markup=reply_markup)

# ----------------- Проверка подписки по заявке -----------------
@dp.message(Command("check"))
async def cmd_check_subscription(message: types.Message):
    """Проверяет подписку пользователя на канал."""
    try:
        chat_member = await bot.get_chat_member(chat_id=CHANNEL_ID, user_id=message.from_user.id)
        if chat_member.status in ['member', 'administrator', 'creator']:
            await message.reply("Спасибо! Ваша подписка на канал подтверждена. Заявка принята.")
        else:
            await message.reply("Вы еще не подписались на наш канал. Пожалуйста, сначала подпишитесь, а затем попробуйте снова.")
    except Exception as e:
        await message.reply(f"Произошла ошибка при проверке. Пожалуйста, попробуйте позже.")
        logging.error(f"Ошибка при проверке подписки: {e}")

# Запуск бота
async def main():
    try:
        await dp.start_polling(bot)
    finally:
        await bot.session.close()

if __name__ == "__main__":
    asyncio.run(main())
