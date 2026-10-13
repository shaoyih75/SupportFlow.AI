"""Dependencies injected with Depends(). Route code never builds these objects itself,
so switching storage (in-memory → PostgreSQL) only changed this file and the repositories."""

from uuid import UUID

from fastapi import Depends, Header
from sqlalchemy.orm import Session

from app.db.session import get_session
from app.errors import UnauthorizedError
from app.models import User
from app.repositories.postgres import PostgresTicketRepository, PostgresUserRepository, PostgresWorkspaceRepository
from app.seed import ALICE_ID
from app.services.ticket_service import TicketService
from app.services.user_service import UserService
from app.services.workspace_service import WorkspaceService


def get_user_repository(session: Session = Depends(get_session)) -> PostgresUserRepository:
    return PostgresUserRepository(session)


def get_workspace_repository(session: Session = Depends(get_session)) -> PostgresWorkspaceRepository:
    return PostgresWorkspaceRepository(session)


def get_ticket_repository(session: Session = Depends(get_session)) -> PostgresTicketRepository:
    return PostgresTicketRepository(session)


def get_current_user(
    x_user_id: str | None = Header(default=None),
    users: PostgresUserRepository = Depends(get_user_repository),
) -> User:
    # No login yet: the X-User-Id header picks the user, defaulting to seeded Alice.
    # A later lesson replaces this with a real access token.
    try:
        user_id = UUID(x_user_id) if x_user_id else ALICE_ID
    except ValueError:
        raise UnauthorizedError("Invalid X-User-Id header")
    user = users.get(user_id)
    if user is None:
        raise UnauthorizedError("Unknown user (did you run `python -m app.seed`?)")
    return user


def get_workspace_service(
    session: Session = Depends(get_session),
    workspaces: PostgresWorkspaceRepository = Depends(get_workspace_repository),
) -> WorkspaceService:
    return WorkspaceService(session, workspaces)


def get_ticket_service(
    session: Session = Depends(get_session),
    tickets: PostgresTicketRepository = Depends(get_ticket_repository),
    workspaces: WorkspaceService = Depends(get_workspace_service),
) -> TicketService:
    return TicketService(session, tickets, workspaces)


def get_user_service(
    session: Session = Depends(get_session),
    users: PostgresUserRepository = Depends(get_user_repository),
    workspaces: PostgresWorkspaceRepository = Depends(get_workspace_repository),
) -> UserService:
    return UserService(session, users, workspaces)
