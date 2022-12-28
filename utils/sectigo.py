from OpenSSL import crypto
import requests
import random
import string
import hashlib
import base64
import os

LOGINNAME = os.environ['loginName']
LOGINPASSWORD = os.environ['loginPassword']
APPLY_SSL_URL = 'https://secure.sectigo.com/products/!AutoApplySSL'
REVALIDATE_URL = 'https://secure.trust-provider.com/products/!AutoUpdateDCV'
COLLECTSSL_URL = 'https://secure.trust-provider.com/products/download/CollectSSL'
DV_SINGLE = '287'
DV_WILDCARD = '289'


class Sectigo:

    def __init__(self, common_name: str, days='370'):
        self.common_name = common_name
        self.days = days
        self.unique_value = self.gen_unique_value()
        self.params = {'loginName': LOGINNAME,
                       'LOGINPASSWORD': LOGINPASSWORD,
                       'days': self.days,
                       'uniqueValue': self.unique_value,
                       'isCustomerValidated': 'Y',
                       'serverSoftware': '-1',
                       'dcvMethod': 'CNAME_CSR_HASH'}

    def gen_key_csr(self, bit=2048):
        """Generate csr, key object.

        Args:
            bit (int): key size

        Returns:
            str: csr, key object
        """
        key = crypto.PKey()
        key.generate_key(crypto.TYPE_RSA, bit)
        csr = crypto.X509Req()
        csr.get_subject().CN = self.common_name
        csr.get_subject().C = 'TW'
        csr.get_subject().ST = 'Taipei'
        csr.get_subject().O = 'corp'
        csr.set_pubkey(key)
        csr.sign(key, 'SHA256')
        return key, csr

    def output_key_csr(self):
        """Output key, csr to file 

        Returns:
            bytes: private_key, certificate_signing_request
        """
        key, csr = self.gen_key_csr()
        private_key = crypto.dump_privatekey(crypto.FILETYPE_PEM, key)
        certificate_signing_request = crypto.dump_certificate_request(
            crypto.FILETYPE_PEM, csr)
        return private_key, certificate_signing_request

    def md5(self, csr: bytes):
        """sectigo md5 hash csr 

        Args:
            csr (str): csr in pem format

        Returns:
            str: sectigo md5 hash value
        """
        encode = self.csr_to_der(csr.decode("UTF-8"))
        md5_hash = hashlib.md5()
        md5_hash.update(encode)
        return md5_hash.hexdigest()

    def sha256(self, csr: bytes):
        """sectigo sha256 hash csr

        Args:
            csr (str): csr in pem formate

        Returns:
            str: sectigo sha256 hash value
        """
        encode = self.csr_to_der(csr.decode("UTF-8"))
        sha256_hash = hashlib.sha256()
        sha256_hash.update(encode)
        return sha256_hash.hexdigest()

    def validation(self, csr, response):
        """Calculate cname validation value

        Args:
            csr 
            response: api response

        Returns:
            _type_: _description_
        """
        host = f'_{self.md5(csr)}'
        sha_csr = self.sha256(csr)
        cname_value = f'{sha_csr[:32]}.{sha_csr[32:]}.{self.unique_value}.sectigo.com'
        order_number = response.splitlines()[1]
        validation = f"Order: {order_number}\nDomain: {self.common_name.replace('*.', '')}\nHost: {host}\nCname: {cname_value}"
        return validation, order_number

    def dv_single(self):
        """dv_single api 

        Returns:
            Success: validation, order_number, pkey, csr
            Failed: response
        """
        pkey, csr = self.output_key_csr()
        self.params['product'] = DV_SINGLE
        self.params['csr'] = csr
        response = requests.post(APPLY_SSL_URL, params=self.params).text
        if response.splitlines()[0] == '0':
            validation, order_number = self.validation(csr, response)
            return validation, order_number, pkey, csr
        else:
            return response

    def dv_wildcard(self):
        """dv_wildcard api 

        Returns:
            Success: validation, order_number, pkey, csr
            Failed: response
        """
        pkey, csr = self.output_key_csr()
        self.params['product'] = DV_WILDCARD
        self.params['csr'] = csr
        response = requests.post(APPLY_SSL_URL, params=self.params).text
        if response.splitlines()[0] == '0':
            validation, order_number = self.validation(csr, response)
            return validation, order_number, pkey, csr
        else:
            return response

    @staticmethod
    def csr_to_der(pem_cert: str):
        """Format csr from pem to der

        Args:
            pem_cert (str): csr in pem formate

        Returns:
            str: csr in der format
        """
        pem_header = "-----BEGIN CERTIFICATE REQUEST-----"
        pem_footer = "-----END CERTIFICATE REQUEST-----"
        d = str(pem_cert).strip()[len(pem_header):-len(pem_footer)]
        return base64.decodebytes(d.encode('ASCII', 'strict'))

    @staticmethod
    def revalidate(order_number: str):
        """Revalidate DNS record

        Args:
            order_number (str): order number

        Returns:
            Success: True, Failed: Flase
        """
        params = {'LOGINNAME': LOGINNAME,
                  'LOGINPASSWORD': LOGINPASSWORD,
                  'orderNumber': order_number,
                  'newMethod': 'CNAME_CSR_HASH'}
        if '0' in requests.post(REVALIDATE_URL, params=params).text:
            return True
        else:
            return False

    @staticmethod
    def certstatus(order_number: str):
        """Check certificate status

        Args:
            order_number (str): order number

        Returns:
            Issued: expiredate, Not Issued: False
        """
        params = {'LOGINNAME': LOGINNAME,
                  'LOGINPASSWORD': LOGINPASSWORD,
                  'orderNumber': order_number,
                  'queryType': '0',
                  'showValidityPeriod': 'Y'}
        response = requests.post(COLLECTSSL_URL, params=params).text
        try:
            return response.split()[2]
        except IndexError:
            return False

    @staticmethod
    def download_cert(order_number: str):
        """download certificate

        Args:
            order_number (str): order number

        Returns:
            Success: FQDN, cert
            Failed: False
        """
        params = {'LOGINNAME': LOGINNAME,
                  'LOGINPASSWORD': LOGINPASSWORD,
                  'orderNumber': order_number,
                  'queryType': '1',
                  'responseType': '3',
                  'showFQDN': 'Y'}
        response = requests.post(COLLECTSSL_URL, params=params).text
        try:
            fqdn = response.splitlines()[1]
        except IndexError:
            return False
        else:
            response_cert = response.split('\n', 2)[2][:-1]
            split_cert = response_cert.split('-----END CERTIFICATE-----')[::-1]
            cert_list = [s + '-----END CERTIFICATE-----' for s in split_cert][1:]
            cert_list.insert(3, '\n')
            cert = ''.join(cert_list)[1:]
            return fqdn, cert

    @staticmethod
    def pem_to_pfx(pkey, pem):
        """PEM format to PFX format

        Args:
            pkey (str): private key
            pem (str): pem

        Returns:
        passphrase,  pfx
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
    def gen_unique_value(i=10):
        """Generate unique value a-z, A-Z, 0-9

        Args:
            i (int, optional): how many indexes

        Returns:
            str: random str
        """
        return ''.join(random.choice(string.ascii_letters + string.digits) for _ in range(i))
