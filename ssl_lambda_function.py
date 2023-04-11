from utils.aws import S3
from utils.sectigo import Sectigo
from utils.tgbot import Tgbot

BUCKET_NAME = 'ssl-bucket-gaia'


def lambda_handler(event, context) -> dict:

    tgbot = Tgbot('<chat-id>')
    text = event['message'].split()
    command, argument = text[0], text[1:]
    s3 = S3(BUCKET_NAME)

    if '/dvsingle' in command:
        try:
            domain = argument[0]
            try:  # if date are not specify, use default
                ssl = Sectigo(domain, argument[1])
            except IndexError:
                ssl = Sectigo(domain)
            tgbot.send_message(f'Dv single 產生中: {domain}')
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
                tgbot.send_message(f'Dv wildcard 產生中: {domain}')
                try:  # if date are not specify, use default
                    ssl = Sectigo(domain, argument[1])
                except IndexError:
                    ssl = Sectigo(domain)
                validation, order_number, pkey, csr = ssl.dv_wildcard()
        except ValueError:
            tgbot.send_message('有效域名: *.example.com')
        except IndexError:
            tgbot.send_message('請輸入域名')
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
            tgbot.send_message('驗證中')
            response = Sectigo.revalidate(order_number)
        except IndexError:
            tgbot.send_message('請輸入訂單編號')
        except Exception as err:
            tgbot.send_message(f'Error: {err}')
        else:
            if response:
                tgbot.send_message('成功!\n用: /status 來確認狀態')
            else:
                tgbot.send_message('請確認訂單邊好, 或訂單已經簽發')
    elif '/status' in command:
        try:
            order_number = argument[0]
            tgbot.send_message('確認狀態')
            response = Sectigo.cert_status(order_number)
        except IndexError:
            tgbot.send_message(f'請輸入訂單編號')
        except Exception as err:
            tgbot.send_message(f'Error: {err}')
        else:
            if not response:
                tgbot.send_message(f'訂單: {argument[0]}\n狀態: 尚未簽發')
            else:
                tgbot.send_message(f'訂單: {argument[0]}\n狀態: 簽發\n過期日: {response}')

    elif '/download' in text[0]:
        try:
            order_number = argument[0]
            tgbot.send_message('下載中')
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
            tgbot.send_message(f'請輸入訂單編號')
        except Exception as err:
            tgbot.send_message(f'下載失敗!，請確認訂單已簽發')
        else:  # gen pre-signed url
            presign_url = s3.gen_presign_url(f'{path}.zip')
            tgbot.send_message(presign_url)
    else:
        tgbot.send_message('輸入 / 確認可用指令')

    return {
        "statusCode": 200
    }
