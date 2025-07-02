import os
from telegram import Update, ReplyKeyboardMarkup
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, filters, ContextTypes, ConversationHandler

BOT_TOKEN = os.getenv("BOT_TOKEN")
ADMIN_ID = int(os.getenv("ADMIN_ID"))

CHOOSE_ACTION, ASK_QUESTION = range(2)

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
        await update.message.reply_text("Напиши свой вопрос, и я передам его специалисту.")
        return ASK_QUESTION
    elif 'психологическую карту' in text:
        await update.message.reply_text("Эта функция сейчас в разработке.")
        return CHOOSE_ACTION
    else:
        await update.message.reply_text("Пожалуйста, выбери действие из меню.")
        return CHOOSE_ACTION

async def handle_question(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.message.from_user
    user_id = update.message.chat_id
    username = user.username or "без ника"
    question = update.message.text

    message = f"📩 Новый вопрос от пользователя:

"               f"👤 @{username}
🆔 {user_id}

"               f"💬 Вопрос: {question}"

    await context.bot.send_message(chat_id=ADMIN_ID, text=message)
    await update.message.reply_text("Вопрос передан. Ожидай ответ.")
    return CHOOSE_ACTION

async def reply_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.message.chat_id != ADMIN_ID:
        await update.message.reply_text("Эта команда доступна только администратору.")
        return

    args = context.args
    if len(args) < 2:
        await update.message.reply_text("Использование: /ответ <user_id> <текст ответа>")
        return

    try:
        user_id = int(args[0])
        reply_text = ' '.join(args[1:])
        await context.bot.send_message(chat_id=user_id, text=f"💬 Ответ от психолога:

{reply_text}")
        await update.message.reply_text("Ответ отправлен.")
    except Exception as e:
        await update.message.reply_text(f"Ошибка при отправке ответа: {e}")

app = ApplicationBuilder().token(BOT_TOKEN).build()

conv_handler = ConversationHandler(
    entry_points=[CommandHandler("start", start)],
    states={
        CHOOSE_ACTION: [MessageHandler(filters.TEXT, choose_action)],
        ASK_QUESTION: [MessageHandler(filters.TEXT, handle_question)],
    },
    fallbacks=[]
)

app.add_handler(conv_handler)
app.add_handler(CommandHandler("ответ", reply_command))

app.run_polling()
