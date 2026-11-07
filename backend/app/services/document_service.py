"""Document upload in three steps. FastAPI handles permission and metadata; the bytes go to S3 directly.

    1. upload-init      client → API   check type/size, write a PENDING row, sign a presigned POST
    2. upload           client → S3    the file goes straight to S3 (never through this server)
    3. upload-complete  client → API   ask S3 what really arrived (HeadObject), then mark UPLOADED

Rule of thumb: everything the client says (filename, type, size, "upload succeeded") is a claim.
Only what S3 reports in step 3 is trusted.
"""

import re
from datetime import timedelta
from pathlib import PurePosixPath
from uuid import UUID, uuid4

from sqlalchemy.orm import Session

from app.config import MAX_UPLOAD_BYTES, UPLOAD_URL_EXPIRES_SECONDS
from app.db.base import utcnow
from app.db.session import transaction
from app.errors import BadRequestError, ConflictError, NotFoundError
from app.models import Document
from app.repositories.base import DocumentRepository
from app.schemas.document import DocumentResponse, DownloadUrlResponse, PresignedPost, UploadInitRequest, UploadInitResponse
from app.storage.s3 import S3Storage, StoredObject

# Extension → content types we accept for it. Both must match, and both are still only claims:
# upload-complete re-checks the type S3 stored and the file's first bytes.
ALLOWED_TYPES = {
    ".pdf": {"application/pdf"},
    ".txt": {"text/plain"},
    ".md": {"text/markdown", "text/plain"},  # browsers and OSes disagree on Markdown's type
}
PDF_SIGNATURE = b"%PDF-"
DOWNLOAD_URL_EXPIRES_SECONDS = 300
# S3 checks the expiry when an upload STARTS. An upload begun just before the deadline can still
# be streaming after it, so a missing file only counts as "never coming" once this grace has passed too.
UPLOAD_GRACE = timedelta(minutes=10)


def clean_filename(raw: str) -> str:
    """Keep a display name only: no folders ("../../etc/passwd" → "passwd"), no control characters."""
    name = PurePosixPath(raw.replace("\\", "/")).name
    return re.sub(r"[\x00-\x1f\x7f]", "", name).strip()


class DocumentService:
    def __init__(self, session: Session, documents: DocumentRepository, storage: S3Storage):
        self.session = session
        self.documents = documents
        self.storage = storage

    # ---------- step 1 ----------

    def init_upload(self, workspace_id: UUID, user_id: UUID, payload: UploadInitRequest) -> UploadInitResponse:
        filename = clean_filename(payload.filename)
        extension = PurePosixPath(filename).suffix.lower()
        if not filename or payload.content_type not in ALLOWED_TYPES.get(extension, set()):
            raise BadRequestError("UNSUPPORTED_FILE_TYPE", "Only PDF, TXT and Markdown (.md) files are supported")

        # The server picks the key: unique per document, scoped by workspace, never the user's filename.
        document_id = uuid4()
        storage_key = f"workspaces/{workspace_id}/documents/{document_id}{extension}"

        # Write the PENDING row BEFORE handing out the upload permission: every object that can
        # ever appear in S3 then already has a row saying whose it is and what it should be.
        with transaction(self.session):
            document = self.documents.add(
                Document(
                    id=document_id,
                    workspace_id=workspace_id,
                    uploaded_by_user_id=user_id,
                    filename=filename,
                    storage_key=storage_key,
                    content_type=payload.content_type,
                    size_bytes=payload.size_bytes,
                    status="PENDING",
                    upload_expires_at=utcnow() + timedelta(seconds=UPLOAD_URL_EXPIRES_SECONDS),
                )
            )

        # Signing is local math with our credentials: no request to S3 happens here.
        upload = self.storage.presigned_post(
            key=storage_key,
            content_type=payload.content_type,
            max_bytes=MAX_UPLOAD_BYTES,  # S3 refuses anything bigger, before storing it
            expires_in=UPLOAD_URL_EXPIRES_SECONDS,
        )
        return UploadInitResponse(
            document=DocumentResponse.model_validate(document),
            upload=PresignedPost(url=upload["url"], fields=upload["fields"]),
            expires_in=UPLOAD_URL_EXPIRES_SECONDS,
        )

    # ---------- step 3 ----------

    def complete_upload(self, workspace_id: UUID, document_id: UUID) -> DocumentResponse:
        document = self._get_or_404(workspace_id, document_id)

        # Idempotent: a retry after a lost response gets the same success, not an error or a new row.
        if document.status == "UPLOADED":
            return DocumentResponse.model_validate(document)

        # Always ask S3 first, even for EXPIRED: what decides is whether the file is there, not the clock.
        stored = self.storage.head(document.storage_key)
        if stored is None:
            # Expired only when the file can no longer arrive: the upload permission AND the grace are over.
            if document.status == "EXPIRED" or utcnow() > document.upload_expires_at + UPLOAD_GRACE:
                if document.status != "EXPIRED":
                    with transaction(self.session):
                        self.documents.update(document, {"status": "EXPIRED"})
                raise ConflictError("UPLOAD_EXPIRED", "This upload has expired. Start a new upload.")
            # Retryable: the client may call complete before S3 finished, or never uploaded.
            raise ConflictError("UPLOAD_NOT_FOUND", "The file has not arrived in S3 yet. Upload it, then retry.")

        # The file is there. S3 only accepts uploads that started while the presigned POST was valid,
        # so it is accepted however late this call comes, even if the row was already marked EXPIRED
        # (an upload that finished after the deadline): EXPIRED → UPLOADED.
        problem = self._verify(document, stored)
        if problem:
            self.storage.delete(document.storage_key)  # never keep bytes we refuse to vouch for
            raise BadRequestError("UPLOAD_REJECTED", problem)

        with transaction(self.session):
            self.documents.update(document, {"status": "UPLOADED", "uploaded_at": utcnow()})
        return DocumentResponse.model_validate(document)

    def _verify(self, document: Document, stored: StoredObject) -> str | None:
        """Compare what S3 actually stored with what the client declared at upload-init."""
        if stored.size_bytes != document.size_bytes:
            return f"Uploaded file is {stored.size_bytes} bytes, but {document.size_bytes} bytes were declared"
        if stored.content_type != document.content_type:
            return f"Uploaded file type {stored.content_type} does not match {document.content_type}"

        # Content check: the extension and Content-Type are just labels the client chose.
        start = self.storage.read_start(document.storage_key, 1024)
        if document.content_type == "application/pdf":
            if not start.startswith(PDF_SIGNATURE):
                return "File is not a valid PDF"
        elif b"\x00" in start:
            return "File is not a text file"
        return None

    # ---------- read ----------

    def list(self, workspace_id: UUID) -> list[DocumentResponse]:
        return [DocumentResponse.model_validate(d) for d in self.documents.list(workspace_id)]

    def get(self, workspace_id: UUID, document_id: UUID) -> DocumentResponse:
        return DocumentResponse.model_validate(self._get_or_404(workspace_id, document_id))

    def download_url(self, workspace_id: UUID, document_id: UUID) -> DownloadUrlResponse:
        document = self._get_or_404(workspace_id, document_id)
        if document.status != "UPLOADED":
            raise ConflictError("DOCUMENT_NOT_UPLOADED", "This document has not finished uploading")
        url = self.storage.presigned_download_url(
            key=document.storage_key, filename=document.filename, expires_in=DOWNLOAD_URL_EXPIRES_SECONDS
        )
        return DownloadUrlResponse(url=url, expires_in=DOWNLOAD_URL_EXPIRES_SECONDS)

    def _get_or_404(self, workspace_id: UUID, document_id: UUID) -> Document:
        document = self.documents.get_in_workspace(workspace_id=workspace_id, document_id=document_id)
        if document is None:
            raise NotFoundError("document")
        return document
