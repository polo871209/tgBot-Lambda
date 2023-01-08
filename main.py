import logging
import os

from dotenv import load_dotenv
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ApplicationBuilder, ContextTypes, CommandHandler, ConversationHandler, CallbackQueryHandler, \
    MessageHandler, filters

from utils.sectigo import Sectigo
from utils.tgbot import edit_message, send_message

load_dotenv()

TOKEN = os.environ['TOKEN']
START, DV_SINGLE, DV_SINGLE_DAY, DV_WILDCARD, DV_WILDCARD_DAY, REVALIDATE, STATUS, DOWNLOAD, EXIT = range(9)
DOMAIN_REGEX = r'^((?!-))(xn--)?[a-z0-9][a-z0-9-_]{0,61}[a-z0-9]{0,1}\.(xn--)?([a-z0-9\-]{1,61}|[a-z0-9-]{1,30}\.[a-z]{2,})$'
WILDCARD_DOMAIN_REGEX = r'^((?!-))(xn--)?\*.[a-z0-9][a-z0-9-_]{0,61}[a-z0-9]{0,1}\.(xn--)?([a-z0-9\-]{1,61}|[a-z0-9-]{1,30}\.[a-z]{2,})$'
DAY_REGEX = r'^(?:36[6-9]|3[7-8]\d|39[0-4])$'

day = ''
domain = ''

logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await context.bot.send_message(
        chat_id=update.effective_chat.id,
        text="Hi! 我是SSL機器人，請選擇服務",
        reply_markup=InlineKeyboardMarkup([
            [
                InlineKeyboardButton('DV Single', callback_data="single"),
                InlineKeyboardButton('DV Wildcard', callback_data="wildcard"),
            ],
            [
                InlineKeyboardButton('重新驗證', callback_data="revalidate"),
                InlineKeyboardButton('證書狀態', callback_data="status"),
                InlineKeyboardButton('下載證書', callback_data="download"),
                InlineKeyboardButton('離開', callback_data="exit"),
            ]
        ])

    )
    return START


async def callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    callback_data = update.callback_query.data
    if callback_data == "single":
        await edit_message('DV Single,\n請輸入天數(366-395):', update, context)
        return DV_SINGLE_DAY
    elif callback_data == "wildcard":
        await edit_message('DV Wildcard,\n請輸入天數(366-395):', update, context)
        return DV_WILDCARD_DAY
    elif callback_data == "revalidate":
        await edit_message('重新驗證,\n請輸入訂單編號:', update, context)
        return REVALIDATE
    elif callback_data == "status":
        await edit_message('查詢證書狀態,\n請輸入訂單編號:', update, context)
        return STATUS
    elif callback_data == "download":
        await edit_message('下載證書,\n請輸入訂單編號:', update, context)
        return DOWNLOAD
    await edit_message('離開', update, context)
    return EXIT


async def dv_single_days(update: Update, context: ContextTypes.DEFAULT_TYPE):
    global day
    day = update.message.text
    await send_message(f'DV single {day}天,\n請輸入域名:', update, context)
    return DV_SINGLE


async def dv_single(update: Update, context: ContextTypes.DEFAULT_TYPE):
    global domain
    domain = update.message.text
    ssl = Sectigo(domain, day)
    validation, key, csr = ssl.apply_ssl('single')
    await send_message(validation, update, context)
    return EXIT


async def dv_wildcard_days(update: Update, context: ContextTypes.DEFAULT_TYPE):
    global day
    day = update.message.text
    await send_message(f'DV wildcard {day}天,\n請輸入域名:', update, context)
    return DV_WILDCARD


async def dv_wildcard(update: Update, context: ContextTypes.DEFAULT_TYPE):
    global domain
    domain = update.message.text
    ssl = Sectigo(domain, day)
    validation, key, csr = ssl.apply_ssl('wildcard')
    await send_message(validation, update, context)
    return EXIT


def main():
    conv_handler = ConversationHandler(
        entry_points=[CommandHandler('start', start)],
        states={
            START: [CallbackQueryHandler(callback)],
            DV_SINGLE_DAY: [
                MessageHandler(filters.Regex(DAY_REGEX), dv_single_days)
            ],
            DV_SINGLE: [
                MessageHandler(filters.Regex(DOMAIN_REGEX), dv_single)
            ],
            DV_WILDCARD_DAY: [
                MessageHandler(filters.Regex(DAY_REGEX), dv_wildcard_days)
            ],
            DV_WILDCARD: [
                MessageHandler(filters.Regex(WILDCARD_DOMAIN_REGEX), dv_wildcard)
            ],
        },
        fallbacks=[]
    )
    application = ApplicationBuilder().token(TOKEN).build()
    application.add_handler(conv_handler)
    application.run_polling()


if __name__ == '__main__':
    main()
