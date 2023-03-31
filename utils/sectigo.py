import base64
import hashlib
import os
import random
import string
from typing import Tuple

import requests
from OpenSSL import crypto

LOGIN_NAME = os.environ['loginName']
LOGIN_PASSWORD = os.environ['loginPassword']
APPLY_SSL_ENDPOINT = 'https://secure.sectigo.com/products/!AutoApplySSL'
REVALIDATE_ENDPOINT = 'https://secure.trust-provider.com/products/!AutoUpdateDCV'
COLLECT_SSL_ENDPOINT = 'https://secure.trust-provider.com/products/download/CollectSSL'
DV_SINGLE = '287'
DV_WILDCARD = '289'


class Sectigo:

    def __init__(self, common_name: str, days='370'):
        self.common_name = common_name
        self.days = days
        self.unique_value = self.gen_unique_value()
        self.params = {'loginName': LOGIN_NAME,
                       'loginPassword': LOGIN_PASSWORD,
                       'days': self.days,
                       'uniqueValue': self.unique_value,
                       'isCustomerValidated': 'Y',
                       'serverSoftware': '-1',
                       'dcvMethod': 'CNAME_CSR_HASH'}

    def gen_key_csr(self) -> Tuple[bytes, bytes]:
        """
        Generate csr, key object
        :return: key, csr
        """
        key = crypto.PKey()
        key.generate_key(crypto.TYPE_RSA, 2048)
        csr = crypto.X509Req()
        csr.get_subject().CN = self.common_name
        csr.get_subject().C = 'TW'
        csr.get_subject().ST = 'Taipei'
        csr.get_subject().O = 'corp'
        csr.set_pubkey(key)
        csr.sign(key, 'SHA256')
        # turn crypto object into byte
        key_bytes = crypto.dump_privatekey(crypto.FILETYPE_PEM, key)
        csr_bytes = crypto.dump_certificate_request(crypto.FILETYPE_PEM, csr)
        return key_bytes, csr_bytes

    @staticmethod
    def csr_to_der(pem_cert: str) -> bytes:
        """
        format csr from pem to der
        :param pem_cert:
        :return: csr in der format
        """
        pem_header = "-----BEGIN CERTIFICATE REQUEST-----"
        pem_footer = "-----END CERTIFICATE REQUEST-----"
        d = str(pem_cert).strip()[len(pem_header):-len(pem_footer)]
        return base64.decodebytes(d.encode('ASCII', 'strict'))

    def md5(self, csr: bytes) -> str:
        """
        sectigo md5 hash csr
        :return: md5 hash
        """
        md5_hash = hashlib.md5()
        md5_hash.update(self.csr_to_der(csr.decode("UTF-8")))
        return md5_hash.hexdigest()

    def sha256(self, csr: bytes) -> str:
        """
        sectigo sha256 hash csr
        :return: sha256 hash
        """
        sha256_hash = hashlib.sha256()
        sha256_hash.update(self.csr_to_der(csr.decode("UTF-8")))
        return sha256_hash.hexdigest()

    def validation(self, csr: bytes, response: str) -> Tuple[str, str]:
        """
        calculate cname validation value
        :param csr:
        :param response: api response
        :return: validation, order_number
        """
        host = f'_{self.md5(csr)}'
        sha_csr = self.sha256(csr)
        cname_value = f'{sha_csr[:32]}.{sha_csr[32:]}.{self.unique_value}.sectigo.com'
        order_number = response.splitlines()[1]
        validation = f"Order: {order_number}\nDomain: {self.common_name.replace('*.', '')}\nHost: {host}\nCname: {cname_value}"
        return validation, order_number

    def dv_single(self) -> Tuple[str, str, bytes, bytes]:
        """
        dv_single api
        :return:
            success: validation, order_number, private_key, csr
            failed: pass
        """
        pkey, csr = self.gen_key_csr()
        self.params['product'] = DV_SINGLE
        self.params['csr'] = csr
        response = requests.post(APPLY_SSL_ENDPOINT, params=self.params).text
        if response.splitlines()[0] == '0':
            validation, order_number = self.validation(csr, response)
            return validation, order_number, pkey, csr
        else:
            pass

    def dv_wildcard(self) -> Tuple[str, str, bytes, bytes]:
        """
        dv_wildcard api
        :return:
            success: validation, order_number, private_key, csr
            failed: pass
        """
        pkey, csr = self.gen_key_csr()
        self.params['product'] = DV_WILDCARD
        self.params['csr'] = csr
        response = requests.post(APPLY_SSL_ENDPOINT, params=self.params).text
        if response.splitlines()[0] == '0':
            validation, order_number = self.validation(csr, response)
            return validation, order_number, pkey, csr
        else:
            pass

    @staticmethod
    def revalidate(order_number: str) -> bool:
        """
        revalidate DNS record
        :param order_number:
        :return: result
        """
        params = {'loginName': LOGIN_NAME,
                  'loginPassword': LOGIN_PASSWORD,
                  'orderNumber': order_number,
                  'newMethod': 'CNAME_CSR_HASH'}
        if '0' in requests.post(REVALIDATE_ENDPOINT, params=params).text:
            return True
        return False

    @staticmethod
    def cert_status(order_number: str) -> str:
        """
        check certificate status
        :param order_number:
        :return: expire date
        """
        params = {'loginName': LOGIN_NAME,
                  'loginPassword': LOGIN_PASSWORD,
                  'orderNumber': order_number,
                  'queryType': '0',
                  'showValidityPeriod': 'Y'}
        response = requests.post(COLLECT_SSL_ENDPOINT, params=params).text
        try:
            return response.split()[2]
        except IndexError:
            pass

    @staticmethod
    def download_cert(order_number: str) -> Tuple[str, str]:
        """
        download certificate
        :param order_number:
        :return: fqdn, cert
        """
        params = {'loginName': LOGIN_NAME,
                  'loginPassword': LOGIN_PASSWORD,
                  'orderNumber': order_number,
                  'queryType': '1',
                  'responseType': '3',
                  'showFQDN': 'Y'}
        response = requests.post(COLLECT_SSL_ENDPOINT, params=params).text
        try:
            fqdn = response.splitlines()[1]
        except IndexError:
            pass
        else:
            response_cert = response.split('\n', 2)[2][:-1]
            # order certificate chains
            split_cert = response_cert.split('-----END CERTIFICATE-----')[::-1]
            cert_list = [s + '-----END CERTIFICATE-----' for s in split_cert][1:]
            cert_list.insert(3, '\n')
            cert = ''.join(cert_list)[1:]
            return fqdn, cert

    @staticmethod
    def pem_to_pfx(pkey: str, pem: str) -> Tuple[str, bytes]:
        """
        PEM format to PFX format
        :param pkey: private key
        :param pem:
        :return: passphrase,  pfx
        """
        key = crypto.load_privatekey(crypto.FILETYPE_PEM, pkey)
        cert = crypto.load_certificate(crypto.FILETYPE_PEM, pem.encode('ASCII'))
        pkcs = crypto.PKCS12()
        pkcs.set_privatekey(key)
        pkcs.set_certificate(cert)
        passphrase = Sectigo.gen_unique_value()
        pfx = pkcs.export(passphrase=passphrase.encode('ASCII'))
        return passphrase, pfx

    @staticmethod
    def gen_unique_value() -> str:
        """
        generate unique value a-z, A-Z, 0-9
        :return:
        """
        return ''.join(random.choice(string.ascii_letters + string.digits) for _ in range(10))
