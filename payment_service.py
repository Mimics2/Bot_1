# payment_service.py

from telegram import Update
from telegram.ext import ContextTypes
from config import logger, SUBSCRIPTION_PRICE

# --- ВНИМАНИЕ: ЭТО ЗАГЛУШКА ДЛЯ БУДУЩЕЙ ИНТЕГРАЦИИ WELLPAY ---
# В реальном проекте здесь будет обращение к API WellPay 
# для генерации счетов и проверки статуса оплаты.

# Mock-база данных для симуляции подписки (в реальном проекте используйте БД)
MOCK_SUBSCRIPTION_DB = set() 

async def check_access(user_id: int, update: Update, context: ContextTypes.DEFAULT_TYPE) -> bool:
    """Проверяет, оплатил ли пользователь доступ к PRO-функциям."""
    
    # 🚨 ИМИТАЦИЯ: Доступ дается, если ID пользователя есть в "базе"
    if user_id in MOCK_SUBSCRIPTION_DB:
        return True
    
    # 🚨 ИМИТАЦИЯ: Если доступ не оплачен, предлагаем оплатить
    await update.message.reply_text(
        "🔒 **Доступ ограничен.**\n"
        "Для использования PRO-функций CopiBot (Gemini) требуется подписка.\n"
        f"Стоимость: **{SUBSCRIPTION_PRICE} руб.**",
        parse_mode='Markdown'
    )
    # Вызываем функцию для создания счета WellPay (пока это заглушка)
    await create_wellpay_invoice(update, context)
    
    return False

async def create_wellpay_invoice(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    Создает счет через WellPay. 
    Эту функцию нужно будет доработать после получения документации WellPay.
    """
    logger.info(f"Generating WellPay invoice for user {update.effective_user.id}")
    
    # --- ВАШ КОД ИНТЕГРАЦИИ WELLPAY БУДЕТ ЗДЕСЬ ---
    
    # Примерно так это будет выглядеть:
    # 1. Сбор данных (цена, ID пользователя)
    # 2. Вызов API WellPay для получения ссылки на оплату
    # 3. Отправка ссылки пользователю
    
    await update.message.reply_text(
        "🔗 **Нажмите на эту ссылку для оплаты подписки:** [Оплатить через WellPay (заглушка)]"
        "(https://wellpay.example.com/invoice_link)",
        parse_mode='Markdown'
    )
    
    # Имитация получения успешной оплаты (для тестирования)
    # Для теста: /activate_pro
    
async def activate_pro_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Команда для имитации активации PRO-доступа (только для тестирования)."""
    user_id = update.effective_user.id
    MOCK_SUBSCRIPTION_DB.add(user_id)
    await update.message.reply_text(
        "🥳 **PRO-доступ активирован!** Теперь вы можете генерировать посты.",
        parse_mode='Markdown'
    )
