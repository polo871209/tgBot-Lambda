import boto3
import os

# AWS variable
access_key_id = os.environ['access_key_id']
secret_access_key = os.environ['secret_access_key']
bucket_name = 'po-lambda'


def data(folder_path, file_name, data):
    '''Send data to S3. folder_path must end with /'''
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
