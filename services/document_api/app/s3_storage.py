import boto3
from botocore.exceptions import ClientError
from typing import Optional
from env import S3_ACCESS_KEY, S3_BUCKET_NAME, S3_BUCKET_REGION, S3_SECRET_ACCESS_KEY

class S3Storage:
    def __init__(self, location: str = ""):
        self.s3 = boto3.client(
            "s3",
            aws_access_key_id=S3_ACCESS_KEY,
            aws_secret_access_key=S3_SECRET_ACCESS_KEY,
            region_name=S3_BUCKET_REGION,
        )
        self.bucket_name = S3_BUCKET_NAME
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
            return None
    
    def delete_file(self, key: str) -> bool:
        """
        Delete a file from S3 using its key.
        Returns True if delete request succeeded.
        """
        try:
            self.s3.delete_object(
                Bucket=self.bucket_name,
                Key=key,
            )
            return True
        except ClientError:
            return False


class StaticStorage(S3Storage):
    def __init__(self):
        super().__init__(location="static", default_acl="public-read")


class MediaStorage(S3Storage):
    def __init__(self):
        super().__init__(location="media")


class DocumentStorage(S3Storage):
    def __init__(self):
        super().__init__(location="documents")
