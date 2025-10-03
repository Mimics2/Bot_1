# handlers.py

from telegram import Update, ReplyKeyboardMarkup, ReplyKeyboardRemove
from telegram.ext import ContextTypes, ConversationHandler
# Импортируем ВСЕ константы, включая клавиатуры
from config import * from ai_service import MASTER_PROMPT, call_gemini_api
from payment_service import check_access, handle_access_code 


# --- КЛАВИАТУРЫ ---
# 🔥 ЭТОТ БЛОК УДАЛЕН. КЛАВИАТУРЫ ИМПОРТИРУЮТСЯ ИЗ config.py

# ... (остальные функции choose_action, start и т.д. остаются как в предыдущем ответе)
