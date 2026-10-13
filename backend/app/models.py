"""SQLAlchemy ORM models = how data is stored in PostgreSQL.

These are NOT the API contract. Routes return Pydantic schemas (app/schemas),
so adding an internal column here never leaks into API responses.
"""

from datetime import datetime
from typing import Literal
from uuid import UUID, uuid4

from sqlalchemy import CheckConstraint, DateTime, ForeignKey, Index, String, Text, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base, utcnow

Role = Literal["OWNER", "MEMBER"]
MembershipStatus = Literal["ACTIVE", "REMOVED"]
TicketStatus = Literal["OPEN", "IN_PROGRESS", "RESOLVED"]
TicketPriority = Literal["LOW", "MEDIUM", "HIGH"]
DocumentStatus = Literal["UPLOADED", "PROCESSING", "READY", "FAILED"]


class TimestampMixin:
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow, nullable=False)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=utcnow, onupdate=utcnow, nullable=False
    )


class User(TimestampMixin, Base):
    __tablename__ = "users"

    id: Mapped[UUID] = mapped_column(primary_key=True, default=uuid4)
    name: Mapped[str] = mapped_column(String(100), nullable=False)
    # unique=True is a constraint: two concurrent registrations with the same email
    # cannot both succeed, even if both passed a Python "does it exist?" check.
    email: Mapped[str] = mapped_column(String(255), unique=True, nullable=False)

    memberships: Mapped[list["WorkspaceMember"]] = relationship(back_populates="user")


class Workspace(TimestampMixin, Base):
    __tablename__ = "workspaces"

    id: Mapped[UUID] = mapped_column(primary_key=True, default=uuid4)
    name: Mapped[str] = mapped_column(String(100), nullable=False)
    # RESTRICT: a user who still owns workspaces cannot be deleted by accident.
    owner_user_id: Mapped[UUID] = mapped_column(ForeignKey("users.id", ondelete="RESTRICT"), nullable=False)

    memberships: Mapped[list["WorkspaceMember"]] = relationship(back_populates="workspace")


class WorkspaceMember(Base):
    __tablename__ = "workspace_members"
    __table_args__ = (
        # Correctness: a user is in a workspace at most once.
        # It also serves the permission lookup WHERE workspace_id = ? AND user_id = ?.
        UniqueConstraint("workspace_id", "user_id", name="uq_workspace_member"),
        # Query: "workspaces I belong to" → WHERE user_id = ? (the unique index above starts
        # with workspace_id, so it cannot serve this lookup).
        Index("ix_workspace_members_user_id", "user_id"),
        CheckConstraint("role IN ('OWNER', 'MEMBER')", name="role_valid"),
        CheckConstraint("status IN ('ACTIVE', 'REMOVED')", name="status_valid"),
    )

    id: Mapped[UUID] = mapped_column(primary_key=True, default=uuid4)
    workspace_id: Mapped[UUID] = mapped_column(ForeignKey("workspaces.id", ondelete="CASCADE"), nullable=False)
    user_id: Mapped[UUID] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    role: Mapped[str] = mapped_column(String(20), nullable=False)
    status: Mapped[str] = mapped_column(String(20), nullable=False, default="ACTIVE")
    joined_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow, nullable=False)

    workspace: Mapped[Workspace] = relationship(back_populates="memberships")
    user: Mapped[User] = relationship(back_populates="memberships")


class Document(TimestampMixin, Base):
    __tablename__ = "documents"
    __table_args__ = (
        CheckConstraint("source_type IN ('pdf', 'docx', 'markdown', 'url')", name="source_type_valid"),
        CheckConstraint("status IN ('UPLOADED', 'PROCESSING', 'READY', 'FAILED')", name="status_valid"),
        # No extra index yet: there is no Document API query to justify one (next lesson).
    )

    id: Mapped[UUID] = mapped_column(primary_key=True, default=uuid4)
    workspace_id: Mapped[UUID] = mapped_column(ForeignKey("workspaces.id", ondelete="CASCADE"), nullable=False)
    title: Mapped[str] = mapped_column(String(200), nullable=False)
    source_type: Mapped[str] = mapped_column(String(20), nullable=False)
    status: Mapped[str] = mapped_column(String(20), nullable=False, default="UPLOADED")


class Ticket(TimestampMixin, Base):
    __tablename__ = "tickets"
    __table_args__ = (
        # Query: WHERE workspace_id = ? AND status = ? ORDER BY created_at DESC LIMIT 20
        # Column order: tenant filter → equality filter → sort.
        Index("ix_tickets_workspace_status_created", "workspace_id", "status", "created_at"),
        # Query: the default list with no status filter
        # WHERE workspace_id = ? ORDER BY created_at DESC LIMIT 20
        Index("ix_tickets_workspace_created", "workspace_id", "created_at"),
        CheckConstraint("status IN ('OPEN', 'IN_PROGRESS', 'RESOLVED')", name="status_valid"),
        CheckConstraint("priority IN ('LOW', 'MEDIUM', 'HIGH')", name="priority_valid"),
    )

    id: Mapped[UUID] = mapped_column(primary_key=True, default=uuid4)
    workspace_id: Mapped[UUID] = mapped_column(ForeignKey("workspaces.id", ondelete="CASCADE"), nullable=False)
    subject: Mapped[str] = mapped_column(String(200), nullable=False)
    priority: Mapped[str] = mapped_column(String(10), nullable=False)
    status: Mapped[str] = mapped_column(String(20), nullable=False, default="OPEN")

    messages: Mapped[list["Message"]] = relationship(back_populates="ticket")


class Message(Base):
    __tablename__ = "messages"
    # No workspace_id column on purpose: a message belongs to a workspace *through* its ticket,
    # so message.workspace_id can never disagree with ticket.workspace_id.
    # No extra index yet: no Message API query exists to justify one.

    id: Mapped[UUID] = mapped_column(primary_key=True, default=uuid4)
    ticket_id: Mapped[UUID] = mapped_column(ForeignKey("tickets.id", ondelete="CASCADE"), nullable=False)
    # SET NULL: keep the conversation history if the author's account is deleted.
    author_user_id: Mapped[UUID | None] = mapped_column(ForeignKey("users.id", ondelete="SET NULL"), nullable=True)
    body: Mapped[str] = mapped_column(Text, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow, nullable=False)

    ticket: Mapped[Ticket] = relationship(back_populates="messages")
