import requests
import os

api_token = os.environ['api_token']  # env from lambda

def send_message(reply, chat_id):  # Send message
    url_req = f'https://api.telegram.org/bot{api_token}/sendMessage?chat_id={chat_id}&text={reply}'
    requests.get(url_req)


def send_copyable_message(reply, chat_id):  # Send MarkDown message
    url_req = f'https://api.telegram.org/bot{api_token}/sendMessage?chat_id={chat_id}&text=`{reply}`&parse_mode=MarkDown'
    requests.get(url_req)