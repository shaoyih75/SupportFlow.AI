from uuid import UUID

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.models import Ticket, TicketPriority, TicketStatus, User, Workspace, WorkspaceMember


class PostgresUserRepository:
    def __init__(self, session: Session):
        self.session = session

    def get(self, user_id: UUID) -> User | None:
        return self.session.get(User, user_id)

    def get_by_email(self, email: str) -> User | None:
        return self.session.scalar(select(User).where(User.email == email))

    def add(self, user: User) -> User:
        self.session.add(user)
        self.session.flush()  # send INSERT now: surfaces unique violations early, still rollback-able
        return user


class PostgresWorkspaceRepository:
    def __init__(self, session: Session):
        self.session = session

    def get(self, workspace_id: UUID) -> Workspace | None:
        return self.session.get(Workspace, workspace_id)

    def add(self, workspace: Workspace) -> Workspace:
        self.session.add(workspace)
        self.session.flush()
        return workspace

    def add_member(self, member: WorkspaceMember) -> WorkspaceMember:
        self.session.add(member)
        self.session.flush()
        return member

    def get_active_membership(self, workspace_id: UUID, user_id: UUID) -> WorkspaceMember | None:
        stmt = select(WorkspaceMember).where(
            WorkspaceMember.workspace_id == workspace_id,
            WorkspaceMember.user_id == user_id,
            WorkspaceMember.status == "ACTIVE",
        )
        return self.session.scalar(stmt)

    def list_for_user(self, user_id: UUID) -> list[tuple[Workspace, WorkspaceMember]]:
        stmt = (
            select(Workspace, WorkspaceMember)
            .join(WorkspaceMember, WorkspaceMember.workspace_id == Workspace.id)
            .where(WorkspaceMember.user_id == user_id, WorkspaceMember.status == "ACTIVE")
            .order_by(Workspace.created_at)
        )
        return [(ws, m) for ws, m in self.session.execute(stmt).all()]

    def count_members(self, workspace_id: UUID) -> int:
        stmt = select(func.count()).where(
            WorkspaceMember.workspace_id == workspace_id, WorkspaceMember.status == "ACTIVE"
        )
        return self.session.scalar(stmt) or 0


class PostgresTicketRepository:
    def __init__(self, session: Session):
        self.session = session

    def add(self, ticket: Ticket) -> Ticket:
        self.session.add(ticket)
        self.session.flush()
        return ticket

    def get(self, workspace_id: UUID, ticket_id: UUID) -> Ticket | None:
        # Filter by BOTH ids. Never fetch by ticket_id alone and "remember" to check later.
        stmt = select(Ticket).where(Ticket.id == ticket_id, Ticket.workspace_id == workspace_id)
        return self.session.scalar(stmt)

    def list(
        self,
        workspace_id: UUID,
        *,
        status: TicketStatus | None,
        priority: TicketPriority | None,
        offset: int,
        limit: int,
    ) -> tuple[list[Ticket], int]:
        conditions = [Ticket.workspace_id == workspace_id]
        if status is not None:
            conditions.append(Ticket.status == status)
        if priority is not None:
            conditions.append(Ticket.priority == priority)

        total = self.session.scalar(select(func.count()).select_from(Ticket).where(*conditions)) or 0
        # id as a tie-breaker keeps page boundaries stable when created_at values are equal.
        stmt = (
            select(Ticket)
            .where(*conditions)
            .order_by(Ticket.created_at.desc(), Ticket.id.desc())
            .offset(offset)
            .limit(limit)
        )
        return list(self.session.scalars(stmt)), total

    def update(self, ticket: Ticket, changes: dict) -> Ticket:
        for field, value in changes.items():
            setattr(ticket, field, value)
        self.session.flush()
        return ticket

    def delete(self, ticket: Ticket) -> None:
        self.session.delete(ticket)
        self.session.flush()
