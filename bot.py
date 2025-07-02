import os
import openai
from telegram import Update, ReplyKeyboardMarkup
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, filters, ContextTypes, ConversationHandler

BOT_TOKEN = os.getenv("BOT_TOKEN")
openai.api_key = os.getenv("OPENAI_API_KEY")

CHOOSE_ACTION, ASK_QUESTION, ASK_MAP_TYPE, ASK_MAP_QUESTIONS = range(4)

main_menu = ReplyKeyboardMarkup(
    [['🧠 Получить консультацию', '🗺️ Создать психологическую карту']],
    resize_keyboard=True
)

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "Привет! Я психологический бот. Выбери, что хочешь сделать:",
        reply_markup=main_menu
    )
    return CHOOSE_ACTION

async def choose_action(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text

    if 'консультацию' in text:
        await update.message.reply_text("Напиши свой вопрос, и я постараюсь помочь.")
        return ASK_QUESTION

    elif 'психологическую карту' in text:
        await update.message.reply_text("Выбери тип карты:\n1. Базовая (4 вопроса)\n2. Расширенная (10 вопросов)")
        return ASK_MAP_TYPE

    else:
        await update.message.reply_text("Пожалуйста, выбери действие из меню.")
        return CHOOSE_ACTION

async def ask_question(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_question = update.message.text

    try:
        response = openai.ChatCompletion.create(
            model="gpt-3.5-turbo",
            messages=[
                {"role": "system", "content": "Ты опытный психолог. Отвечай спокойно, мягко и профессионально."},
                {"role": "user", "content": user_question}
            ]
        )
        answer = response.choices[0].message.content.strip()
    except Exception as e:
        answer = "Произошла ошибка при генерации ответа. Попробуй позже."

    await update.message.reply_text(f"🔍 Ответ психолога:\n\n{answer}")
    return CHOOSE_ACTION

async def ask_map_type(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text.strip()

    if text.startswith("1"):
        context.user_data['map_type'] = 'base'
        context.user_data['questions'] = [
            "Как ты себя чувствуешь сегодня?",
            "Что тебя больше всего тревожит?",
            "Как ты обычно справляешься со стрессом?",
            "Опиши ситуацию, когда чувствовал(а) себя особенно счастливым(ой)."
        ]
    elif text.startswith("2"):
        context.user_data['map_type'] = 'extended'
        context.user_data['questions'] = [
            "Как ты себя чувствуешь сегодня?",
            "Что тебя больше всего тревожит?",
            "Как ты обычно справляешься со стрессом?",
            "Опиши ситуацию, когда чувствовал(а) себя особенно счастливым(ой).",
            "Как ты воспринимаешь своё детство?",
            "Какие у тебя отношения с близкими?",
            "Что вызывает у тебя чувство вины?",
            "Как ты представляешь своё будущее?",
            "Какие у тебя цели на ближайший год?",
            "Чего ты боишься больше всего?"
        ]
    else:
        await update.message.reply_text("Выбери 1 или 2.")
        return ASK_MAP_TYPE

    context.user_data['answers'] = []
    return await ask_next_question(update, context)

async def ask_next_question(update: Update, context: ContextTypes.DEFAULT_TYPE):
    questions = context.user_data['questions']
    answers = context.user_data['answers']

    if len(answers) < len(questions):
        await update.message.reply_text(questions[len(answers)])
        return ASK_MAP_QUESTIONS
    else:
        text = "\n\n".join(f"{q}\n➡ {a}" for q, a in zip(questions, answers))
        await update.message.reply_text("Спасибо! Карта отправлена на модерацию.")
        admin_chat_id = "ВАШ_TG_ID"
        await context.bot.send_message(chat_id=admin_chat_id, text=f"🗺️ Новая психологическая карта:\n\n{text}")
        return CHOOSE_ACTION

async def collect_answer(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data['answers'].append(update.message.text)
    return await ask_next_question(update, context)

app = ApplicationBuilder().token(BOT_TOKEN).build()

conv_handler = ConversationHandler(
    entry_points=[CommandHandler("start", start)],
    states={
        CHOOSE_ACTION: [MessageHandler(filters.TEXT, choose_action)],
        ASK_QUESTION: [MessageHandler(filters.TEXT, ask_question)],
        ASK_MAP_TYPE: [MessageHandler(filters.TEXT, ask_map_type)],
        ASK_MAP_QUESTIONS: [MessageHandler(filters.TEXT, collect_answer)],
    },
    fallbacks=[]
)

app.add_handler(conv_handler)
app.run_polling()
