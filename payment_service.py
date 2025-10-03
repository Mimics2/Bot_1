# payment_service.py

from telegram import Update
from telegram.ext import ContextTypes
# Импортируем обе константы: цена и валюта
from config import logger, SUBSCRIPTION_PRICE, SUBSCRIPTION_CURRENCY 

# Mock-база данных для симуляции подписки 
MOCK_SUBSCRIPTION_DB = set() 

async def check_access(user_id: int, update: Update, context: ContextTypes.DEFAULT_TYPE) -> bool:
    """Проверяет, оплатил ли пользователь доступ к PRO-функциям."""
    
    # ИМИТАЦИЯ: Проверка подписки
    if user_id in MOCK_SUBSCRIPTION_DB:
        return True
    
    # Если доступ не оплачен, предлагаем оплатить
    await update.message.reply_text(
        "🔒 **Доступ ограничен.**\n"
        "Для использования PRO-функций CopiBot (Gemini) требуется подписка.\n"
        f"Стоимость: **{SUBSCRIPTION_PRICE} {SUBSCRIPTION_CURRENCY}**", # Используем $1 USD
        parse_mode='Markdown'
    )
    await create_wellpay_invoice(update, context)
    
    return False

async def create_wellpay_invoice(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    ЗАГЛУШКА: Симулирует создание счета WellPay и отправку ссылки.
    """
    logger.info(f"Generating WellPay invoice for user {update.effective_user.id}")
    
    await update.message.reply_text(
        "🔗 **Нажмите на эту ссылку для оплаты подписки:** [Оплатить через WellPay (заглушка)]"
        "(https://wellpay.example.com/invoice_link)",
        parse_mode='Markdown'
    )
    
async def activate_pro_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """КОМАНДА ДЛЯ ТЕСТА: Имитация активации PRO-доступа."""
    user_id = update.effective_user.id
    MOCK_SUBSCRIPTION_DB.add(user_id)
    await update.message.reply_text(
        "🥳 **PRO-доступ активирован!** Теперь вы можете генерировать посты.\n"
        "Нажмите /start, чтобы продолжить.",
        parse_mode='Markdown'
    )
