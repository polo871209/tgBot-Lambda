# this is file which use python-telegram-bot~=20.0, still working on it,
# where I can replace using docker in the future .


import logging

from telegram import Update, ReplyKeyboardMarkup
from telegram.ext import ApplicationBuilder, ContextTypes, CommandHandler, ConversationHandler, \
    MessageHandler, filters

from utils.sectigo import Sectigo

TOKEN = ""
START, SINGLE_DOMAIN, WILDCARD_DOMAIN = range(3)

logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)

reply_keyboard = [
    ["DV single", "DV wildcard"],
    ["重新驗證", "證書狀態", "下載證書"]
]

start_markup = ReplyKeyboardMarkup(reply_keyboard, one_time_keyboard=True)


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        text="請選擇服務",
        reply_markup=start_markup
    )
    return START


async def single_domain(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await context.bot.send_message(
        chat_id=update.effective_chat.id,
        text="""輸入域名及天數: """
    )
    return SINGLE_DOMAIN


async def wildcard_domain(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await context.bot.send_message(
        chat_id=update.effective_chat.id,
        text="""輸入域名及天數: """
    )
    return WILDCARD_DOMAIN


async def dv_single(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        domain, days = update.message.text.split()
        ssl = Sectigo(domain, days)
    except IndexError:
        domain = update.message.text
        ssl = Sectigo(domain)
    finally:
        await context.bot.send_message(
            chat_id=update.effective_chat.id,
            text=f'Generating DV single: {domain}'
        )


async def dv_wildcard(update: Update, context: ContextTypes.DEFAULT_TYPE):
    domain, days = update.message.text.split()


def main():
    conv_handler = ConversationHandler(
        entry_points=[CommandHandler('start', start)],
        states={
            START: [
                MessageHandler(
                    filters.Regex("^(DV single)$"), single_domain
                ),
                MessageHandler(
                    filters.Regex("^(DV wildcard)$"), wildcard_domain
                ),
                MessageHandler(
                    filters.Regex("^(重新驗證)$"), dv_wildcard
                ),
                MessageHandler(
                    filters.Regex("^(證書狀態)$"), dv_wildcard
                ),
                MessageHandler(
                    filters.Regex("^(下載證書)$"), dv_wildcard
                ),
            ],
            SINGLE_DOMAIN: [
                MessageHandler(
                    filters.Regex(".*"), dv_single
                ),
            ],
            WILDCARD_DOMAIN: [
                MessageHandler(
                    filters.Regex(".*"), dv_wildcard
                ),
            ]
        },
        fallbacks=[]
    )
    application = ApplicationBuilder().token(TOKEN).build()
    application.add_handler(conv_handler)
    application.run_polling()


if __name__ == '__main__':
    main()
