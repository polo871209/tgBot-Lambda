import logging
import os
import shutil

import requests
from dotenv import load_dotenv, find_dotenv
from flask import Flask
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ApplicationBuilder, ContextTypes, CommandHandler, ConversationHandler, CallbackQueryHandler, \
    MessageHandler, filters

from utils.cloud_storage import CloudStorage
from utils.sectigo import Sectigo
from utils.tgbot import edit_message, send_message, edit_former_message, send_document

load_dotenv(find_dotenv())

TOKEN = os.environ['TOKEN']
CHAT_ID = "-1001810978149"
START, DV_SINGLE, DV_SINGLE_DOMAIN, DV_WILDCARD, DV_WILDCARD_DOMAIN, \
    REVALIDATE, STATUS, DOWNLOAD, ERROR = range(9)
EXIT = ConversationHandler.END

DOMAIN_REGEX = r'^((?!-))(xn--)?[a-z0-9][a-z0-9-_]{0,61}[a-z0-9]{0,1}\.(xn--)?([a-z0-9\-]{1,61}|[a-z0-9-]{1,30}\.[a-z]{2,})$'
WILDCARD_DOMAIN_REGEX = r'^((?!-))(xn--)?\*.[a-z0-9][a-z0-9-_]{0,61}[a-z0-9]{0,1}\.(xn--)?([a-z0-9\-]{1,61}|[a-z0-9-]{1,30}\.[a-z]{2,})$'
DAY_REGEX = r'^(?:36[6-9]|3[7-8]\d|39[0-4])$'
ORDER_REGEX = r'^[0-9]{10}$'

day = ''
domain = ''

logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if str(update.effective_chat.id) != CHAT_ID:
        await send_message("Chat are not allowed! Please exit or chat will be banned!", update, context)
        return EXIT
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
        await edit_message('DV Single,\n請輸入域名(example.com):', update, context)
        return DV_SINGLE_DOMAIN
    elif callback_data == "wildcard":
        await edit_message('DV Wildcard,\n請輸入域名(*.example.com):', update, context)
        return DV_WILDCARD_DOMAIN
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


async def apply_ssl(product: str, update: Update, context: ContextTypes.DEFAULT_TYPE):
    global day
    try:
        day = update.message.text
        ssl = Sectigo(domain, day)
        validation, order, key, csr = ssl.apply_ssl(product)
        _domain = domain.replace('*', 'star')
        bucket = CloudStorage()
        response_1 = bucket.upload_str(f'{order}.{_domain}/{_domain}.key', key.decode('UTF-8'))
        response_2 = bucket.upload_str(f'{order}.{_domain}/{_domain}.csr', csr.decode('UTF-8'))
        if response_1 and response_2:
            await send_message(validation, update, context)
            return EXIT
        return ERROR
    except requests.RequestException:
        return ERROR


async def dv_single(update: Update, context: ContextTypes.DEFAULT_TYPE):
    return await apply_ssl('single', update, context)


async def dv_single_domain(update: Update, context: ContextTypes.DEFAULT_TYPE):
    global domain
    domain = update.message.text
    await edit_former_message(f'DV single {domain},\n請輸入天數(366-395):', 1, update, context)
    return DV_SINGLE


async def dv_wildcard(update: Update, context: ContextTypes.DEFAULT_TYPE):
    return await apply_ssl('wildcard', update, context)


async def dv_wildcard_domain(update: Update, context: ContextTypes.DEFAULT_TYPE):
    global domain
    domain = update.message.text
    await edit_former_message(f'DV wildcard {domain},\n請輸入天數(366-395):', 1, update, context)
    return DV_WILDCARD


async def revalidate(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        order = update.message.text
        await send_message(Sectigo.revalidate(order), update, context)
        return EXIT
    except requests.RequestException:
        return ERROR


async def status(update: Update, context: ContextTypes.DEFAULT_TYPE):
    order = update.message.text
    await send_message(Sectigo.status(order), update, context)
    return EXIT


async def download(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        if not os.path.exists('./tmp'):
            os.mkdir('./tmp')
        order = update.message.text
        _domain, cert = Sectigo.download(order)
        _domain = _domain.replace('*', 'star')
        dir_name = f'{order}.{_domain}'
        file_name = f'./tmp/{dir_name}/{_domain}'
        cs = CloudStorage()
        cs.download_dir(f'{dir_name}/', f'./tmp/')
        with open(f'{file_name}.key', 'r') as key:
            key_str = key.read()
            passphrase, pfx = Sectigo.pem_to_pfx(key_str, cert)
            # pfx = pfx.encode('utf-8')
            with open(f'./tmp/{dir_name}/password.txt', 'w') as f:
                f.write(passphrase)
            with open(f'{file_name}.pfx', 'wb') as f:
                f.write(pfx)
        with open(f'{file_name}.crt', 'w') as f:
            f.write(cert)
        with open(f'{file_name}.pem', 'w') as f:
            f.write(cert)
        shutil.make_archive(f'./tmp/{dir_name}', 'zip', f'./tmp/{dir_name}')
        os.rename(f'./tmp/{dir_name}.zip', f"./tmp/{_domain.replace('.', '_')}.zip")
        await send_document(f"./tmp/{_domain.replace('.', '_')}.zip", update, context)
    except Exception:
        return ERROR
    return EXIT


async def error(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await send_message('輸入錯誤，請重新嘗試', update, context)
    return EXIT


app = Flask(__name__)


@app.route("/")
def main():
    conv_handler = ConversationHandler(
        entry_points=[CommandHandler('start', start)],
        states={
            START: [CallbackQueryHandler(callback)],
            DV_SINGLE_DOMAIN: [
                MessageHandler(filters.Regex(DOMAIN_REGEX), dv_single_domain),
                MessageHandler(filters.Regex('.*'), error)
            ],
            DV_SINGLE: [
                MessageHandler(filters.Regex(DAY_REGEX), dv_single),
                MessageHandler(filters.Regex('.*'), error)
            ],
            DV_WILDCARD_DOMAIN: [
                MessageHandler(filters.Regex(WILDCARD_DOMAIN_REGEX), dv_wildcard_domain),
                MessageHandler(filters.Regex('.*'), error)
            ],
            DV_WILDCARD: [
                MessageHandler(filters.Regex(DAY_REGEX), dv_wildcard),
                MessageHandler(filters.Regex('.*'), error)
            ],
            REVALIDATE: [
                MessageHandler(filters.Regex(ORDER_REGEX), revalidate),
                MessageHandler(filters.Regex('.*'), error)
            ],
            STATUS: [
                MessageHandler(filters.Regex(ORDER_REGEX), status),
                MessageHandler(filters.Regex('.*'), error)
            ],
            DOWNLOAD: [
                MessageHandler(filters.Regex(ORDER_REGEX), download),
                MessageHandler(filters.Regex('.*'), error)
            ],
            ERROR: [
                MessageHandler(filters.Regex('.*'), error)
            ]
        },
        fallbacks=[]
    )

    application = ApplicationBuilder().token(TOKEN).build()
    application.add_handler(conv_handler)
    application.run_polling()


if __name__ == "__main__":
    main()
