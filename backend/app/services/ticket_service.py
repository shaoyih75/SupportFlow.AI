from uuid import UUID

from sqlalchemy.orm import Session

from app.db.session import transaction
from app.errors import NotFoundError
from app.models import Ticket, TicketPriority, TicketStatus, User
from app.repositories.base import TicketRepository
from app.schemas.common import Page
from app.schemas.ticket import TicketCreate, TicketResponse, TicketUpdate
from app.services.workspace_service import WorkspaceService


class TicketService:
    def __init__(self, session: Session, tickets: TicketRepository, workspaces: WorkspaceService):
        self.session = session
        self.tickets = tickets
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
        items, total = self.tickets.list(
            workspace_id, status=status, priority=priority, offset=(page - 1) * page_size, limit=page_size
        )
        return Page[TicketResponse](
            items=[TicketResponse.model_validate(t) for t in items], page=page, page_size=page_size, total=total
        )

    def create(self, workspace_id: UUID, payload: TicketCreate, user: User) -> TicketResponse:
        self.workspaces.require_member(workspace_id, user)
        with transaction(self.session):
            ticket = self.tickets.add(
                Ticket(
                    workspace_id=workspace_id,
                    subject=payload.subject.strip(),
                    priority=payload.priority,
                    status="OPEN",  # business rule: new tickets always start OPEN
                )
            )
        return TicketResponse.model_validate(ticket)

    def get(self, workspace_id: UUID, ticket_id: UUID, user: User) -> TicketResponse:
        return TicketResponse.model_validate(self._get_accessible(workspace_id, ticket_id, user))

    def update(self, workspace_id: UUID, ticket_id: UUID, payload: TicketUpdate, user: User) -> TicketResponse:
        ticket = self._get_accessible(workspace_id, ticket_id, user)
        changes = payload.model_dump(exclude_unset=True)  # only fields the client actually sent
        if "subject" in changes and changes["subject"] is not None:
            changes["subject"] = changes["subject"].strip()
        # null for a required column means "not provided", not "erase it"
        changes = {k: v for k, v in changes.items() if v is not None}
        with transaction(self.session):
            self.tickets.update(ticket, changes)
        return TicketResponse.model_validate(ticket)

    def delete(self, workspace_id: UUID, ticket_id: UUID, user: User) -> None:
        ticket = self._get_accessible(workspace_id, ticket_id, user)
        with transaction(self.session):
            self.tickets.delete(ticket)

    def _get_accessible(self, workspace_id: UUID, ticket_id: UUID, user: User) -> Ticket:
        self.workspaces.require_member(workspace_id, user)
        # Scoped lookup: a ticket from another workspace is simply "not found" here,
        # so the response does not reveal that the id exists elsewhere.
        ticket = self.tickets.get(workspace_id, ticket_id)
        if ticket is None:
            raise NotFoundError("ticket")
        return ticket
