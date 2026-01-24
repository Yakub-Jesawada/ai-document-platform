from uuid import uuid4
from tempfile import NamedTemporaryFile
import os

from fastapi import UploadFile
from s3_storage import S3Storage
from functools import lru_cache

@lru_cache
def get_s3_storage() -> S3Storage:
    return S3Storage()


def get_file_extension(filename: str) -> str:
    return filename.rsplit(".", 1)[-1].lower() if "." in filename else ""


async def upload_file_to_s3(
    *,
    file: UploadFile,
    user_uuid: str,
) -> str:
    """
    Uploads file to S3 and returns stable S3 key.
    """
    s3 = get_s3_storage()

    filename = f"{file.filename}"
    s3_key = f"documents/{user_uuid}/{filename}"

    with NamedTemporaryFile(delete=False) as tmp:
        tmp.write(await file.read())
        tmp_path = tmp.name

    try:
        s3.upload_file(tmp_path, s3_key)
    finally:
        os.remove(tmp_path)

    return s3_key

