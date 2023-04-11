# this function create email with uploaded file id
import os

from utils.aws import S3
from utils.migadu_email import create_email
from utils.tgbot import Tgbot

bucket_name = 'ssl-bucket-gaia'


def lambda_handler(event, context):
    tgbot = Tgbot('<chat-id>')
    s3 = S3(bucket_name)

    file_id = event['file_id']
    file_name = '/tmp/info.csv'
    try:
        file_data = tgbot.download_file(file_id)
        mail_list = file_data.split('\n')
        try:
            os.remove(file_name)
        except Exception:
            pass
        with open(file_name, 'w') as f:
            f.write('email,password\n')
        try:  # create and write file
            for mail in mail_list:
                payload = mail.split(',')
                email, password = create_email(payload[0], payload[1], payload[2][:-1])
                with open(file_name, 'a') as f:
                    f.write(f'{email},{password}\n')
        except IndexError:
            pass
        with open(file_name, 'r') as f:
            data = f.read()
        s3.upload_data(file_name, data)
        url = str(s3.gen_presign_url(file_name))
        tgbot.send_message(url)
    except Exception:
        tgbot.send_message('無法讀取檔案，請重新嘗試')
    return {
        'statusCode': 200
    }
