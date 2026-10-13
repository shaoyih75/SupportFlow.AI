from uuid import UUID

from sqlalchemy.orm import Session

from app.db.session import transaction
from app.errors import ForbiddenError, NotFoundError
from app.models import User, Workspace, WorkspaceMember
from app.repositories.base import WorkspaceRepository
from app.schemas.workspace import WorkspaceCreate, WorkspaceResponse


class WorkspaceService:
    def __init__(self, session: Session, workspaces: WorkspaceRepository):
        self.session = session
        self.workspaces = workspaces

    def require_member(self, workspace_id: UUID, user: User) -> WorkspaceMember:
        """Every workspace-scoped request goes through here before touching data."""
        if self.workspaces.get(workspace_id) is None:
            raise NotFoundError("workspace")
        membership = self.workspaces.get_active_membership(workspace_id, user.id)
        if membership is None:
            raise ForbiddenError("You are not a member of this workspace")
        return membership

    def list_for_user(self, user: User) -> list[WorkspaceResponse]:
        return [self._to_response(ws, m) for ws, m in self.workspaces.list_for_user(user.id)]

    def create(self, payload: WorkspaceCreate, user: User) -> WorkspaceResponse:
        # Two writes, one transaction: a workspace must never exist without its OWNER.
        with transaction(self.session):
            ws = self.workspaces.add(Workspace(name=payload.name, owner_user_id=user.id))
            membership = self.workspaces.add_member(WorkspaceMember(workspace_id=ws.id, user_id=user.id, role="OWNER"))
        return self._to_response(ws, membership)

    def _to_response(self, ws: Workspace, m: WorkspaceMember) -> WorkspaceResponse:
        return WorkspaceResponse(
            id=ws.id,
            name=ws.name,
            role=m.role,
            member_count=self.workspaces.count_members(ws.id),
            created_at=ws.created_at,
        )
