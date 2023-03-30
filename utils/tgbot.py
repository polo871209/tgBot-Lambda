import os

import requests

API_TOKEN = os.environ['api_token']


class Tgbot:

    def __init__(self, chat_id):
        self.chat_id = chat_id

    def send_message(self, message: str) -> None:
        """
        send message to chat
        :param message:
        :return:
        """
        url_req = f'https://api.telegram.org/bot{API_TOKEN}/sendMessage'
        params = {'chat_id': self.chat_id,
                  'text': message}
        requests.get(url_req, params=params)
