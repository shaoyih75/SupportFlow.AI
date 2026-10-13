from dataclasses import asdict
from datetime import datetime, timezone
from uuid import UUID, uuid4

from app.errors import NotFoundError
from app.models import Ticket, TicketPriority, TicketStatus, User
from app.repositories.memory import InMemoryRepository
from app.schemas.common import Page
from app.schemas.ticket import TicketCreate, TicketResponse
from app.services.workspace_service import WorkspaceService


class TicketService:
    def __init__(self, repo: InMemoryRepository, workspaces: WorkspaceService):
        self.repo = repo
        self.workspaces = workspaces

    def list(
        self,
        workspace_id: UUID,
        user: User,
        *,
        page: int,
        page_size: int,
        status: TicketStatus | None,
        priority: TicketPriority | None,
    ) -> Page[TicketResponse]:
        self.workspaces.require_member(workspace_id, user)
        items, total = self.repo.list_tickets(
            workspace_id, status=status, priority=priority, offset=(page - 1) * page_size, limit=page_size
        )
        return Page[TicketResponse](
            items=[self._to_response(t) for t in items], page=page, page_size=page_size, total=total
        )

    def create(self, workspace_id: UUID, payload: TicketCreate, user: User) -> TicketResponse:
        self.workspaces.require_member(workspace_id, user)
        ticket = Ticket(
            id=uuid4(),
            workspace_id=workspace_id,
            subject=payload.subject.strip(),
            priority=payload.priority,
            status="OPEN",  # business rule: new tickets always start OPEN
            created_at=datetime.now(timezone.utc),
        )
        return self._to_response(self.repo.add_ticket(ticket))

    def get(self, ticket_id: UUID, user: User) -> TicketResponse:
        return self._to_response(self._get_accessible(ticket_id, user))

    def delete(self, ticket_id: UUID, user: User) -> None:
        self._get_accessible(ticket_id, user)
        self.repo.delete_ticket(ticket_id)

    # TODO (class challenge): def update(self, ticket_id: UUID, payload: TicketUpdate, user: User) -> TicketResponse
    #   Hint: reuse _get_accessible, then apply only the fields the client sent
    #   (payload.model_dump(exclude_unset=True)).

    def _get_accessible(self, ticket_id: UUID, user: User) -> Ticket:
        ticket = self.repo.get_ticket(ticket_id)
        if ticket is None:
            raise NotFoundError("ticket")
        # Having a workspace_id on the ticket is not permission: check membership.
        self.workspaces.require_member(ticket.workspace_id, user)
        return ticket

    @staticmethod
    def _to_response(ticket: Ticket) -> TicketResponse:
        return TicketResponse(**asdict(ticket))
