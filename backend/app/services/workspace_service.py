from uuid import UUID

from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.db.session import transaction
from app.errors import ConflictError, NotFoundError
from app.models import User, Workspace, WorkspaceMember
from app.repositories.base import UserRepository, WorkspaceRepository
from app.schemas.workspace import MemberCreate, MemberResponse, WorkspaceCreate, WorkspaceResponse


class WorkspaceService:
    def __init__(self, session: Session, workspaces: WorkspaceRepository, users: UserRepository):
        self.session = session
        self.workspaces = workspaces
        self.users = users

    def list_for_user(self, user: User) -> list[WorkspaceResponse]:
        # Only ACTIVE memberships: a suspended or removed member no longer sees the workspace.
        return [self._to_response(ws, m) for ws, m in self.workspaces.list_for_user(user.id)]

    def get(self, membership: WorkspaceMember) -> WorkspaceResponse:
        ws = self.workspaces.get(membership.workspace_id)
        assert ws is not None  # the FK guarantees it for an existing membership
        return self._to_response(ws, membership)

    def create(self, payload: WorkspaceCreate, user: User) -> WorkspaceResponse:
        # Two writes, one transaction: a workspace must never exist without its OWNER.
        with transaction(self.session):
            ws = self.workspaces.add(Workspace(name=payload.name, owner_user_id=user.id))
            membership = self.workspaces.add_member(WorkspaceMember(workspace_id=ws.id, user_id=user.id, role="OWNER"))
        return self._to_response(ws, membership)

    def list_members(self, workspace_id: UUID) -> list[MemberResponse]:
        return [self._member_response(m, u) for m, u in self.workspaces.list_members(workspace_id)]

    def add_member(self, workspace_id: UUID, payload: MemberCreate) -> MemberResponse:
        user = self.users.get_by_email(payload.email.strip().lower())
        if user is None:
            raise NotFoundError("user")
        existing = self.workspaces.get_membership(workspace_id, user.id)
        if existing is not None and existing.status == "ACTIVE":
            raise ConflictError("ALREADY_A_MEMBER", "User is already a member of this workspace")
        try:
            with transaction(self.session):
                if existing is not None:
                    # One row per (workspace, user): re-activate instead of inserting a duplicate.
                    existing.role, existing.status = payload.role, "ACTIVE"
                    member = existing
                else:
                    member = self.workspaces.add_member(
                        WorkspaceMember(workspace_id=workspace_id, user_id=user.id, role=payload.role)
                    )
        except IntegrityError as exc:
            # Two concurrent adds: the UNIQUE constraint, not the check above, has the last word.
            if "uq_workspace_member" in str(exc.orig):
                raise ConflictError("ALREADY_A_MEMBER", "User is already a member of this workspace") from exc
            raise
        return self._member_response(member, user)

    def remove_member(self, workspace_id: UUID, user_id: UUID) -> None:
        member = self.workspaces.get_active_membership(workspace_id, user_id)
        if member is None:
            raise NotFoundError("member")
        if member.role == "OWNER" and self._active_owner_count(workspace_id) == 1:
            raise ConflictError("LAST_OWNER", "A workspace must keep at least one OWNER")
        with transaction(self.session):
            member.status = "REMOVED"  # keep the row (history); access ends immediately

    def _active_owner_count(self, workspace_id: UUID) -> int:
        return sum(1 for m, _ in self.workspaces.list_members(workspace_id) if m.role == "OWNER" and m.status == "ACTIVE")

    def _to_response(self, ws: Workspace, m: WorkspaceMember) -> WorkspaceResponse:
        return WorkspaceResponse(
            id=ws.id,
            name=ws.name,
            role=m.role,
            member_count=self.workspaces.count_members(ws.id),
            created_at=ws.created_at,
        )

    @staticmethod
    def _member_response(m: WorkspaceMember, u: User) -> MemberResponse:
        return MemberResponse(user_id=u.id, name=u.name, email=u.email, role=m.role, status=m.status, joined_at=m.joined_at)
