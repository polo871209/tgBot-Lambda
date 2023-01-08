import base64
import hashlib
import os
import random
import string
from typing import Optional

import requests
from OpenSSL import crypto
from dotenv import load_dotenv

load_dotenv()

LOGIN_NAME = os.environ['LOGIN_NAME']
LOGIN_PASSWORD = os.environ['LOGIN_PASSWORD']
APPLY_SSL_ENDPOINT = 'https://secure.sectigo.com/products/!AutoApplySSL'
REVALIDATE_ENDPOINT = 'https://secure.trust-provider.com/products/!AutoUpdateDCV'
COLLECT_SSL_ENDPOINT = 'https://secure.trust-provider.com/products/download/CollectSSL'
DV_SINGLE = '287'
DV_WILDCARD = '289'


class Sectigo:

    def __init__(self, domain_name: str, days: Optional[str] = '366'):
        self.domain_name = domain_name
        self.days = days
        self.order_number = ''
        self.unique_value = 'gaia'

    def apply_ssl(self, product: str) -> any:
        """
        apply ssl
        :param product: single or wildcard
        :return: dns validation(str), key(byte), csr(byte)
        """
        if product == 'single':
            product = DV_SINGLE
        elif product == 'wildcard':
            product = DV_WILDCARD
        try:
            key, csr = self._generate_key_csr()
            self._ssl_request(product, csr)
            return self._dns_validation(csr), key, csr
        except requests.RequestException:
            return '請求失敗，請重新嘗試'

    @staticmethod
    def revalidate(order_number: str):
        """
        perform DCV check
        :param order_number
        """
        params = {
            'loginName': LOGIN_NAME,
            'loginPassword': LOGIN_PASSWORD,
            'orderNumber': order_number,
            'newMethod': 'CNAME_CSR_HASH'
        }
        response = requests.post(REVALIDATE_ENDPOINT, params=params).text
        if 'errorCode=0' or 'errorCode=-4' in response:
            return Sectigo.status(order_number)
        raise requests.RequestException

    @staticmethod
    def status(order_number: str) -> str:
        """
        order status
        :param order_number:
        :return: order status
        """
        params = {
            'loginName': LOGIN_NAME,
            'loginPassword': LOGIN_PASSWORD,
            'orderNumber': order_number,
            'queryType': '0',
            'showValidityPeriod': 'Y'
        }
        response = requests.post(COLLECT_SSL_ENDPOINT, params=params).text
        if response == '0':
            return f'Order: {order_number}\n狀態: 未簽發'
        elif response.split()[0] == '1':
            return f'Order: {order_number}\n狀態: 已簽發\n過期日: {response.split()[2]}'
        raise requests.RequestException

    @staticmethod
    def download(order_number: str) -> any:
        """
        download certificate
        :param order_number
        :return: false if not issued
        :return: domain, cert
        """
        params = {
            'loginName': LOGIN_NAME,
            'loginPassword': LOGIN_PASSWORD,
            'orderNumber': order_number,
            'queryType': '1',
            'responseType': '3',
            'showFQDN': 'Y'
        }
        response = requests.post(COLLECT_SSL_ENDPOINT, params=params).text
        if response == '0':
            return False
        elif response.split()[0] == '2':
            unordered_cert = response.split('\n', 2)[2][:-1]
            split_cert = unordered_cert.split('-----END CERTIFICATE-----')[::-1]
            cert_list = [s + '-----END CERTIFICATE-----' for s in split_cert][1:]
            cert_list.insert(3, '\n')
            cert = ''.join(cert_list)[1:]
            return response.split()[1], cert
        raise requests.RequestException

    @staticmethod
    def pem_to_pfx(key: str, pem: str) -> tuple:
        pkcs12 = crypto.PKCS12()
        pkcs12.set_privatekey(crypto.load_privatekey(crypto.FILETYPE_PEM, key))
        pkcs12.set_certificate(crypto.load_certificate(crypto.FILETYPE_PEM, pem.encode('ASCII')))
        passphrase = Sectigo._gen_unique_value()
        pfx = pkcs12.export(passphrase=passphrase.encode('ASCII'))
        return passphrase, pfx

    def _generate_key_csr(self, bit: Optional[int] = 2048) -> tuple:
        """
        :param bit: key length
        :return: [key: bytes, csr: bytes]
        """
        key_object = crypto.PKey()
        key_object.generate_key(crypto.TYPE_RSA, bit)
        key = crypto.dump_privatekey(crypto.FILETYPE_PEM, key_object)

        csr_object = crypto.X509Req()
        csr_object.get_subject().commonName = self.domain_name
        csr_object.set_pubkey(key_object)
        csr_object.sign(key_object, 'SHA256')
        csr = crypto.dump_certificate_request(crypto.FILETYPE_PEM, csr_object)

        return key, csr

    def _ssl_request(self, product: str, csr: bytes) -> None:
        """
        Sectigo ssl request
        :param product: product number
        :param csr
        """
        params = {
            'loginName': LOGIN_NAME,
            'loginPassword': LOGIN_PASSWORD,
            'product': product,
            'csr': csr,
            'days': self.days,
            'uniqueValue': self.unique_value,
            'isCustomerValidated': 'Y',
            'serverSoftware': '-1',
            'dcvMethod': 'CNAME_CSR_HASH'
        }
        response = requests.post(APPLY_SSL_ENDPOINT, params=params).text
        if response.splitlines()[0] == '0':
            self.order_number = response.splitlines()[1]
        else:
            raise requests.RequestException

    @staticmethod
    def _csr_to_der(pem_cert: str):
        """
        csr to der format
        :param pem_cert:
        :return:
        """
        pem_header = "-----BEGIN CERTIFICATE REQUEST-----"
        pem_footer = "-----END CERTIFICATE REQUEST-----"
        d = str(pem_cert).strip()[len(pem_header):-len(pem_footer)]
        return base64.decodebytes(d.encode('ASCII', 'strict'))

    def _md5_hash(self, csr: bytes) -> str:
        """
        csr md5 hash
        :param csr
        :return: md5 hash string
        """
        encode = self._csr_to_der(csr.decode("UTF-8"))
        md5_hash = hashlib.md5()
        md5_hash.update(encode)
        return md5_hash.hexdigest()

    def _sha256(self, csr: bytes) -> str:
        """
        csr sha256 hash
        :param csr
        :return: sha256 hash string
        """
        encode = self._csr_to_der(csr.decode("UTF-8"))
        sha256_hash = hashlib.sha256()
        sha256_hash.update(encode)
        return sha256_hash.hexdigest()

    def _dns_validation(self, csr: bytes) -> str:
        """
        output from csr
        :param csr
        :return: dns validation str
        """
        host = f'_{self._md5_hash(csr)}'
        sha_csr = self._sha256(csr)
        cname_value = f'{sha_csr[:32]}.{sha_csr[32:]}.{self.unique_value}.sectigo.com'
        return f"訂單編號: {self.order_number}\n域名: {self.domain_name.replace('*.', '')}\n" \
               f"主機: {host}\nCNAME: {cname_value}"

    @staticmethod
    def _gen_unique_value(i: Optional[int] = 10):
        """
        generate unique value
        :param i: how many index
        :return: random str of number and alphabet
        """
        return ''.join(random.choice(string.ascii_letters + string.digits) for _ in range(i))

# ssl = Sectigo("abc.com")
# print(ssl.apply_ssl(DV_SINGLE))
# print(Sectigo.revalidate("1378973013"))
# print(Sectigo.revalidate("1375237405"))
