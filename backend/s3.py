import boto3, botocore
from botocore.client import BaseClient
from fastapi import UploadFile
from backend import settings
import os, sys, threading
from boto3.s3.transfer import TransferConfig

upload_result = []

class ProgressPercentage(object):
    def __init__(self, file: UploadFile):
        self._filename = file.filename
        file.file.seek(0, 2)
        self._size = file.file.tell()
        print("file size", self._size)
        file.file.seek(0, 0)
        self._seen_so_far = 0
        self._lock = threading.Lock()

    def __call__(self, bytes_amount):
        with self._lock:
            self._seen_so_far += bytes_amount
            percentage = (self._seen_so_far / self._size) * 100
            upload_result.append(
                "\r%s  %s / %s  (%.2f%%)" % (
                    self._filename, self._seen_so_far, self._size,
                    percentage))

            # sys.stdout.flush()


def get_s3_client():
    try:
        # conn = boto3.connect_s3(aws_access_key_id, aws_secret_access_key)

        s3_client: BaseClient = boto3.client(
            "s3",
            aws_access_key_id=settings.AWS_KEY,
            aws_secret_access_key=settings.AWS_SECRET
        )
        # s3_client.
        return s3_client
    except:
        # TODO
        print("exception in getting s3 cli")
        pass


async def upload_file_to_s3(s3_client, file: UploadFile):

    # config = TransferConfig(multipart_threshold=1024 * 25, max_concurrency=os.cpu_count(),
    #                         multipart_chunksize=1024 * 25, use_threads=True)

    file_file = file.file

    s3_client.upload_fileobj(
        file_file,
        settings.BUCKET_NAME,
        file.filename,
        ExtraArgs={
            "ACL": "public-read",
            "ContentType": file.content_type
        },
        Callback=ProgressPercentage(file)
    )


def get_video_object(key=settings.KEY, range=None):
    key = key.split(".")[0] + ".mp4"
    s3_client = get_s3_client()
    if not range:
        video_obj = s3_client.get_object(Bucket=settings.BUCKET_NAME, Key=key)
    else:
        video_obj = s3_client.get_object(Bucket=settings.BUCKET_NAME, Key=key, Range=range)

    return video_obj
