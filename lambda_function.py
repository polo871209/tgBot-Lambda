from sectigo import Sectigo
from tgbot import Tgbot
from aws import S3
import json
import sys


BUCKET_NAME = 'your_bucketname'


def lambda_handler(event, context):
    message = json.loads(event['body'])
    chat_id = str(message['message']['chat']['id'])
    tgbot = Tgbot(chat_id)
    try:  # Check if user enter valid syntax
        text = message['message']['text'].split()
        command = text[0]
        argument = text[1:]
    except Exception:  # Please input valid syntax
        tgbot.send_message('Valid syntax: {/Command} {Arguments}')
    else:
        if '/dvsingle' in command:  # Generate dvsingle
            try:
                domian = argument[0]
                tgbot.send_message(f'Generating dvsingle: {domian}')
                s3 = S3(BUCKET_NAME)
                try:
                    ssl = Sectigo(domian, argument[1])
                except IndexError:
                    ssl = Sectigo(domian)
                validation, order_number, pkey, csr = ssl.dv_single()
            except Exception as err:
                tgbot.send_message(f'Error: {err}')
            else:
                file_name = domian.replace('.', '_')
                file_path = f'{order_number}_{file_name}/{file_name}'
                r1 = s3.upload_data(
                    f'{file_path}.key', pkey)
                r2 = s3.upload_data(
                    f'{file_path}.csr', csr)
                if r1 and r2:
                    tgbot.send_message(validation)
                else:
                    tgbot.send_message('Data upload to s3 failed')

        elif '/dvwildcard' in command:  # Generate dvsingle
            try:
                domian = argument[0]
                if '*' not in domian:
                    raise ValueError
                else:
                    tgbot.send_message(f'Generating dvwildcard: {domian}')
                    s3 = S3(BUCKET_NAME)
                    try:
                        ssl = Sectigo(domian, argument[1])
                    except IndexError:
                        ssl = Sectigo(domian)
                    validation, order_number, pkey, csr = ssl.dv_wildcard()
            except ValueError:
                tgbot.send_message('Valid Syntax: *.example.com')
            except Exception as err:
                tgbot.send_message(f'Error: {err}')
            else:
                file_name = domian.replace('.', '_').replace('*', 'star')
                file_path = f'{order_number}_{file_name}/{file_name}'
                r1 = s3.upload_data(
                    f'{file_path}.key', pkey)
                r2 = s3.upload_data(
                    f'{file_path}.csr', csr)
                if r1 and r2:
                    tgbot.send_message(validation)
                else:
                    tgbot.send_message('Data upload to s3 failed')

        elif '/revalidate' in command:  # Revalidate  order
            tgbot.send_message('Revalidating...')
            try:
                response = Sectigo.revalidate(argument[0])
            except Exception as err:
                tgbot.send_message(f'Error: {err}')
            else:
                if response:
                    tgbot.send_message(
                        'Success!\nUse: /certstatus to check status.')
                else:
                    tgbot.send_message(
                        'Please enter valid order number, or order already issued.')
        elif '/certstatus' in command:  # Order status
            tgbot.send_message('Checking status...')
            try:
                response = Sectigo.certstatus(argument[0])
            except Exception as err:
                tgbot.send_message(f'Error: {err}')
            else:
                if not response:
                    tgbot.send_message(
                        f'Order: {argument[0]}\nStatus: Not Issued')
                else:
                    tgbot.send_message(
                        f'Order: {argument[0]}\nStatus: Issued\nExpire date: {response}')

        elif '/downloadcert' in text[0]:  # Download order
            try:
                tgbot.send_message('Downloading...')
                s3 = S3(BUCKET_NAME)
                domian, cert = Sectigo.download_cert(argument[0])
                file_name = domian.replace('.', '_').replace('*', 'star')
                path = f'{argument[0]}_{file_name}/{file_name}'
                key = s3.get_object(f'{path}.key')
                passphrase, pfx = Sectigo.pem_to_pfx(key, cert)
                s3.upload_data(f'{path}.pem', cert)
                s3.upload_data(f'{path}.crt', cert)
                s3.upload_data(f'{path}.pfx', pfx)
                s3.upload_data(
                    f'{argument[0]}_{file_name}/password.txt', passphrase)
                s3.zip_folder(f'{argument[0]}_{file_name}', path)
            except IndexError:
                tgbot.send_message(f'Downlaod failed!\nError: Enter a order number')
            except Exception as err:
                tgbot.send_message(f'Downlaod failed!\nError: {err}')
            else:
                pre_signurl = s3.gen_presigned_url(f'{path}.zip')
                tgbot.send_message(pre_signurl)
        else:
            tgbot.send_message('Click Menu to see what you can do')

    return {"statusCode": 200}
