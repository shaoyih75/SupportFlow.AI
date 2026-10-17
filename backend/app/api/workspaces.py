from uuid import UUID

from fastapi import APIRouter, Depends, Response

from app.deps import can_manage_members, can_read, get_current_user, get_workspace_service
from app.models import User, WorkspaceMember
from app.schemas.workspace import MemberCreate, MemberResponse, WorkspaceCreate, WorkspaceResponse
from app.services.workspace_service import WorkspaceService

router = APIRouter(prefix="/workspaces", tags=["workspaces"])


@router.get("", response_model=list[WorkspaceResponse])
def list_workspaces(
    user: User = Depends(get_current_user),
    service: WorkspaceService = Depends(get_workspace_service),
):
    return service.list_for_user(user)


@router.post("", response_model=WorkspaceResponse, status_code=201)
def create_workspace(
    payload: WorkspaceCreate,
    user: User = Depends(get_current_user),
    service: WorkspaceService = Depends(get_workspace_service),
):
    return service.create(payload, user)


@router.get("/{workspace_id}", response_model=WorkspaceResponse)
def get_workspace(
    workspace_id: UUID,
    membership: WorkspaceMember = Depends(can_read),
    service: WorkspaceService = Depends(get_workspace_service),
):
    return service.get(membership)


@router.get("/{workspace_id}/members", response_model=list[MemberResponse])
def list_members(
    workspace_id: UUID,
    membership: WorkspaceMember = Depends(can_read),
    service: WorkspaceService = Depends(get_workspace_service),
):
    return service.list_members(workspace_id)


@router.post("/{workspace_id}/members", response_model=MemberResponse, status_code=201)
def add_member(
    workspace_id: UUID,
    payload: MemberCreate,
    membership: WorkspaceMember = Depends(can_manage_members),
    service: WorkspaceService = Depends(get_workspace_service),
):
    return service.add_member(workspace_id, payload)


@router.delete("/{workspace_id}/members/{user_id}", status_code=204)
def remove_member(
    workspace_id: UUID,
    user_id: UUID,
    membership: WorkspaceMember = Depends(can_manage_members),
    service: WorkspaceService = Depends(get_workspace_service),
):
    service.remove_member(workspace_id, user_id)
    return Response(status_code=204)
