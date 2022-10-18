# aws S3 functions
from botocore.exceptions import ClientError
import boto3
import os

# AWS cerdential
access_key_id = os.environ['access_key_id']
secret_access_key = os.environ['secret_access_key']
bucket_name = 'po-lambda'


def upload_data(folder_path: str, file_name: str, data: str):
    """upload data to S3 using access key

    Args:
        folder_path (str): Path end with /.
        file_name (str): File name.
        data (str): Data in the file.

    Returns:
        str: result
    """
    session = boto3.Session(aws_access_key_id=access_key_id,
                            aws_secret_access_key=secret_access_key)
    s3 = session.resource('s3')  # Create S3 session.
    path = f'{folder_path}{file_name}'
    object = s3.Object(bucket_name, path)
    result = object.put(Body=data)
    res = result.get('ResponseMetadata')
    if res.get('HTTPStatusCode') == 200:
        return 'Done'
    else:
        return 'Failed'


def presigned_url(file_path: str, expiry=3600):
    """generate S3 presigned url using access key

    Args:
        file_path (str): File path / file name.
        expiry (int, optional): Defaults to 3600.

    Returns:
        _type_: _description_
    """

    client = boto3.client("s3", aws_access_key_id=access_key_id,
                          aws_secret_access_key=secret_access_key)
    try:
        response = client.generate_presigned_url(
            'get_object', Params={'Bucket': bucket_name, 'Key': file_path}, ExpiresIn=expiry)
        return response
    except ClientError as err:
        return err
