"""Storage models: what the repository keeps. Never returned directly from a route;
routes return Pydantic Response schemas instead."""

from dataclasses import dataclass
from datetime import datetime
from typing import Literal
from uuid import UUID

Role = Literal["OWNER", "MEMBER"]
TicketStatus = Literal["OPEN", "IN_PROGRESS", "RESOLVED"]
TicketPriority = Literal["LOW", "MEDIUM", "HIGH"]


@dataclass
class User:
    id: UUID
    name: str
    email: str


@dataclass
class Workspace:
    id: UUID
    name: str
    owner_user_id: UUID
    created_at: datetime


@dataclass
class WorkspaceMember:
    workspace_id: UUID
    user_id: UUID
    role: Role


@dataclass
class Ticket:
    id: UUID
    workspace_id: UUID
    subject: str
    priority: TicketPriority
    status: TicketStatus
    created_at: datetime
