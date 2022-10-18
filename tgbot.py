import requests
import os

api_token = os.environ['api_token']


def send_message(message: str, chat_id: str):
    """use tg bot to send message

    Args:
        message (str): message
        chat_id (str): chat_id
    """
    url_req = f'https://api.telegram.org/bot{api_token}/sendMessage'
    params = {'chat_id': chat_id,
              'text': message}
    requests.get(url_req, params=params)
