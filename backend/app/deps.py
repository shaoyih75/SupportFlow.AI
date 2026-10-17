"""Dependencies injected with Depends(): identity, membership and role checks run here,
BEFORE any route body or business logic.

    Authorization: Bearer <token>
      → get_current_user            401 if missing / invalid / expired
      → require_workspace_member    403 if no ACTIVE membership in the URL's workspace
      → require_workspace_role(...) 403 if the role may not do this action
      → TicketService (scoped query) 404 if the ticket is not in this workspace
"""

from uuid import UUID

import jwt
from fastapi import Depends
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.orm import Session

from app.auth.security import decode_access_token
from app.db.session import get_session
from app.errors import ForbiddenError, UnauthorizedError
from app.models import Role, User, WorkspaceMember
from app.repositories.postgres import PostgresTicketRepository, PostgresUserRepository, PostgresWorkspaceRepository
from app.services.ticket_service import TicketService
from app.services.user_service import UserService
from app.services.workspace_service import WorkspaceService

# Reads `Authorization: Bearer <token>`. tokenUrl powers Swagger's "Authorize" button.
# auto_error=False: we raise our own 401 so the error body keeps the project's shape.
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/auth/token", auto_error=False)


# ---------- repositories and services ----------

def get_user_repository(session: Session = Depends(get_session)) -> PostgresUserRepository:
    return PostgresUserRepository(session)


def get_workspace_repository(session: Session = Depends(get_session)) -> PostgresWorkspaceRepository:
    return PostgresWorkspaceRepository(session)


def get_ticket_repository(session: Session = Depends(get_session)) -> PostgresTicketRepository:
    return PostgresTicketRepository(session)


def get_workspace_service(
    session: Session = Depends(get_session),
    workspaces: PostgresWorkspaceRepository = Depends(get_workspace_repository),
    users: PostgresUserRepository = Depends(get_user_repository),
) -> WorkspaceService:
    return WorkspaceService(session, workspaces, users)


def get_ticket_service(
    session: Session = Depends(get_session),
    tickets: PostgresTicketRepository = Depends(get_ticket_repository),
) -> TicketService:
    return TicketService(session, tickets)


def get_user_service(
    session: Session = Depends(get_session),
    users: PostgresUserRepository = Depends(get_user_repository),
    workspaces: PostgresWorkspaceRepository = Depends(get_workspace_repository),
) -> UserService:
    return UserService(session, users, workspaces)


# ---------- authentication: who are you? ----------

def get_current_user(
    token: str | None = Depends(oauth2_scheme),
    users: PostgresUserRepository = Depends(get_user_repository),
) -> User:
    if not token:
        raise UnauthorizedError("Not authenticated")
    try:
        payload = decode_access_token(token)
        user_id = UUID(payload["sub"])
    except (jwt.PyJWTError, KeyError, ValueError):
        raise UnauthorizedError("Invalid or expired token")

    # The token proves who signed in; the database says whether that user still exists.
    user = users.get(user_id)
    if user is None:
        raise UnauthorizedError("User not found")
    return user


# ---------- authorization: may you enter / may you do this? ----------

def require_workspace_member(
    workspace_id: UUID,  # from the URL path, e.g. /workspaces/{workspace_id}/tickets
    current_user: User = Depends(get_current_user),  # from the token, never from the request body
    workspaces: PostgresWorkspaceRepository = Depends(get_workspace_repository),
) -> WorkspaceMember:
    membership = workspaces.get_active_membership(workspace_id, current_user.id)
    # Same 403 whether the workspace does not exist or you are not in it (or are SUSPENDED / REMOVED):
    # an outsider learns nothing about which workspace ids are real.
    if membership is None:
        raise ForbiddenError("You do not have access to this workspace")
    return membership  # role checks reuse this row instead of querying again


def require_workspace_role(*allowed_roles: Role):
    """Dependency factory: `Depends(require_workspace_role("OWNER", "MEMBER"))`."""

    def dependency(membership: WorkspaceMember = Depends(require_workspace_member)) -> WorkspaceMember:
        if membership.role not in allowed_roles:
            raise ForbiddenError("Insufficient permissions for this action")
        return membership

    return dependency


# The RBAC table in one place (see README "Permission model").
can_read = require_workspace_member
can_write_tickets = require_workspace_role("OWNER", "MEMBER")
can_delete_tickets = require_workspace_role("OWNER")
can_manage_members = require_workspace_role("OWNER")
