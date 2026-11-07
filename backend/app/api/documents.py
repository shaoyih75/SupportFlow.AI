from uuid import UUID

from fastapi import APIRouter, Depends

from app.deps import can_read, can_upload_documents, get_document_service
from app.models import WorkspaceMember
from app.schemas.document import DocumentResponse, DownloadUrlResponse, UploadInitRequest, UploadInitResponse
from app.services.document_service import DocumentService

# Same pattern as tickets: under the workspace, `membership` runs the permission checks first.
router = APIRouter(prefix="/workspaces/{workspace_id}/documents", tags=["documents"])


@router.get("", response_model=list[DocumentResponse])
def list_documents(
    workspace_id: UUID,
    membership: WorkspaceMember = Depends(can_read),
    service: DocumentService = Depends(get_document_service),
):
    return service.list(workspace_id)


@router.post("/upload-init", response_model=UploadInitResponse, status_code=201)
def init_upload(
    workspace_id: UUID,
    payload: UploadInitRequest,
    membership: WorkspaceMember = Depends(can_upload_documents),
    service: DocumentService = Depends(get_document_service),
):
    """Step 1: returns a presigned POST. Send the file to `upload.url` with `upload.fields`, then call
    upload-complete."""
    return service.init_upload(workspace_id, membership.user_id, payload)


@router.post("/{document_id}/upload-complete", response_model=DocumentResponse)
def complete_upload(
    workspace_id: UUID,
    document_id: UUID,
    membership: WorkspaceMember = Depends(can_upload_documents),
    service: DocumentService = Depends(get_document_service),
):
    """Step 3: the server checks the object in S3 and marks the document UPLOADED. Safe to retry."""
    return service.complete_upload(workspace_id, document_id)


@router.get("/{document_id}", response_model=DocumentResponse)
def get_document(
    workspace_id: UUID,
    document_id: UUID,
    membership: WorkspaceMember = Depends(can_read),
    service: DocumentService = Depends(get_document_service),
):
    return service.get(workspace_id, document_id)


@router.get("/{document_id}/download-url", response_model=DownloadUrlResponse)
def get_download_url(
    workspace_id: UUID,
    document_id: UUID,
    membership: WorkspaceMember = Depends(can_read),
    service: DocumentService = Depends(get_document_service),
):
    """A short-lived link to download the file straight from S3."""
    return service.download_url(workspace_id, document_id)
