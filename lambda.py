import requests
import hashlib
import json
import os

api_token = os.environ['api_token']  # env from lambda


def request_api(first5_char):  # /pwnedcheck api
    url = 'https://api.pwnedpasswords.com/range/' + first5_char
    res = requests.get(url)
    return res.text  # Response in text


def sha1_hash(password):  # /pwnedcheck hash sha 1
    hashed_string = hashlib.sha1(password.encode('utf-8')).hexdigest().upper()
    return hashed_string


def split_res(response):  # /pwnedcheck split API response in to hash and count
    split_res = (line.split(':') for line in response.splitlines())
    return split_res


def pwnedcheck_main(password):  # /pwnedcheck main
    hashed_password = sha1_hash(password)
    first5_char, tail = hashed_password[:5], hashed_password[5:]
    response = request_api(first5_char)  # Request using first 5 hash
    splited_response = split_res(response)
    for h, count in splited_response:
        if h == tail:
            return f'\'{password}\'  Had been hacked {count} times, you need a new password.'
    return f'\'{password}\'  Had not been hacked, good job!'


def send_message(reply, chat_id):  # Send message to bot
    url_req = "https://api.telegram.org/bot" + api_token + \
        "/sendMessage" + "?chat_id=" + chat_id + "&text=" + reply
    requests.get(url_req)


def lambda_handler(event, context):

    try:
        message = json.loads(event['body'])  # parse out query string param
        chat_id = str(message['message']['chat']['id'])
        text = message['message']['text'].split()
        command, argument = text[0], text[1]
        if 'pwnedcheck' in command:
            send_message(pwnedcheck_main(argument), chat_id)
        else:
            send_message('Click Menu to see what you can do', chat_id)
    except:
        send_message('Valid syntax: {Command} {Argument}', chat_id)

    return {"statusCode": 200}
