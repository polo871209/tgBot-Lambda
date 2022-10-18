import requests
import hashlib


def request_api(first5_char: str):
    """pwendpassword check api

    Args:
        first5_char (str): _description_

    Returns:
        str: api response
    """
    url = 'https://api.pwnedpasswords.com/range/' + first5_char
    response = requests.get(url).text
    return response  # Response in text


def sha1_hash(password: str):
    """sha1_hash

    Args:
        password (str): any password

    Returns:
        str: hashed password
    """
    hashed_string = hashlib.sha1(password.encode('utf-8')).hexdigest().upper()
    return hashed_string


def split_res(response: str):
    split_res = (line.split(':') for line in response.splitlines())
    return split_res


def main(password: str):
    """pwen checker api __main__

    Args:
        password (str): any password

    Returns:
        str: pwend check result
    """
    hashed_password = sha1_hash(password)
    first5_char, tail = hashed_password[:5], hashed_password[5:]
    response = request_api(first5_char)  # Request using first 5 hash
    splited_response = split_res(response)
    for h, count in splited_response:
        if h == tail:
            return f'\'{password}\'  Had been hacked {count} times, you need a new password.'
    return f'\'{password}\'  Had not been hacked, good job!'
