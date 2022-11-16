import boto3

BUCKET_NAME = 'po-lambda'


class S3():
    def __init__(self):
        self.client = boto3.client('s3')
        self.s3 = boto3.resource('s3')

    def upload_data(self, path: str, data: str):
        """upload data to S3

        Args:
            path (str): full file path.
            data (str): Data in the file.

        Returns:
            Success: True, Failed: False
        """
        result = self.client.put_object(
            Body=data, Bucket=BUCKET_NAME, Key=path)
        res = result.get('ResponseMetadata')
        if res.get('HTTPStatusCode') == 200:
            return True
        else:
            return False
