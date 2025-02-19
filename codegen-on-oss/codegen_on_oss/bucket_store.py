from importlib.metadata import version
from typing import TYPE_CHECKING

from boto3 import client

if TYPE_CHECKING:
    from types_boto3_s3 import S3Client

    from codegen_on_oss.sources import RepoSource


class BucketStore:
    s3_client: "S3Client"

    def __init__(self, bucket_name: str):
        self.bucket_name = bucket_name
        self.s3_client = client("s3")

    def upload_run(
        self,
        repo_source: "RepoSource",
        log_output_path: str,
        metrics_output_path: str,
    ):
        codegen_version = str(version("codegen"))
        key_prefix: str = f"{codegen_version}/{repo_source.source_type}"
        config_key = f"{key_prefix}/config.json"

        self.s3_client.put_object(
            Bucket=self.bucket_name,
            Key=config_key,
            Body=repo_source.settings.model_dump_json(indent=4).encode("utf-8"),
            ContentType="application/json",
        )

        log_key = f"{key_prefix}/output.logs"
        self.s3_client.upload_file(log_output_path, self.bucket_name, log_key)

        metrics_key = f"{key_prefix}/metrics.csv"
        self.s3_client.upload_file(metrics_output_path, self.bucket_name, metrics_key)
