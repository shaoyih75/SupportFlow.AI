from uuid import UUID

from fastapi import APIRouter, Depends, Query, Response

from app.deps import get_current_user, get_ticket_service
from app.models import TicketPriority, TicketStatus, User
from app.schemas.common import Page
from app.schemas.ticket import TicketCreate, TicketResponse, TicketUpdate
from app.services.ticket_service import TicketService

# Every ticket route lives under its workspace, so the workspace boundary is part of the URL
# and the repository can always query by (workspace_id, ticket_id).
router = APIRouter(prefix="/workspaces/{workspace_id}/tickets", tags=["tickets"])


@router.get("", response_model=Page[TicketResponse])
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


@router.post("", response_model=TicketResponse, status_code=201)
def create_ticket(
    workspace_id: UUID,
    payload: TicketCreate,
    user: User = Depends(get_current_user),
    service: TicketService = Depends(get_ticket_service),
):
    return service.create(workspace_id, payload, user)


@router.get("/{ticket_id}", response_model=TicketResponse)
def get_ticket(
    workspace_id: UUID,
    ticket_id: UUID,
    user: User = Depends(get_current_user),
    service: TicketService = Depends(get_ticket_service),
):
    return service.get(workspace_id, ticket_id, user)


@router.patch("/{ticket_id}", response_model=TicketResponse)
def update_ticket(
    workspace_id: UUID,
    ticket_id: UUID,
    payload: TicketUpdate,
    user: User = Depends(get_current_user),
    service: TicketService = Depends(get_ticket_service),
):
    return service.update(workspace_id, ticket_id, payload, user)


@router.delete("/{ticket_id}", status_code=204)
def delete_ticket(
    workspace_id: UUID,
    ticket_id: UUID,
    user: User = Depends(get_current_user),
    service: TicketService = Depends(get_ticket_service),
):
    service.delete(workspace_id, ticket_id, user)
    return Response(status_code=204)
