import tgbot
import pwen
import sectigo
import awss3
import json


def lambda_handler(event, context):
    message = json.loads(event['body'])
    chat_id = str(message['message']['chat']['id'])
    try:
        text = message['message']['text'].split()
        if 'pwnedcheck' in text[0]:
            tgbot.send_message(pwen.main(text[1]), chat_id)
        elif 'dvsingle' in text[0]:
            tgbot.send_message(
                f'dvsingle: {text[1]}, generating cname...', chat_id)
            validation, order_number, pkey, csr = sectigo.apply_ssl(
                'dvsingle', text[1], text[2])
            tgbot.send_message(validation, chat_id)
            awss3.upload_data(
                f'{order_number}_{text[1]}/', f'{text[1]}.key', pkey)
            awss3.upload_data(
                f'{order_number}_{text[1]}/', f'{text[1]}.csr', csr)
        elif 'revalidate' in text[0]:
            tgbot.send_message('Revalidating...', chat_id)
            response = sectigo.revalidate(text[1])
            if 'errorCode=0' in response:
                tgbot.send_message(
                    f'Success!\nUse: /certstatus to check status.', chat_id)
            else:
                tgbot.send_message(
                    'Please enter valid order number, or order already issued.', chat_id)
        elif 'certstatus' in text[0]:
            tgbot.send_message('Checking status...', chat_id)
            response = sectigo.certstatus(text[1])
            if 'Not' in response:
                tgbot.send_message(
                    f'Order: {text[1]}\nStatus: Not Issued\nUse /revalidate or check your cname value', chat_id)
            else:
                tgbot.send_message(
                    f'Order: {text[1]}\nStatus: Issued\nExpire date: {response}', chat_id)

        elif 'downloadcert' in text[0]:
            try:
                tgbot.send_message('Downloading...', chat_id)
                FQDN, cert = sectigo.download_cert(text[1])
                awss3.upload_data(f'{text[1]}_{FQDN}/', f'{FQDN}.pem', cert)
                key_url = awss3.presigned_url(
                    f'{text[1]}_{FQDN}/{FQDN}.key').replace('&', '%26')
                pem_url = awss3.presigned_url(
                    f'{text[1]}_{FQDN}/{FQDN}.pem').replace('&', '%26')
                tgbot.send_message(
                    f'Domain: {FQDN}\nkey: {key_url}\npem: {pem_url}\nLink expire in 1hr', chat_id)
            except:
                tgbot.send_message(
                    f'Downlaod failed!\nPlease input valid order or check /certstatus', chat_id)
        else:
            tgbot.send_message('Click Menu to see what you can do', chat_id)
    except:
        tgbot.send_message('Valid syntax: {/Command} {Arguments}', chat_id)

    return {"statusCode": 200}
