"""
gcp cloud storage sdk
"""
import os

from dotenv import load_dotenv, find_dotenv
from google.cloud import storage

load_dotenv(find_dotenv())


class CloudStorage:

    def __init__(self):
        client = storage.Client(project=os.environ['GCP_PROJECT'])
        self.bucket = client.get_bucket(os.environ['GCP_BUCKET'])

    def upload_str(self, gcp_filename: str, string: str) -> bool:
        """
        upload file
        :param gcp_filename: cloud storage path
        :param string
        :return: bool
        """
        try:
            blob = self.bucket.blob(gcp_filename)
            blob.upload_from_string(string)
        except Exception:
            return False
        return True

    def upload_file(self, gcp_filename: str, local_filename: str) -> bool:
        """
        upload file
        :param gcp_filename: cloud storage path
        :param local_filename: local file path
        :return: bool
        """
        try:
            blob = self.bucket.blob(gcp_filename)
            blob.upload_from_filename(local_filename)
        except Exception:
            return False
        return True

    def download_dir(self, bucket_dir: str, local_dir: str):
        blobs = self.bucket.list_blobs(prefix=bucket_dir)
        for blob in blobs:
            _dir, filename = blob.name.split('/')
            if not os.path.exists(f'{local_dir}{_dir}/'):
                os.mkdir(f'{local_dir}{_dir}/')
            blob.download_to_filename(f'{local_dir}{_dir}/{filename}')

# ssl = CloudStorage()
# ssl.download_file('1381711117.*.abc.com/', '../tmp/')
