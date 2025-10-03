import os
import logging
from telegram import Update, ReplyKeyboardMarkup, ReplyKeyboardRemove
from telegram.ext import (
    Application, CommandHandler, MessageHandler, filters, ConversationHandler, ContextTypes
)
from google import genai
from google.genai.errors import APIError

# --- 1. НАСТРОЙКИ И ТОКЕНЫ ---

# 1.1. ТОКЕНЫ (Вставлены предоставленные вами ключи)
TELEGRAM_BOT_TOKEN = '8428976532:AAElfrt3A7y3Q5Paq2-eVY9ACxQXKc9cSZE'
GEMINI_API_KEY = 'AIzaSyBXaEujyx80xYCaZ6ByraBad4hqyJQr6WQ' 

# Устанавливаем уровень логирования
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO
)
logger = logging.getLogger(__name__)

# Состояния диалога (Машина состояний)
(CHOOSING_THEME, CHOOSING_GENRE, GETTING_TOPIC, GETTING_CORRECTION, CHOOSING_ACTION) = range(5)

# --- 2. КЛАВИАТУРЫ (КНОПКИ) ---

# Клавиатура для выбора основного действия
main_keyboard = [
    ["🆕 Начать новый пост", "⚙️ Корректировать предыдущий"],
    ["❌ Отмена"]
]

# Клавиатура для выбора темы поста
theme_keyboard = [
    ["Бизнес", "Технологии", "Путешествия", "Здоровье"],
    ["Личный бренд", "Другая тема", "⬅️ Назад"]
]

# Клавиатура для выбора жанра/стиля
genre_keyboard = [
    ["Информационный (обучение)", "Продающий (AIDA)", "Развлекательный (лайфхак)"],
    ["Сторителлинг (личная история)", "Провокация (хайп)", "⬅️ Назад"]
]

# --- 3. ФУНКЦИИ-ОБРАБОТЧИКИ ---

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Начинает диалог и предлагает выбрать действие."""
    await update.message.reply_text(
        "👋 Добро пожаловать в CopiBot на базе Gemini! Выберите, что будем делать:",
        reply_markup=ReplyKeyboardMarkup(main_keyboard, one_time_keyboard=True, resize_keyboard=True)
    )
    return CHOOSING_ACTION

async def choose_action(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Обрабатывает выбор 'Начать новый пост' или 'Корректировать'."""
    text = update.message.text
    
    if text == "🆕 Начать новый пост":
        await update.message.reply_text(
            "Отлично! Теперь выберите основную тему вашего поста:",
            reply_markup=ReplyKeyboardMarkup(theme_keyboard, one_time_keyboard=True, resize_keyboard=True)
        )
        return CHOOSING_THEME
    
    elif text == "⚙️ Корректировать предыдущий":
        await update.message.reply_text(
            "Пожалуйста, отправьте мне текст, который нужно скорректировать, "
            "и **подробно укажите**, что именно нужно изменить (стиль, тон, грамматика).",
            reply_markup=ReplyKeyboardRemove()
        )
        return GETTING_CORRECTION
    
    await update.message.reply_text("Пожалуйста, выберите действие на клавиатуре.")
    return CHOOSING_ACTION

async def choose_theme(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Обрабатывает выбор темы и просит выбрать жанр."""
    text = update.message.text
    
    if text == "⬅️ Назад":
        return await start(update, context)
    
    context.user_data['theme'] = text
    
    await update.message.reply_text(
        f"Вы выбрали тему: *{text}*.\nТеперь выберите жанр или стиль написания:",
        parse_mode='Markdown',
        reply_markup=ReplyKeyboardMarkup(genre_keyboard, one_time_keyboard=True, resize_keyboard=True)
    )
    return CHOOSING_GENRE

async def choose_genre(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Обрабатывает выбор жанра и просит ввести конкретную подтему."""
    text = update.message.text
    
    if text == "⬅️ Назад":
        # Возвращаемся к выбору темы
        await update.message.reply_text(
            "Выберите основную тему вашего поста:",
            reply_markup=ReplyKeyboardMarkup(theme_keyboard, one_time_keyboard=True, resize_keyboard=True)
        )
        return CHOOSING_THEME 
        
    context.user_data['genre'] = text
    
    await update.message.reply_text(
        f"Вы выбрали жанр: *{text}*.\nТеперь, пожалуйста, введите **конкретную подтему**, основную идею или черновик для поста. "
        "Например: 'Почему фрилансеры боятся повышать чек и как это исправить'.",
        parse_mode='Markdown',
        reply_markup=ReplyKeyboardRemove()
    )
    return GETTING_TOPIC

async def generate_post(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Генерирует пост с помощью Gemini и выводит результат, используя MASTER-ПРОМПТ."""
    
    # 1. Сбор данных пользователя
    user_topic = update.message.text
    theme = context.user_data.get('theme', 'Общая категория')
    genre = context.user_data.get('genre', 'Информационный')
    
    # Пока фиксированные данные. В будущем можно добавить шаги для их ввода.
    audience = "Фрилансеры, работающие из дома, которые ищут мотивацию и продуктивность."
    post_length = "Средний (2-3 абзаца, с маркированными списками)."
    additional_wishes = "Добавить провокационный заголовок, использовать дружелюбный, но экспертный тон и не писать 'и вот почему'."

    # 2. Формирование инструкции для Gemini (Ваш MASTER-ПРОМПТ)
    prompt = f"""
    # MASTER-ПРОМПТ: PRO-КОПИРАЙТЕР 5.1

    ## 1. РОЛЬ И ПРИНЦИПЫ (ROLE & PRINCIPLES)

    Твоя роль — **ТОП-уровневый, креативный копирайтер** для социальных сетей (Instagram, Telegram, VK), который специализируется на вовлекающем и продающем контенте. Твоя ключевая задача — генерировать тексты, которые **невозможно отличить от написанных человеком**.

    ### Ключевые принципы работы:
    1.  **Натуральность:** Строго избегай слов-маркеров ИИ (например: "безусловно", "в заключение", "стоит отметить", "важно подчеркнуть", "и вот почему", "давайте рассмотрим"). Используй короткие, динамичные предложения и активный залог.
    2.  **Эмоциональный крючок:** Всегда начинай пост с мощного, вовлекающего заголовка, который обращается к конкретной **боли, страху или желанию** целевой аудитории.
    3.  **Визуальная динамика:** Используй **много релевантных эмодзи**, размещая их, как правило, в начале предложения или смыслового блока для создания ритма и динамики.
    4.  **Профессиональные модели:** Используй классические копирайтерские структуры (AIDA, PAS, 4U, Storytelling), выбирая наиболее подходящую для задачи.
    5.  **Четкий CTA:** Всегда завершай текст **единственным, недвусмысленным** призывом к действию (подписка, комментарий, переход по ссылке).

    ## 2. АНАЛИТИЧЕСКИЙ ЭТАП (Chain-of-Thought / CoT)

    Перед генерацией ты должен провести внутренний анализ, **используя все предоставленные данные**. Этот анализ **не должен быть виден** в финальном ответе.
    1.  **Главная Цель:** Определи единственную, конечную цель поста.
    2.  **Выбор Структуры:** Выбери оптимальную модель (AIDA, PAS или другую) и кратко обоснуй почему.
    3.  **Ключевой Крючок (Hook):** Сформулируй 2-3 варианта первого предложения, который моментально захватит внимание ЦА.
    4.  **Тон:** Определи эмоциональный тон.

    ## 3. ВХОДНЫЕ ДАННЫЕ ОТ ПОЛЬЗОВАТЕЛЯ (INPUT)

    Ты будешь получать задачу в следующем формате. Используй эти данные для создания поста.

    1.  **Тема/Идея/Черновик (Пользовательский ввод):** {user_topic}
    2.  **Основная Категория (Выбор кнопки):** {theme}
    3.  **Жанр/Стиль (Выбор кнопки):** {genre}
    4.  **Целевая аудитория (ЦА):** {audience}
    5.  **Длина и Стиль:** {post_length}
    6.  **Дополнительные пожелания:** {additional_wishes}

    ## 4. ГЕНЕРАЦИЯ И ХЭШТЕГИ

    На основе внутреннего анализа и входных данных сгенерируй **только один** финальный вариант поста, строго соблюдая все принципы из пункта 1.

    ### Хештеги:
    Сгенерируй **от 6 до 8** релевантных хэштегов, разделенных на две группы для максимального охвата:
    1.  **Широкие (#):** 3-4 общих, высокочастотных тега по основной тематике.
    2.  **Нишевые (##):** 3-4 узкоспециализированных тега, которые точно соответствуют ЦА или продукту.

    ## 5. ФОРМАТ ОТВЕТА (OUTPUT FORMAT)

    **ВНИМАНИЕ:** Твой ответ должен содержать **ТОЛЬКО** финальный текст поста и хэштеги, оформленные строго по шаблону.

    ```
    [ФИНАЛЬНЫЙ ТЕКСТ ПОСТА, ИСПОЛЬЗУЯ МНОГО ЭМОДЗИ И ДИНАМИЧНЫЕ ПРЕДЛОЖЕНИЯ]

    # Широкие_Теги # Общая_Тематика
    ## Нишевый_Тег ## Узкий_Тег
    ```
    """
    
    await update.message.reply_text("✍️ Ваш пост генерируется. Пожалуйста, подождите...")

    try:
        # Инициализируем Gemini Client с вашим ключом
        client = genai.Client(api_key=GEMINI_API_KEY)
        
        response = client.models.generate_content(
            model='gemini-2.5-flash',
            contents=prompt,
        )
        
        # Отправляем готовый пост
        await update.message.reply_text(
            f"✅ **ГОТОВЫЙ ПОСТ ({theme} / {genre})**:\n\n{response.text}",
            parse_mode='Markdown'
        )
        
    except APIError as e:
        logger.error(f"Gemini API Error: {e}")
        await update.message.reply_text(
            "❌ Ошибка API Gemini. Не удалось сгенерировать пост. Проверьте ваш API ключ."
        )
    except Exception as e:
        logger.error(f"General Error: {e}")
        await update.message.reply_text(
            "❌ Произошла общая ошибка при генерации. Попробуйте снова."
        )

    # Завершаем диалог и возвращаемся к началу
    return await start(update, context)

async def correct_post(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Корректирует текст с помощью Gemini."""
    correction_prompt = update.message.text
    
    # Формируем инструкцию для коррекции
    prompt = (
        f"Ты профессиональный редактор и корректор. Твоя задача — выполнить корректировку текста, "
        f"основываясь на запросе пользователя. Запрос и текст для коррекции: '{correction_prompt}'. "
        f"Верни только исправленный и улучшенный текст. Не добавляй никаких пояснений, только результат."
    )
    
    await update.message.reply_text("🔄 Выполняю коррекцию текста...")

    try:
        client = genai.Client(api_key=GEMINI_API_KEY)
        response = client.models.generate_content(
            model='gemini-2.5-flash',
            contents=prompt,
        )
        
        await update.message.reply_text(
            f"✅ **СКОРРЕКТИРОВАННЫЙ ТЕКСТ**:\n\n{response.text}",
            parse_mode='Markdown'
        )
    
    except Exception as e:
        logger.error(f"Correction Error: {e}")
        await update.message.reply_text(
            "❌ Ошибка при коррекции. Попробуйте сформулировать запрос иначе."
        )

    # Завершаем диалог и возвращаемся к началу
    return await start(update, context)

async def cancel(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Отменяет диалог."""
    await update.message.reply_text(
        'Операция отменена. Чем я могу еще помочь?',
        reply_markup=ReplyKeyboardMarkup(main_keyboard, one_time_keyboard=True, resize_keyboard=True)
    )
    context.user_data.clear()
    return CHOOSING_ACTION

# --- 4. ЗАПУСК БОТА ---

def main() -> None:
    """Основная функция для запуска бота."""
    
    application = Application.builder().token(TELEGRAM_BOT_TOKEN).build()

    conv_handler = ConversationHandler(
        entry_points=[CommandHandler("start", start)],
        states={
            CHOOSING_ACTION: [
                MessageHandler(filters.Text(list(zip(*main_keyboard))[0]), choose_action)
            ],
            CHOOSING_THEME: [
                MessageHandler(filters.Text(list(zip(*theme_keyboard))[0] + ["Другая тема", "⬅️ Назад"]), choose_theme)
            ],
            CHOOSING_GENRE: [
                MessageHandler(filters.Text(list(zip(*genre_keyboard))[0] + ["⬅️ Назад"]), choose_genre)
            ],
            GETTING_TOPIC: [
                MessageHandler(filters.TEXT & ~filters.COMMAND, generate_post)
            ],
            GETTING_CORRECTION: [
                 MessageHandler(filters.TEXT & ~filters.COMMAND, correct_post)
            ],
        },
        fallbacks=[MessageHandler(filters.Text(["❌ Отмена"]), cancel)],
        allow_reentry=True
    )

    application.add_handler(conv_handler)
    
    logger.info("🤖 Бот запущен и готов к работе...")
    
    application.run_polling(allowed_updates=Update.ALL_TYPES)

if __name__ == '__main__':
    main()
