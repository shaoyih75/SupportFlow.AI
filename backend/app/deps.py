"""Dependencies injected with Depends(). Tests or a real database can swap these
without touching any route."""

from uuid import UUID

from fastapi import Depends, Header

from app.errors import UnauthorizedError
from app.models import User
from app.repositories.memory import ALICE_ID, InMemoryRepository, build_seeded_repository
from app.services.ticket_service import TicketService
from app.services.workspace_service import WorkspaceService

_repository = build_seeded_repository()


def get_repository() -> InMemoryRepository:
    return _repository


def get_current_user(
    x_user_id: str | None = Header(default=None),
    repo: InMemoryRepository = Depends(get_repository),
) -> User:
    # No login yet: the X-User-Id header picks the user, defaulting to Alice.
    # A later lesson replaces this with a real access token.
    try:
        user_id = UUID(x_user_id) if x_user_id else ALICE_ID
    except ValueError:
        raise UnauthorizedError("Invalid X-User-Id header")
    user = repo.get_user(user_id)
    if user is None:
        raise UnauthorizedError("Unknown user")
    return user


def get_workspace_service(repo: InMemoryRepository = Depends(get_repository)) -> WorkspaceService:
    return WorkspaceService(repo)


def get_ticket_service(
    repo: InMemoryRepository = Depends(get_repository),
    workspaces: WorkspaceService = Depends(get_workspace_service),
) -> TicketService:
    return TicketService(repo, workspaces)
