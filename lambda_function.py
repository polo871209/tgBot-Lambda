from utils.sectigo import Sectigo
from utils.tgbot import Tgbot
from utils.aws import S3
import json

BUCKET_NAME = 'your_bucketname'


def lambda_handler(event, context):
    message = json.loads(event['body'])
    chat_id = str(message['message']['chat']['id'])
    tgbot = Tgbot(chat_id)
    try:  # Check if user enter valid syntax
        text = message['message']['text'].split()
        command, argument = text[0], text[1:]
    except Exception:  # Please input valid syntax
        tgbot.send_message('Valid syntax: /Command Arguments')
    else:
        if '/dvsingle' in command:  # Generate dvsingle
            try:
                domain = argument[0]
                try:
                    ssl = Sectigo(domain, argument[1])
                except IndexError:
                    ssl = Sectigo(domain)
                s3 = S3(BUCKET_NAME)
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
                if r1 and r2:
                    tgbot.send_message(validation)
                else:
                    tgbot.send_message('Data upload to s3 failed')

        elif '/dvwildcard' in command:  # Generate dvsingle
            try:
                domain = argument[0]
                if '*' not in domain:
                    raise ValueError
                else:
                    tgbot.send_message(f'Generating dvwildcard: {domain}')
                    s3 = S3(BUCKET_NAME)
                    try:
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
                if r1 and r2:
                    tgbot.send_message(validation)
                else:
                    tgbot.send_message('Data upload to s3 failed')

        elif '/revalidate' in command:  # Revalidate  order
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
                    tgbot.send_message('Success!\nUse: /certstatus to check status.')
                else:
                    tgbot.send_message(
                        'Please enter valid order number, or order already issued.')
        elif '/certstatus' in command:  # Order status
            try:
                order_number = argument[0]
                tgbot.send_message('Checking status...')
                response = Sectigo.certstatus(order_number)
            except IndexError:
                tgbot.send_message(f'Error: Please enter a order number')
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
                order_number = argument[0]
                tgbot.send_message('Downloading...')
                s3 = S3(BUCKET_NAME)
                domain, cert = Sectigo.download_cert(order_number)
                file_name = domain.replace('.', '_').replace('*', 'star')
                path = f'{order_number}_{file_name}/{file_name}'
                key = s3.get_object(f'{path}.key')
                passphrase, pfx = Sectigo.pem_to_pfx(key, cert)
                s3.upload_data(f'{path}.pem', cert)
                s3.upload_data(f'{path}.crt', cert)
                s3.upload_data(f'{path}.pfx', pfx)
                s3.upload_data(f'{order_number}_{file_name}/password.txt', passphrase)
                s3.zip_folder(f'{order_number}_{file_name}', path)
            except IndexError:
                tgbot.send_message(f'Error: Please enter a order number')
            except Exception as err:
                tgbot.send_message(f'Download failed!\nError: {err}')
            else:
                presign_url = s3.gen_presign_url(f'{path}.zip')
                tgbot.send_message(presign_url)
        else:
            tgbot.send_message('Type / to see what you can do')

    return {"statusCode": 200}
