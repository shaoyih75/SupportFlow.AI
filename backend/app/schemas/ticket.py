from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field

from app.models import TicketPriority, TicketStatus


class TicketCreate(BaseModel):
    # No id / workspace_id / status / created_at: the URL and the server decide those.
    subject: str = Field(min_length=3, max_length=200)
    priority: TicketPriority


class TicketUpdate(BaseModel):
    # PATCH: every field is optional; only the fields the client sends are changed.
    subject: str | None = Field(default=None, min_length=3, max_length=200)
    priority: TicketPriority | None = None
    status: TicketStatus | None = None


class TicketResponse(BaseModel):
    # Built from the SQLAlchemy Ticket via model_validate(ticket). Only these fields are
    # exposed; ORM-only columns such as updated_at stay internal.
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    workspace_id: UUID
    subject: str
    priority: TicketPriority
    status: TicketStatus
    created_at: datetime
