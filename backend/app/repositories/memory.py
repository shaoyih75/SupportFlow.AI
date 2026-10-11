"""In-memory repository. Next lesson: same methods, backed by PostgreSQL + SQLAlchemy."""

from datetime import datetime, timedelta, timezone
from uuid import UUID, uuid4

from app.models import Ticket, TicketPriority, TicketStatus, User, Workspace, WorkspaceMember

# Fixed ids so the frontend and curl examples can rely on them.
ALICE_ID = UUID("00000000-0000-0000-0000-000000000001")
BOB_ID = UUID("00000000-0000-0000-0000-000000000002")
ACME_WS_ID = UUID("11111111-1111-1111-1111-111111111111")
NEW_TEAM_WS_ID = UUID("22222222-2222-2222-2222-222222222222")
BOB_WS_ID = UUID("33333333-3333-3333-3333-333333333333")


class InMemoryRepository:
    def __init__(self) -> None:
        self.users: dict[UUID, User] = {}
        self.workspaces: dict[UUID, Workspace] = {}
        self.members: list[WorkspaceMember] = []
        self.tickets: dict[UUID, Ticket] = {}

    # --- users ---
    def get_user(self, user_id: UUID) -> User | None:
        return self.users.get(user_id)

    # --- workspaces ---
    def get_workspace(self, workspace_id: UUID) -> Workspace | None:
        return self.workspaces.get(workspace_id)

    def add_workspace(self, workspace: Workspace) -> Workspace:
        self.workspaces[workspace.id] = workspace
        return workspace

    def add_member(self, member: WorkspaceMember) -> WorkspaceMember:
        self.members.append(member)
        return member

    def get_membership(self, workspace_id: UUID, user_id: UUID) -> WorkspaceMember | None:
        return next((m for m in self.members if m.workspace_id == workspace_id and m.user_id == user_id), None)

    def list_memberships(self, user_id: UUID) -> list[WorkspaceMember]:
        return [m for m in self.members if m.user_id == user_id]

    def count_members(self, workspace_id: UUID) -> int:
        return sum(1 for m in self.members if m.workspace_id == workspace_id)

    # --- tickets ---
    def get_ticket(self, ticket_id: UUID) -> Ticket | None:
        return self.tickets.get(ticket_id)

    def add_ticket(self, ticket: Ticket) -> Ticket:
        self.tickets[ticket.id] = ticket
        return ticket

    def delete_ticket(self, ticket_id: UUID) -> None:
        self.tickets.pop(ticket_id, None)

    def list_tickets(
        self,
        workspace_id: UUID,
        *,
        status: TicketStatus | None,
        priority: TicketPriority | None,
        offset: int,
        limit: int,
    ) -> tuple[list[Ticket], int]:
        matches = [
            t
            for t in self.tickets.values()
            if t.workspace_id == workspace_id
            and (status is None or t.status == status)
            and (priority is None or t.priority == priority)
        ]
        matches.sort(key=lambda t: t.created_at, reverse=True)
        return matches[offset : offset + limit], len(matches)


def build_seeded_repository() -> InMemoryRepository:
    repo = InMemoryRepository()
    now = datetime.now(timezone.utc)

    repo.users[ALICE_ID] = User(ALICE_ID, "Alice Chen", "alice@example.com")
    repo.users[BOB_ID] = User(BOB_ID, "Bob Lee", "bob@example.com")

    for ws_id, name, owner in [
        (ACME_WS_ID, "Acme Support", ALICE_ID),
        (NEW_TEAM_WS_ID, "New Team", ALICE_ID),
        (BOB_WS_ID, "Bob's Private Workspace", BOB_ID),  # Alice is NOT a member → 403 demo
    ]:
        repo.add_workspace(Workspace(ws_id, name, owner, now - timedelta(days=30)))
        repo.add_member(WorkspaceMember(ws_id, owner, "OWNER"))
    repo.add_member(WorkspaceMember(ACME_WS_ID, BOB_ID, "MEMBER"))

    seed: list[tuple[str, TicketPriority, TicketStatus, int]] = [
        ("Customer cannot reset password", "HIGH", "OPEN", 1),
        ("Refund request for duplicate charge", "MEDIUM", "IN_PROGRESS", 5),
        ("How to export invoices as CSV?", "LOW", "RESOLVED", 30),
        ("API returns 429 during bulk import", "HIGH", "OPEN", 3),
        ("Update billing contact email", "LOW", "RESOLVED", 60),
    ]
    for subject, priority, status, hours_ago in seed:
        repo.add_ticket(Ticket(uuid4(), ACME_WS_ID, subject, priority, status, now - timedelta(hours=hours_ago)))
    repo.add_ticket(Ticket(uuid4(), BOB_WS_ID, "Bob's secret ticket", "LOW", "OPEN", now))
    return repo
