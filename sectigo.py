from OpenSSL import crypto
import requests
import random
import string
import hashlib
import base64
import os


loginName = os.environ['loginName']
loginPassword = os.environ['loginPassword']


def gen_private_key(bit=2048):
    """Generate Rsa key

    Args:
        bit (int, optional): Defaults to 2048.

    Returns:
        str: Rsa key
    """
    key = crypto.PKey()
    key.generate_key(crypto.TYPE_RSA, bit)
    return key


def gen_csr(commonName: str):
    """Generate csr object. This will also generate rsa key using gen_private_key function

    Args:
        commonName (str): Domain name

    Returns:
        str: csr object, key object
    """
    csr = crypto.X509Req()
    csr.get_subject().C = 'TW'
    csr.get_subject().ST = 'Taipei'
    csr.get_subject().O = 'corp'
    csr.get_subject().CN = commonName
    key = gen_private_key()
    csr.set_pubkey(key)
    csr.sign(key, 'SHA256')
    return key, csr


def output_key_csr(commonName: str):
    """Output key, csr to file 

    Args:
        commonName (str): Domain name

    Returns:
        str: private_key, certificate_signing_request
    """
    key, csr = gen_csr(commonName)
    private_key = crypto.dump_privatekey(crypto.FILETYPE_PEM, key)
    certificate_signing_request = crypto.dump_certificate_request(
        crypto.FILETYPE_PEM, csr)
    return private_key, certificate_signing_request


def PEM_to_DER_csr(pem_cert: str):
    """Format csr from pem to der

    Args:
        pem_cert (str): csr in pem fomat

    Returns:
        str: csr in der format
    """
    pem_header = "-----BEGIN CERTIFICATE REQUEST-----"
    pem_footer = "-----END CERTIFICATE REQUEST-----"
    d = str(pem_cert).strip()[len(pem_header):-len(pem_footer)]
    return base64.decodebytes(d.encode('ASCII', 'strict'))


def md5(csr: str):
    """sectigo md5 hash csr 

    Args:
        csr (str): csr in pem format

    Returns:
        str: sectigo md5 hash value
    """
    encode = PEM_to_DER_csr(csr.decode("UTF-8"))
    md5_hash = hashlib.md5()
    md5_hash.update(encode)
    return md5_hash.hexdigest()


def sha256(csr: str):
    """sectigo sha256 hash csr

    Args:
        csr (str): csr in pem formate

    Returns:
        str: sectigo sha256 hash value
    """
    encode = PEM_to_DER_csr(csr.decode("UTF-8"))
    sha256_hash = hashlib.sha256()
    sha256_hash.update(encode)
    return sha256_hash.hexdigest()


def gen_uniquevalue(i=10):
    """Generate unique value a-z, A-Z, 0-9

    Args:
        i (int, optional): how many indexs

    Returns:
        str: random str
    """
    uniqueValue = ''.join(random.choice(
        string.ascii_letters + string.digits)for x in range(i))
    return uniqueValue


def dv(product: str, days: str, csr: str):
    """sectigo dv api call

    Args:
        product (str): product number
        days (str): days between 366-395
        csr (str): csr 

    Returns:
        str: response, uniqueValue
    """
    uniqueValue = f'GAIA{gen_uniquevalue()}'
    url = f'https://secure.sectigo.com/products/!AutoApplySSL'
    params = {'loginName': loginName,
              'loginPassword': loginPassword,
              'days': days,
              'product': product,
              'csr': csr,
              'uniqueValue': uniqueValue,
              'isCustomerValidated': 'Y',
              'serverSoftware': '-1',
              'dcvMethod': 'CNAME_CSR_HASH'}
    response = requests.post(url, params=params).text
    return response, uniqueValue


def apply_ssl(product: str, commonName: str, days: str):
    """apply for ssl __main__.This include all the function above

    Args:
        product (str): sectigo product number
        commonName (str): Domain name
        days (str): days between 366-395

    Returns:
        str: DNS validation value, order_number, private key, csr
    """
    if product == 'dvsingle':
        product = os.environ['dvsingle']
    elif product == 'dvwildcard':
        product = os.environ['dvwildcard']
    pkey, csr = output_key_csr(commonName)
    response, uniqueValue = dv(product, days, csr)
    if response.splitlines()[0] == '0':
        host = f'_{md5(csr)}.'
        sha_csr = sha256(csr)
        cname_value = f'{sha_csr[:32]}.{sha_csr[32:]}.{uniqueValue}.sectigo.com.'
        order_number = response.splitlines()[1]
        validation = f'Order: {order_number}\nDomain: {commonName}\nHost: {host}\nCnameValue: {cname_value}'
        return validation, order_number, pkey, csr
    else:
        return f'Error:{response}Please contact admin'


def revalidate(orderNumber: str, newMethod='CNAME_CSR_HASH'):
    """Revalidaying DNS record

    Args:
        orderNumber (str): order number
        newMethod (str, optional): EMAIL, HTTP_CSR_HASH, HTTPS_CSR_HASH, CNAME_CSR_HASH 

    Returns:
        str: api response 
    """
    url = 'https://secure.trust-provider.com/products/!AutoUpdateDCV'
    params = {'loginName': loginName,
              'loginPassword': loginPassword,
              'orderNumber': orderNumber,
              'newMethod': newMethod}
    response = requests.post(url, params=params).text
    return response


def certstatus(orderNumber: str):
    """Check certificate status

    Args:
        orderNumber (str): order number

    Returns:
        str: expiredate, 'Not Issued' if certificate not issued
    """
    url = f'https://secure.trust-provider.com/products/download/CollectSSL'
    params = {'loginName': loginName,
              'loginPassword': loginPassword,
              'orderNumber': orderNumber,
              'queryType': '0',
              'showValidityPeriod': 'Y'}
    response = requests.post(url, params=params).text
    status, expiredate = response.split()[0], response.split()[2]
    if status == '1':
        return expiredate
    else:
        return 'Not Issued'


def download_cert(orderNumber: str):
    """download certificate

    Args:
        orderNumber (str): order number

    Returns:
        str: FQDN, certificate
    """
    url = f'https://secure.trust-provider.com/products/download/CollectSSL'
    params = {'loginName': loginName,
              'loginPassword': loginPassword,
              'orderNumber': orderNumber,
              'queryType': '1',
              'responseType': '3',
              'showFQDN': 'Y'}
    response = requests.post(url, params=params).text
    FQDN = response.splitlines()[1]
    response_cert = response.split('\n', 2)[2][:-1]
    split_cert = response_cert.split('-----END CERTIFICATE-----')[::-1]
    cert_list = [s + '-----END CERTIFICATE-----' for s in split_cert][1:]
    cert = ''.join(cert_list)[1:]
    return FQDN, cert
