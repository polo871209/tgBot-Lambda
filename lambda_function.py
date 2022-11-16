from sectigo import Sectigo, certstatus, download_cert, revalidate
from tgbot import Tgbot
from aws import S3
import json


def lambda_handler(event, context):
    message = json.loads(event['body'])
    chat_id = str(message['message']['chat']['id'])
    tgbot = Tgbot(chat_id)
    try:  # Check if user enter valid syntax
        text = message['message']['text'].split()
        command = text[0]
        argument = text[1:]
    except:  # Please input valid syntax
        tgbot.send_message('Valid syntax: {/Command} {Arguments}')
    else:
        if '/dvsingle' in command:  # Generate dvsingle
            tgbot.send_message(f'dvsingle: {argument[0]}, generating cname...')
            ssl = Sectigo(argument[0], argument[1])
            try:
                validation, order_number, pkey, csr = ssl.dv_single()
                s3 = S3()
            except:
                tgbot.send_message(
                    'Failed to generate DV single cert, please contact admin')
            else:
                file_path = f'{order_number}_{argument[0]}/{argument[0]}'
                r1 = s3.upload_data(
                    f'{file_path}.key', pkey)
                r2 = s3.upload_data(
                    f'{file_path}.csr', csr)
                if r1 and r2:
                    tgbot.send_message(validation)
                else:
                    tgbot.send_message(
                        'Data upload to s3 failed, please contact admin')
        elif '/revalidate' in command:  # Revalidate  order
            tgbot.send_message('Revalidating...Please wait')
            response = revalidate(argument[0])
            if response:
                tgbot.send_message(
                    'Success!\nUse: /certstatus to check status.')
            else:
                tgbot.send_message(
                    'Please enter valid order number, or order already issued.')
        elif '/certstatus' in command:  # Order status
            tgbot.send_message('Checking status...Please wait')
            response = certstatus(argument[0])
            if not response:
                tgbot.send_message(
                    f'Order: {argument[0]}\nStatus: Not Issued\nUse /revalidate or check your cname value')
            else:
                tgbot.send_message(
                    f'Order: {argument[0]}\nStatus: Issued\nExpire date: {response}')

        elif '/downloadcert' in text[0]:  # Download order
            try:
                tgbot.send_message('Downloading...Please wait')
                common_name, cert = download_cert(argument[0])
            except:
                tgbot.send_message(
                    'Downlaod failed!\nPlease input valid order or check /certstatus')
            else:
                s3 = S3()
                s3.upload_data(
                    f'{argument[0]}_{common_name}/{common_name}.pem', cert)
                tgbot.send_message(f'Domain: {common_name}')
        else:
            tgbot.send_message('Click Menu to see what you can do')

    return {"statusCode": 200}
