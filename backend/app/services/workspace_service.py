from datetime import datetime, timezone
from uuid import UUID, uuid4

from app.errors import ForbiddenError, NotFoundError
from app.models import User, Workspace, WorkspaceMember
from app.repositories.memory import InMemoryRepository
from app.schemas.workspace import WorkspaceCreate, WorkspaceResponse


class WorkspaceService:
    def __init__(self, repo: InMemoryRepository):
        self.repo = repo

    def require_member(self, workspace_id: UUID, user: User) -> WorkspaceMember:
        """Every workspace-scoped request goes through here before touching data."""
        if self.repo.get_workspace(workspace_id) is None:
            raise NotFoundError("workspace")
        membership = self.repo.get_membership(workspace_id, user.id)
        if membership is None:
            raise ForbiddenError("You are not a member of this workspace")
        return membership

    def list_for_user(self, user: User) -> list[WorkspaceResponse]:
        result = []
        for m in self.repo.list_memberships(user.id):
            ws = self.repo.get_workspace(m.workspace_id)
            if ws is not None:
                result.append(self._to_response(ws, m))
        return sorted(result, key=lambda w: w.created_at)

    def create(self, payload: WorkspaceCreate, user: User) -> WorkspaceResponse:
        ws = self.repo.add_workspace(Workspace(uuid4(), payload.name, user.id, datetime.now(timezone.utc)))
        membership = self.repo.add_member(WorkspaceMember(ws.id, user.id, "OWNER"))
        return self._to_response(ws, membership)

    def _to_response(self, ws: Workspace, m: WorkspaceMember) -> WorkspaceResponse:
        return WorkspaceResponse(
            id=ws.id,
            name=ws.name,
            role=m.role,
            member_count=self.repo.count_members(ws.id),
            created_at=ws.created_at,
        )
