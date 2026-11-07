"""The only module that talks to S3. Services call these methods and never import boto3,
just like they call repositories and never write SQL.

File bytes never pass through FastAPI: the client uploads straight to S3 with a presigned POST,
and the API only signs that permission and later checks what actually arrived.
"""

from dataclasses import dataclass
from urllib.parse import quote

import boto3
from botocore.config import Config
from botocore.exceptions import ClientError

from app.config import S3_ACCESS_KEY_ID, S3_BUCKET, S3_ENDPOINT_URL, S3_REGION, S3_SECRET_ACCESS_KEY


@dataclass
class StoredObject:
    """What S3 says about an object (HeadObject), as opposed to what the client claimed."""

    size_bytes: int
    content_type: str


class S3Storage:
    def __init__(self, bucket: str = S3_BUCKET):
        self.bucket = bucket
        self.client = boto3.client(
            "s3",
            endpoint_url=S3_ENDPOINT_URL,  # None = real AWS
            region_name=S3_REGION,
            aws_access_key_id=S3_ACCESS_KEY_ID,
            aws_secret_access_key=S3_SECRET_ACCESS_KEY,
            # path style (http://host/bucket/key) works for both local S3 and AWS
            config=Config(signature_version="s3v4", s3={"addressing_style": "path"}),
        )

    def presigned_post(self, *, key: str, content_type: str, max_bytes: int, expires_in: int) -> dict:
        """A short-lived permission to upload ONE object at `key`.

        S3 itself rejects the upload if it breaks these conditions, before the bytes are stored:
        a different Content-Type → 403, a body larger than max_bytes → 400 EntityTooLarge.
        """
        return self.client.generate_presigned_post(
            Bucket=self.bucket,
            Key=key,
            Fields={"Content-Type": content_type},
            Conditions=[{"Content-Type": content_type}, ["content-length-range", 1, max_bytes]],
            ExpiresIn=expires_in,
        )

    def head(self, key: str) -> StoredObject | None:
        """HeadObject: the object's real size and type, without downloading it. None if missing."""
        try:
            response = self.client.head_object(Bucket=self.bucket, Key=key)
        except ClientError as exc:
            if exc.response["Error"]["Code"] in ("404", "NoSuchKey", "NotFound"):
                return None
            raise
        return StoredObject(size_bytes=response["ContentLength"], content_type=response["ContentType"])

    def read_start(self, key: str, length: int) -> bytes:
        """The first `length` bytes (a ranged GET), e.g. to check a file signature like %PDF-."""
        response = self.client.get_object(Bucket=self.bucket, Key=key, Range=f"bytes=0-{length - 1}")
        return response["Body"].read()

    def delete(self, key: str) -> None:
        self.client.delete_object(Bucket=self.bucket, Key=key)

    def presigned_download_url(self, *, key: str, filename: str, expires_in: int) -> str:
        """A short-lived GET link. The browser downloads from S3 directly, under the original filename."""
        return self.client.generate_presigned_url(
            "get_object",
            Params={
                "Bucket": self.bucket,
                "Key": key,
                # RFC 5987 form, so non-ASCII names such as 产品手册.pdf survive the HTTP header
                "ResponseContentDisposition": f"attachment; filename*=UTF-8''{quote(filename)}",
            },
            ExpiresIn=expires_in,
        )
