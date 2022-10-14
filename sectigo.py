from OpenSSL import crypto
import urllib.parse
import requests
import random
import string
import hashlib
import base64
import os

# Sectigo login credential
loginName = os.environ['loginName']
loginPassword = os.environ['loginPassword']


def gen_private_key(bit=2048):
    '''Generate RSA key. Default 2048 bit'''
    key = crypto.PKey()
    key.generate_key(crypto.TYPE_RSA, bit)
    return key


def gen_csr(commonName):  # Generate CSR object
    csr = crypto.X509Req()
    csr.get_subject().C = 'TW'
    csr.get_subject().ST = 'Taipei'
    csr.get_subject().O = 'corp'
    csr.get_subject().CN = commonName
    key = gen_private_key()  # generate key object
    csr.set_pubkey(key)
    csr.sign(key, 'SHA256')
    return csr, key


def output_key_csr(commonName):
    '''Out put csr, key file. commonName = domain'''
    csr, key = gen_csr(commonName)
    private_key = crypto.dump_privatekey(crypto.FILETYPE_PEM, key)
    certificate_signing_request = crypto.dump_certificate_request(
        crypto.FILETYPE_PEM, csr)
    return private_key, certificate_signing_request


def PEM_to_DER_csr(pem_cert):
    pem_header = "-----BEGIN CERTIFICATE REQUEST-----"
    pem_footer = "-----END CERTIFICATE REQUEST-----"
    d = str(pem_cert).strip()[len(pem_header):-len(pem_footer)]
    return base64.decodebytes(d.encode('ASCII', 'strict'))


def md5(csr):  # hash
    encode = PEM_to_DER_csr(csr.decode("UTF-8"))
    md5_hash = hashlib.md5()
    md5_hash.update(encode)
    return md5_hash.hexdigest()


def sha256(csr):  # hash
    encode = PEM_to_DER_csr(csr.decode("UTF-8"))
    sha256_hash = hashlib.sha256()
    sha256_hash.update(encode)
    return sha256_hash.hexdigest()


def gen_unique_value():  # Generate uniqueValue
    uniqueValue = ''.join(random.choice(
        string.ascii_letters + string.digits)for x in range(10))
    return uniqueValue


def sectigo_dv_api(product, days, encoded_csr):
    uniqueValue = gen_unique_value()
    url = f'https://secure.sectigo.com/products/!AutoApplySSL?loginName={loginName}&loginPassword={loginPassword}&days={days}&product={product}&csr={encoded_csr}&isCustomerValidated=Y&serverSoftware=-1&dcvMethod=CNAME_CSR_HASH&uniqueValue=GAIA{uniqueValue}'
    payload = {}  # print(url)
    headers = {}
    response = requests.request("POST", url, headers=headers, data=payload)
    return response.text, f'GAIA{uniqueValue}'


def apply_ssl(product, commonName, days):
    if product == 'dvsingle':
        product = os.environ['dvsingle']
    pkey, csr = output_key_csr(commonName)
    encoded_csr = urllib.parse.quote(csr)  # url encode
    response, uniqueValue = sectigo_dv_api(product, days, encoded_csr)
    if response.splitlines()[0] == '0':
        host = f'_{md5(csr)}.'
        sha_csr = sha256(csr)
        cname_value = f'{sha_csr[:32]}.{sha_csr[32:]}.{uniqueValue}.sectigo.com.'
        order_number = response.splitlines()[1]
        validation = f'''Order: {order_number}\nDomain: {commonName}\nHost: {host}\nCnameValue: {cname_value}'''
        return validation, order_number, pkey, csr
    else:
        return f'Error:{response}Please contact admin'


payload = {}
headers = {}


def revalidate(orderNumber='', newMethod='CNAME_CSR_HASH'):
    url = f"https://secure.trust-provider.com/products/!AutoUpdateDCV?loginName={loginName}&loginPassword={loginPassword}&orderNumber={orderNumber}&newMethod={newMethod}"
    response = requests.request("POST", url, headers=headers, data=payload)
    return response.text


def certstatus(orderNumber):
    url = f'https://secure.trust-provider.com/products/download/CollectSSL?loginName={loginName}&loginPassword={loginPassword}&orderNumber={orderNumber}&queryType=0&showValidityPeriod=Y'
    return requests.request("POST", url, headers=headers, data=payload).text


def download_cert(orderNumber):
    url = f'https://secure.trust-provider.com/products/download/CollectSSL?loginName={loginName}&loginPassword={loginPassword}&orderNumber={orderNumber}&queryType=1&responseType=3&showFQDN=Y'
    response = requests.request(
        "POST", url, headers=headers, data=payload).text
    FQDN = response.splitlines()[1]
    cert = response.split('\n', 2)[2][:-1]
    return FQDN, cert
