from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, Field

from app.models import Role


class WorkspaceCreate(BaseModel):
    name: str = Field(min_length=1, max_length=100)


class WorkspaceResponse(BaseModel):
    id: UUID
    name: str
    role: Role  # the current user's role in this workspace
    member_count: int
    created_at: datetime
