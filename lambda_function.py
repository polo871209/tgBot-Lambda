import json

from utils.aws import S3
from utils.sectigo import Sectigo
from utils.tgbot import Tgbot

BUCKET_NAME = 'your_bucketname'
CHAT_ID = 'allowed-chat-id'


def lambda_handler(event, context) -> dict:
    """
    This function receive webhook event and parse command
    :return: status to end webhook update
    """
    # Read event from webhook
    message = json.loads(event['body'])
    chat_id = str(message['message']['chat']['id'])

    if chat_id == CHAT_ID:  # if user invoke from allowed chat
        tgbot = Tgbot(CHAT_ID)
        text = message['message']['text'].split()
        command, argument = text[0], text[1:]
        s3 = S3(BUCKET_NAME)

        if '/dvsingle' in command:
            try:
                domain = argument[0]
                try:  # if date are not specify, use default
                    ssl = Sectigo(domain, argument[1])
                except IndexError:
                    ssl = Sectigo(domain)
                tgbot.send_message(f'Generating dvsingle: {domain}')
                validation, order_number, pkey, csr = ssl.dv_single()
            except IndexError:
                tgbot.send_message(f'Error: Please enter a domain name')
            except Exception as err:
                tgbot.send_message(f'Error: {err}')
            else:
                file_name = domain.replace('.', '_')
                file_path = f'{order_number}_{file_name}/{file_name}'
                r1 = s3.upload_data(f'{file_path}.key', pkey)
                r2 = s3.upload_data(f'{file_path}.csr', csr)
                if r1 and r2:  # check if key and csr successfully update
                    tgbot.send_message(validation)
                else:
                    tgbot.send_message('Data upload to s3 failed')

        elif '/dvwildcard' in command:
            try:
                domain = argument[0]
                if '*' not in domain:
                    raise ValueError
                else:
                    tgbot.send_message(f'Generating dvwildcard: {domain}')
                    try:  # if date are not specify, use default
                        ssl = Sectigo(domain, argument[1])
                    except IndexError:
                        ssl = Sectigo(domain)
                    validation, order_number, pkey, csr = ssl.dv_wildcard()
            except ValueError:
                tgbot.send_message('Valid Syntax: *.example.com')
            except IndexError:
                tgbot.send_message(f'Error: Please enter a domain name')
            except Exception as err:
                tgbot.send_message(f'Error: {err}')
            else:
                file_name = domain.replace('.', '_').replace('*', 'star')
                file_path = f'{order_number}_{file_name}/{file_name}'
                r1 = s3.upload_data(f'{file_path}.key', pkey)
                r2 = s3.upload_data(f'{file_path}.csr', csr)
                if r1 and r2:  # check if key and csr successfully update
                    tgbot.send_message(validation)
                else:
                    tgbot.send_message('Data upload to s3 failed')

        elif '/validate' in command:
            try:
                order_number = argument[0]
                tgbot.send_message('Revalidating...')
                response = Sectigo.revalidate(order_number)
            except IndexError:
                tgbot.send_message(f'Error: Please enter a order number')
            except Exception as err:
                tgbot.send_message(f'Error: {err}')
            else:
                if response:
                    tgbot.send_message('Success!\nUse: /status to check status.')
                else:
                    tgbot.send_message('Please enter valid order number, or order already issued.')
        elif '/status' in command:
            try:
                order_number = argument[0]
                tgbot.send_message('Checking status...')
                response = Sectigo.cert_status(order_number)
            except IndexError:
                tgbot.send_message(f'Error: Please enter a order number')
            except Exception as err:
                tgbot.send_message(f'Error: {err}')
            else:
                if not response:
                    tgbot.send_message(f'Order: {argument[0]}\nStatus: Not Issued')
                else:
                    tgbot.send_message(f'Order: {argument[0]}\nStatus: Issued\nExpire date: {response}')

        elif '/download' in text[0]:
            try:
                order_number = argument[0]
                tgbot.send_message('Downloading...')
                domain, cert = Sectigo.download_cert(order_number)
                file_name = domain.replace('.', '_').replace('*', 'star')  # window don't recognize * as file name
                path = f'{order_number}_{file_name}/{file_name}'
                key = s3.get_object(f'{path}.key')  # download key file to gen pfx
                passphrase, pfx = Sectigo.pem_to_pfx(key, cert)
                # upload all the file to as then zip it
                s3.upload_data(f'{path}.pem', cert)
                s3.upload_data(f'{path}.crt', cert)
                s3.upload_data(f'{path}.pfx', pfx)
                s3.upload_data(f'{order_number}_{file_name}/password.txt', passphrase)
                s3.zip_folder(f'{order_number}_{file_name}', path)
            except IndexError:
                tgbot.send_message(f'Error: Please enter a order number')
            except Exception as err:
                tgbot.send_message(f'Download failed!\nError: {err}')
            else:  # gen pre-signed url
                presign_url = s3.gen_presign_url(f'{path}.zip')
                tgbot.send_message(presign_url)
        else:
            tgbot.send_message('Type / to see what you can do')
    else:
        tgbot = Tgbot(chat_id)
        tgbot.send_message('not allowed')

    return {
        "statusCode": 200
    }
