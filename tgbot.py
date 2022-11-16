import requests
import os


API_TOKEN = os.environ['api_token']


class Tgbot():

    def __init__(self, chat_id):
        self.chat_id = chat_id

    def send_message(self, message: str):
        """send message to chat

        Args:
            message (str): message
        """
        url_req = f'https://api.telegram.org/bot{API_TOKEN}/sendMessage'
        params = {'chat_id': self.chat_id,
                  'text': message}
        requests.get(url_req, params=params)
