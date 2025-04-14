from datetime import datetime
from importlib.metadata import version
from typing import TYPE_CHECKING

from boto3 import client

if TYPE_CHECKING:
    from types_boto3_s3 import S3Client


class BucketStore:
    s3_client: "S3Client"

    def __init__(self, bucket_name: str):
        self.bucket_name = bucket_name
        self.s3_client = client("s3")
        self.key_prefix: str = str(version("codegen"))

    def upload_file(self, local_path: str, remote_path: str) -> str:
        key = f"{self.key_prefix}/{datetime.now().strftime('%Y-%m-%d-%H-%M-%S')}/{remote_path}"
        self.s3_client.upload_file(
            local_path,
            self.bucket_name,
            key,
        )
        return key
