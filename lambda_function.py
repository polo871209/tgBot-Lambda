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
            awss3.data(f'{order_number}_{text[1]}/', f'{text[1]}.key', pkey)
            awss3.data(f'{order_number}_{text[1]}/', f'{text[1]}.csr', csr)
        elif 'revalidate' in text[0]:
            response = sectigo.revalidate(text[1])
            if 'errorCode=0' in response:
                tgbot.send_message(
                    f'Success!\nUse: /certstatus to check status.', chat_id)
            else:
                tgbot.send_message(
                    'Please enter valid order number, or order already issued.', chat_id)
        elif 'certstatus' in text[0]:
            response = sectigo.certstatus(text[1])
            try:
                tgbot.send_message(
                    f'Order: {text[1]} \nStatus: Issued\nExpire on: {response.split()[2]}', chat_id)
            except:
                tgbot.send_message(
                    f'Order: {text[1]} \nStatus: Not Issued\nTry /revalidate or check your DNS record.', chat_id)
        elif 'downloadcert' in text[0]:
            try:
                FQDN, cert = sectigo.download_cert(text[1])
                awss3.data(f'{text[1]}_{FQDN}/', f'{FQDN}.pem', cert)
                tgbot.send_message('Downlaod success!', chat_id)
            except:
                tgbot.send_message(
                    f'Downlaod failed!\nPlease input valid order or check /certstatus', chat_id)
        else:
            tgbot.send_message('Click Menu to see what you can do', chat_id)
    except:
        tgbot.send_message('Valid syntax: {/Command} {Arguments}', chat_id)

    return {"statusCode": 200}
