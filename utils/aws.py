import boto3
import os
import shutil


class S3:
    def __init__(self, bucket_name: str):
        # setting up sessions
        self.client = boto3.client('s3')
        self.s3 = boto3.resource('s3')
        self.bucket = bucket_name

    def upload_data(self, path: str, data: str) -> bool:
        """upload data to S3

        Args:
            path (str): full file path.
            data (str): Data in the file.

        Returns:
            Success: True, Failed: False
        """
        result = self.client.put_object(Body=data, Bucket=self.bucket, Key=path)
        res = result.get('ResponseMetadata')  # check if success
        if res.get('HTTPStatusCode') == 200:
            return True
        else:
            return False

    def get_object(self, path: str):
        """get object from s3

        Args:
            path (str): file path

        Returns:
            data
        """
        obj = self.s3.Object(self.bucket, path)
        return obj.get()['Body'].read().decode('utf-8')

    def zip_folder(self, dir_name: str, output_filename: str):
        """zip s3 dir and upload to bucket, this utilizes lambda /tmp/ dir to zip file and send back to bucket.

        Args:
            dir_name (str): s3 directory name
            output_filename (str): file path+name **without .zip
        """
        bucket = self.s3.Bucket(self.bucket)
        if not os.path.exists(f'/tmp/{dir_name}'):
            os.makedirs(f'/tmp/{dir_name}')
        for f in bucket.objects.filter(Prefix=dir_name):
            if '.zip' not in f.key:
                bucket.download_file(f.key, f'/tmp/{f.key}')
        shutil.make_archive(f'/tmp/{dir_name}', 'zip', '/tmp', dir_name)
        self.s3.Bucket(self.bucket).upload_file(f'/tmp/{dir_name}.zip', f'{output_filename}.zip')
        shutil.rmtree(f'/tmp/{dir_name}/')

    def gen_presign_url(self, object_name: str, expiration=3600):
        """generate presign url

        Args:
            object_name (str): object name+path
            expiration (int, optional): Defaults to 3600.
        """
        params = {'Bucket': self.bucket, 'Key': object_name}
        try:
            response = self.client.generate_presigned_url('get_object', Params=params, ExpiresIn=expiration)
            return response
        except Exception as err:
            return err
