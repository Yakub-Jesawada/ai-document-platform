import os
import logging
import boto3
from botocore.exceptions import ClientError
from typing import Optional
from config import settings

logger = logging.getLogger(__name__)


class S3Storage:
    def __init__(self, location: str = ""):
        self.s3 = boto3.client(
            "s3",
            aws_access_key_id=settings.S3_ACCESS_KEY,
            aws_secret_access_key=settings.S3_SECRET_ACCESS_KEY,
            region_name=settings.S3_BUCKET_REGION,
        )
        self.bucket_name = settings.S3_BUCKET_NAME
        self.location = location

    def _get_s3_key(self, filename: str):
        return f"{self.location}/{filename}" if self.location else filename

    def upload_file(self, file_path: str, filename: Optional[str] = None):
        key = self._get_s3_key(filename or os.path.basename(file_path))
        self.s3.upload_file(Filename=file_path, Bucket=self.bucket_name, Key=key)
        return key

    def generate_presigned_url(self, key: str, expires_in: int = 3600) -> str:
        try:
            url = self.s3.generate_presigned_url(
                "get_object",
                Params={"Bucket": self.bucket_name, "Key": key},
                ExpiresIn=expires_in,
            )
            return url
        except ClientError:
            logger.exception("Failed to generate presigned URL for key: %s", key)
            return None

    def delete_file(self, key: str) -> bool:
        try:
            self.s3.delete_object(
                Bucket=self.bucket_name,
                Key=key,
            )
            return True
        except ClientError:
            logger.exception("Failed to delete S3 object: %s", key)
            return False


class DocumentStorage(S3Storage):
    def __init__(self):
        super().__init__(location="documents")
