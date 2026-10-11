from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, Field

from app.models import TicketPriority, TicketStatus


class TicketCreate(BaseModel):
    # No id / workspace_id / status / created_at: the URL and the server decide those.
    subject: str = Field(min_length=3, max_length=200)
    priority: TicketPriority


class TicketUpdate(BaseModel):
    # Used by PATCH /api/tickets/{ticket_id} (class challenge). Every field is optional.
    subject: str | None = Field(default=None, min_length=3, max_length=200)
    priority: TicketPriority | None = None
    status: TicketStatus | None = None


class TicketResponse(BaseModel):
    id: UUID
    workspace_id: UUID
    subject: str
    priority: TicketPriority
    status: TicketStatus
    created_at: datetime
