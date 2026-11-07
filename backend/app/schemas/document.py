from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field

from app.config import MAX_UPLOAD_BYTES
from app.models import DocumentStatus


class UploadInitRequest(BaseModel):
    # No workspace_id here: it comes from the URL, and the membership check runs on that value.
    # Everything below is only the client's CLAIM; upload-complete checks it against S3.
    filename: str = Field(min_length=1, max_length=255)
    content_type: str = Field(min_length=1, max_length=100)
    size_bytes: int = Field(gt=0, le=MAX_UPLOAD_BYTES)


class PresignedPost(BaseModel):
    url: str
    fields: dict[str, str]  # must be sent as form fields, before the file, in the POST to `url`


class DocumentResponse(BaseModel):
    # storage_key stays internal: clients never need to know where the bytes live.
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    workspace_id: UUID
    filename: str
    content_type: str
    size_bytes: int
    status: DocumentStatus
    created_at: datetime
    uploaded_at: datetime | None


class UploadInitResponse(BaseModel):
    document: DocumentResponse
    upload: PresignedPost
    expires_in: int  # seconds


class DownloadUrlResponse(BaseModel):
    url: str
    expires_in: int
