from uuid import UUID

from sqlalchemy.orm import Session

from app.db.session import transaction
from app.errors import NotFoundError
from app.models import Ticket, TicketPriority, TicketStatus
from app.repositories.base import TicketRepository
from app.schemas.common import Page
from app.schemas.ticket import TicketCreate, TicketResponse, TicketUpdate


class TicketService:
    """Ticket business rules. Who may call which method is decided BEFORE we get here,
    by require_workspace_member / require_workspace_role in app/deps.py. Every method still
    takes workspace_id, so even an internal caller cannot reach a ticket outside its workspace."""

    def __init__(self, session: Session, tickets: TicketRepository):
        self.session = session
        self.tickets = tickets

    def list(
        self,
        workspace_id: UUID,
        *,
        page: int,
        page_size: int,
        status: TicketStatus | None,
        priority: TicketPriority | None,
    ) -> Page[TicketResponse]:
        items, total = self.tickets.list(
            workspace_id, status=status, priority=priority, offset=(page - 1) * page_size, limit=page_size
        )
        return Page[TicketResponse](
            items=[TicketResponse.model_validate(t) for t in items], page=page, page_size=page_size, total=total
        )

    def create(self, workspace_id: UUID, payload: TicketCreate) -> TicketResponse:
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

    def get(self, workspace_id: UUID, ticket_id: UUID) -> TicketResponse:
        return TicketResponse.model_validate(self._get_or_404(workspace_id, ticket_id))

    def update(self, workspace_id: UUID, ticket_id: UUID, payload: TicketUpdate) -> TicketResponse:
        ticket = self._get_or_404(workspace_id, ticket_id)
        changes = payload.model_dump(exclude_unset=True)  # only fields the client actually sent
        if changes.get("subject") is not None:
            changes["subject"] = changes["subject"].strip()
        # null for a required column means "not provided", not "erase it"
        changes = {k: v for k, v in changes.items() if v is not None}
        with transaction(self.session):
            self.tickets.update(ticket, changes)
        return TicketResponse.model_validate(ticket)

    def delete(self, workspace_id: UUID, ticket_id: UUID) -> None:
        ticket = self._get_or_404(workspace_id, ticket_id)
        with transaction(self.session):
            self.tickets.delete(ticket)

    def _get_or_404(self, workspace_id: UUID, ticket_id: UUID) -> Ticket:
        # A ticket from another workspace is "not found" here: from this caller's
        # authorized scope it does not exist, and we do not confirm that the id is real.
        ticket = self.tickets.get_in_workspace(workspace_id=workspace_id, ticket_id=ticket_id)
        if ticket is None:
            raise NotFoundError("ticket")
        return ticket
