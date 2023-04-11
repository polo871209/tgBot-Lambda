import os
import secrets
from typing import List

import requests

user = os.environ['user']
mail_token = os.environ['mail_token']


def create_email(name: str, local_part: str, domain: str) -> List[str]:
    """
    create email api
    :param name: name of the email
    :param local_part: {local_part}@example.com
    :param domain: domain name of the email
    :return: email, password
    """
    auth = requests.auth.HTTPBasicAuth(user, mail_token)
    password = secrets.token_urlsafe(14)

    payload = {
        "name": name,
        "local_part": local_part,
        "password": password
    }

    response = requests.post(
        f'https://api.migadu.com/v1/domains/{domain}/mailboxes',
        auth=auth,
        data=payload
    ).json()

    if response['address'] == (email := f'{local_part}@{domain}'):
        return [email, password]
    return ['failed']

