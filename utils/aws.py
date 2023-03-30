import os
import shutil

import boto3


class S3:
    def __init__(self, bucket_name: str):
        # setting up sessions
        self.client = boto3.client('s3')
        self.s3 = boto3.resource('s3')
        self.bucket = bucket_name

    def upload_data(self, path: str, data: str) -> bool:
        """
        upload data to S3
        :param path: file path(key)
        :param data: data in the file
        :return: status in boolean
        """
        result = self.client.put_object(Body=data, Bucket=self.bucket, Key=path)
        res = result.get('ResponseMetadata')
        if res.get('HTTPStatusCode') == 200:  # check if success
            return True
        else:
            return False

    def get_object(self, path: str) -> str:
        """
        get object from s3
        :param path: file path(key)
        :return: file data
        """
        obj = self.s3.Object(self.bucket, path)
        return obj.get()['Body'].read().decode('utf-8')

    def zip_folder(self, dir_name: str, output_filename: str) -> None:
        """
        zip s3 dir and upload back to bucket
        utilizes lambda /tmp/ dir to zip file and upload back to bucket
        :param dir_name: s3 directory(key) name
        :param output_filename: file path+name **without '.zip'
        """
        bucket = self.s3.Bucket(self.bucket)
        if not os.path.exists(f'/tmp/{dir_name}'):
            os.makedirs(f'/tmp/{dir_name}')
        for f in bucket.objects.filter(Prefix=dir_name):  # list all the s3 object under prefix
            if '.zip' not in f.key:  # if never zip, then do it
                bucket.download_file(f.key, f'/tmp/{f.key}')
        shutil.make_archive(f'/tmp/{dir_name}', 'zip', '/tmp', dir_name)  # zip
        self.s3.Bucket(self.bucket).upload_file(f'/tmp/{dir_name}.zip', f'{output_filename}.zip')
        shutil.rmtree(f'/tmp/{dir_name}/')

    def gen_presign_url(self, object_name: str, expiration=3600) -> str:
        """
        generate presign url
        :param object_name: object path(key)
        :param expiration: defaults to 3600s
        :return: presign url
        """
        params = {
            'Bucket': self.bucket,
            'Key': object_name
        }
        try:
            response = self.client.generate_presigned_url('get_object', Params=params, ExpiresIn=expiration)
            return response
        except Exception:
            return ''
