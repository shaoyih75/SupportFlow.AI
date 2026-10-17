"""⚠️ DELIBERATELY INSECURE — Class 6 opening demo only.

Mounted only when ENABLE_IDOR_DEMO=1. It shows an IDOR bug: the caller is authenticated,
but the ticket is fetched by its global id and never checked against the caller's
workspaces, so any logged-in user can read any ticket whose id they know.
Compare with app/api/tickets.py, which uses require_workspace_member + a scoped query.
"""

from uuid import UUID

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.db.session import get_session
from app.deps import get_current_user
from app.errors import NotFoundError
from app.models import Ticket, User
from app.schemas.ticket import TicketResponse

router = APIRouter(prefix="/demo/insecure", tags=["⚠️ insecure demo"])


@router.get("/tickets/{ticket_id}", response_model=TicketResponse)
def get_ticket_bad(
    ticket_id: UUID,
    current_user: User = Depends(get_current_user),  # identity is known...
    session: Session = Depends(get_session),
):
    ticket = session.get(Ticket, ticket_id)  # ...but never used to check access
    if ticket is None:
        raise NotFoundError("ticket")
    return ticket
