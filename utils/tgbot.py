import os

import requests

API_TOKEN = os.environ['api_token']


class Tgbot:

    def __init__(self, chat_id: str) -> None:
        self.chat_id = chat_id

    def send_message(self, message: str) -> None:
        """
        send message to chat
        :param message: message to sent
        """
        url_req = f'https://api.telegram.org/bot{API_TOKEN}/sendMessage'
        params = {
            'chat_id': self.chat_id,
            'text': message
        }
        requests.get(url_req, params=params)

    @staticmethod
    def get_file_path(file_id: str) -> str:
        """
        file path required for download file
        :param file_id:
        :return: file path
        """
        params = {
            'file_id': file_id
        }

        response = requests.get(
            f'https://api.telegram.org/bot{API_TOKEN}/getFile', params=params
        ).json()

        return response['result']['file_path']

    def download_file(self, file_id: str) -> str:
        """
        read file content with file_id
        :param file_id:
        :return: file content
        """
        file_path = self.get_file_path(file_id)
        params = {
            'file_id': file_id
        }

        response = requests.get(
            f'https://api.telegram.org/file/bot{API_TOKEN}/{file_path}',
            params=params
        ).text

        return response