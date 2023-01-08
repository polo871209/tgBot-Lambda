import logging

from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ApplicationBuilder, ContextTypes, CommandHandler, ConversationHandler, CallbackQueryHandler, \
    MessageHandler, filters

from utils.sectigo import Sectigo
from utils.tgbot import edit_message

START, DV_SINGLE, DV_SINGLE_DAY, DV_WILDCARD, DV_WILDCARD_DAY, REVALIDATE, STATUS, DOWNLOAD, EXIT = range(9)
DOMAIN_REGEX = r'^((?!-))(xn--)?[a-z0-9][a-z0-9-_]{0,61}[a-z0-9]{0,1}\.(xn--)?([a-z0-9\-]{1,61}|[a-z0-9-]{1,30}\.[a-z]{2,})$'
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
        await edit_message('DV Single, 請輸入完整域名(example.com):', update, context)
        return DV_SINGLE_DAY
    elif callback_data == "wildcard":
        await edit_message('DV Wildcard, 請輸入完整域名(*.example.com):', update, context)
        return DV_WILDCARD_DAY
    elif callback_data == "revalidate":
        await edit_message('重新驗證, 請輸入訂單編號:', update, context)
        return REVALIDATE
    elif callback_data == "status":
        await edit_message('查詢證書狀態, 請輸入訂單編號:', update, context)
        return STATUS
    elif callback_data == "download":
        await edit_message('下載證書, 請輸入訂單編號:', update, context)
        return DOWNLOAD
    await edit_message('離開', update, context)
    return EXIT


async def dv_single_days(update: Update, context: ContextTypes.DEFAULT_TYPE):
    global day
    day = update.message.text
    return DV_SINGLE


async def dv_single(update: Update, context: ContextTypes.DEFAULT_TYPE):
    global domain
    domain = update.message.text
    ssl = Sectigo(domain, day)
    Sectigo.apply_ssl('single')


def main():
    conv_handler = ConversationHandler(
        entry_points=[CommandHandler('start', start)],
        states={
            START: [CallbackQueryHandler(callback)],
            DV_SINGLE_DAY: [
                MessageHandler(filters.Regex(DAY_REGEX), dv_single_days)
            ],
            DV_SINGLE: [
                MessageHandler(
                    filters.Regex(DOMAIN_REGEX), dv_single,
                )
            ]
        },
        fallbacks=[]
    )
    application = ApplicationBuilder().token('5632658812:AAGqjBlRgCRsUMNwLWAVwncS0mg-weFhh3Q').build()
    application.add_handler(conv_handler)
    application.run_polling()


if __name__ == '__main__':
    main()
