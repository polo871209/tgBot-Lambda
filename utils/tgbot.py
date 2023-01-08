from telegram import Update
from telegram.ext import ContextTypes


async def edit_message(message: str, update: Update, context: ContextTypes.DEFAULT_TYPE):
    await context.bot.editMessageText(
        chat_id=update.effective_chat.id,
        message_id=update.callback_query.message.message_id,
        text=message
    )


async def send_message(message: str, update: Update, context: ContextTypes.DEFAULT_TYPE):
    await context.bot.send_message(
        chat_id=update.effective_chat.id,
        text=message
    )
