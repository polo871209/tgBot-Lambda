# invoker function behind api gateway before main function

import json
import os

import boto3

from utils.tgbot import Tgbot

ssl_bot_arn = os.environ['ssl_bot_arn']
imperva_bot_arn = os.environ['imperva_bot_arn']
email_bot_arn = os.environ['email_bot_arn']


def lambda_handler(event, context):
    payload = json.loads(event['body'])  # payload from telegram
    chat_id = str(payload['message']['chat']['id'])

    if chat_id == '<chat-id>':
        tgbot = Tgbot('<chat-id>')
        client = boto3.client('lambda')

        try:  # check user input message
            message = payload['message']['text']
        except KeyError:  # message not found
            caption = payload['message']['caption']

            if '/addmail' in caption:
                try:  # Check if user upload file
                    file_id = str(payload['message']['document']['file_id'])

                    event_params = {
                        'statusCode': 200,
                        'file_id': file_id
                    }
                    # pass payload to main function
                    client.invoke(
                        FunctionName=email_bot_arn,
                        InvocationType='Event',
                        Payload=json.dumps(event_params)
                    )
                    # notify user request success
                    tgbot.send_message('email 產生中，請稍後')

                except Exception:
                    tgbot.send_message('請包含上傳檔案')
        else:
            if '/topsite' in message:
                try:
                    text = message.split()
                    # get data from payload
                    event_params = {
                        'statusCode': 200,
                        'account_id': text[1],
                        'start_date': text[2],
                        'end_date': text[3],
                        'count': text[4]
                    }
                    # pass payload to main function
                    client.invoke(
                        FunctionName=imperva_bot_arn,
                        InvocationType='Event',
                        Payload=json.dumps(event_params)
                    )
                    # notify user request success
                    tgbot.send_message('產生中，請稍後')

                except Exception:
                    tgbot.send_message("請輸入正確格式\n帳號 ID, 開始日期(ex. 2022-02-02), 結束日期, 排名數量")
            elif '/dvsingle' or '/dvwildcard' or '/validate' or '/status' or '/download' in message:

                event_params = {
                    'statusCode': 200,
                    'message': message
                }

                client.invoke(
                    FunctionName=ssl_bot_arn,
                    InvocationType='Event',
                    Payload=json.dumps(event_params)
                )

            else:
                tgbot.send_message('輸入 / 確認有效指令')
    else:
        tgbot = Tgbot(chat_id)
        tgbot.send_message('not allowed!')

    return {
        'statusCode': 200,
    }
