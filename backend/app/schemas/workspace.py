from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, EmailStr, Field

from app.models import MembershipStatus, Role


class WorkspaceCreate(BaseModel):
    name: str = Field(min_length=1, max_length=100)


class WorkspaceResponse(BaseModel):
    id: UUID
    name: str
    role: Role  # the current user's role in this workspace
    member_count: int
    created_at: datetime


class MemberCreate(BaseModel):
    # Who and which role. Never "which workspace": that comes from the URL.
    email: EmailStr
    role: Role = "MEMBER"


class MemberResponse(BaseModel):
    user_id: UUID
    name: str
    email: str
    role: Role
    status: MembershipStatus
    joined_at: datetime
