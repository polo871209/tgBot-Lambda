import os

from utils.aws import S3
from utils.imperva import Imperva
from utils.tgbot import Tgbot

api_id = os.environ['api_id']
api_key = os.environ['api_key']
bucket_name = 'ssl-bucket-gaia'


def lambda_handler(event, context):
    tgbot = Tgbot('<chat-id>')
    imperva = Imperva(api_id, api_key)

    try:  # Check if user enter valid syntax
        account_id = event['account_id']
        start_date = event['start_date']
        end_date = event['end_date']
        count = event['count']
    except Exception:  # Please input valid syntax
        tgbot.send_message('Valid syntax: /Command Arguments')
    else:
        if event['statusCode'] == 200:
            try:
                s3 = S3(bucket_name)
                file_name = f'{start_date}-{end_date}.csv'

                imperva.top_sites(account_id, start_date, end_date, count)
                with open(f'/tmp/{file_name}', 'r') as f:
                    data = f.read()
                s3.upload_data(file_name, data)
                url = str(s3.gen_presign_url(file_name))
                tgbot.send_message(url)
            except Exception:
                tgbot.send_message(
                    "請輸入正確格式\n帳號 ID, 開始日期(ex. 2022-02-02), 結束日期, 排名數量")

    return {
        "statusCode": 200
    }
