from uuid import UUID

from fastapi import APIRouter, Depends, Query, Response

from app.deps import get_current_user, get_ticket_service
from app.models import TicketPriority, TicketStatus, User
from app.schemas.common import Page
from app.schemas.ticket import TicketCreate, TicketResponse
from app.services.ticket_service import TicketService

router = APIRouter(tags=["tickets"])


@router.get("/workspaces/{workspace_id}/tickets", response_model=Page[TicketResponse])
def list_tickets(
    workspace_id: UUID,
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    status: TicketStatus | None = None,
    priority: TicketPriority | None = None,
    user: User = Depends(get_current_user),
    service: TicketService = Depends(get_ticket_service),
):
    return service.list(workspace_id, user, page=page, page_size=page_size, status=status, priority=priority)


@router.post("/workspaces/{workspace_id}/tickets", response_model=TicketResponse, status_code=201)
def create_ticket(
    workspace_id: UUID,
    payload: TicketCreate,
    user: User = Depends(get_current_user),
    service: TicketService = Depends(get_ticket_service),
):
    return service.create(workspace_id, payload, user)


@router.get("/tickets/{ticket_id}", response_model=TicketResponse)
def get_ticket(
    ticket_id: UUID,
    user: User = Depends(get_current_user),
    service: TicketService = Depends(get_ticket_service),
):
    return service.get(ticket_id, user)


@router.delete("/tickets/{ticket_id}", status_code=204)
def delete_ticket(
    ticket_id: UUID,
    user: User = Depends(get_current_user),
    service: TicketService = Depends(get_ticket_service),
):
    service.delete(ticket_id, user)
    return Response(status_code=204)


# TODO (class challenge): PATCH /tickets/{ticket_id}
#   - body: TicketUpdate (app/schemas/ticket.py), response: TicketResponse, 200
#   - call service.update(...); do not modify data in the route
