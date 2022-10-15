from botocore.exceptions import ClientError
import boto3
import os

# AWS variable
access_key_id = os.environ['access_key_id']
secret_access_key = os.environ['secret_access_key']
bucket_name = 'po-lambda'


def upload_data(folder_path, file_name, data):
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


def presigned_url(object_key, expiry=3600):

    client = boto3.client("s3", aws_access_key_id=access_key_id, aws_secret_access_key=secret_access_key)
    try:
        response = client.generate_presigned_url(
            'get_object', Params={'Bucket': bucket_name, 'Key': object_key}, ExpiresIn=expiry)
        return response
    except ClientError as err:
        print(err)