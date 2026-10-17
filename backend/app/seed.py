"""Demo data with fixed ids (the frontend and curl examples rely on them).

Run after migrating:  python -m app.seed
Safe to run again: each user, workspace, membership and the demo tickets are created
only if missing, and demo users without a password get the demo password.

Demo logins (local development only):
    alice@example.com / password123   OWNER of Acme Support and New Team
    bob@example.com   / password123   OWNER of Bob's Private Workspace, MEMBER of Acme Support
    carol@example.com / password123   VIEWER of Acme Support
"""

from datetime import datetime, timedelta, timezone
from uuid import UUID

DEMO_PASSWORD = "password123"

ALICE_ID = UUID("00000000-0000-0000-0000-000000000001")
BOB_ID = UUID("00000000-0000-0000-0000-000000000002")
CAROL_ID = UUID("00000000-0000-0000-0000-000000000003")
ACME_WS_ID = UUID("11111111-1111-1111-1111-111111111111")
NEW_TEAM_WS_ID = UUID("22222222-2222-2222-2222-222222222222")
BOB_WS_ID = UUID("33333333-3333-3333-3333-333333333333")


def seed(session) -> list[str]:
    """Returns what it created or fixed, so a re-run can say "nothing to do"."""
    from sqlalchemy import func, select

    from app.auth.security import hash_password
    from app.models import Ticket, User, Workspace, WorkspaceMember

    done: list[str] = []
    now = datetime.now(timezone.utc)
    password_hash = hash_password(DEMO_PASSWORD)

    for user_id, name, email in [
        (ALICE_ID, "Alice Chen", "alice@example.com"),
        (BOB_ID, "Bob Lee", "bob@example.com"),
        (CAROL_ID, "Carol Wu", "carol@example.com"),
    ]:
        user = session.get(User, user_id)
        if user is None:
            session.add(User(id=user_id, name=name, email=email, password_hash=password_hash))
            done.append(f"user {email}")
        elif user.password_hash is None:
            user.password_hash = password_hash
            done.append(f"password for {email}")
    session.flush()

    for ws_id, name, owner in [
        (ACME_WS_ID, "Acme Support", ALICE_ID),
        (NEW_TEAM_WS_ID, "New Team", ALICE_ID),
        (BOB_WS_ID, "Bob's Private Workspace", BOB_ID),  # Alice is NOT a member → 403 demo
    ]:
        if session.get(Workspace, ws_id) is None:
            session.add(Workspace(id=ws_id, name=name, owner_user_id=owner, created_at=now - timedelta(days=30)))
            done.append(f"workspace {name}")
    session.flush()

    for ws_id, user_id, role in [
        (ACME_WS_ID, ALICE_ID, "OWNER"),
        (NEW_TEAM_WS_ID, ALICE_ID, "OWNER"),
        (BOB_WS_ID, BOB_ID, "OWNER"),
        (ACME_WS_ID, BOB_ID, "MEMBER"),
        (ACME_WS_ID, CAROL_ID, "VIEWER"),
    ]:
        exists = session.scalar(
            select(WorkspaceMember).where(WorkspaceMember.workspace_id == ws_id, WorkspaceMember.user_id == user_id)
        )
        if exists is None:
            session.add(WorkspaceMember(workspace_id=ws_id, user_id=user_id, role=role))
            done.append(f"{role} membership")
    session.flush()

    def has_tickets(ws_id: UUID) -> bool:
        return (session.scalar(select(func.count()).select_from(Ticket).where(Ticket.workspace_id == ws_id)) or 0) > 0

    if not has_tickets(ACME_WS_ID):
        for subject, priority, status, hours_ago in [
            ("Customer cannot reset password", "HIGH", "OPEN", 1),
            ("Refund request for duplicate charge", "MEDIUM", "IN_PROGRESS", 5),
            ("How to export invoices as CSV?", "LOW", "RESOLVED", 30),
            ("API returns 429 during bulk import", "HIGH", "OPEN", 3),
            ("Update billing contact email", "LOW", "RESOLVED", 60),
        ]:
            session.add(Ticket(workspace_id=ACME_WS_ID, subject=subject, priority=priority, status=status,
                               created_at=now - timedelta(hours=hours_ago)))
        done.append("Acme tickets")
    if not has_tickets(BOB_WS_ID):
        session.add(Ticket(workspace_id=BOB_WS_ID, subject="Bob's secret ticket", priority="LOW", status="OPEN"))
        done.append("Bob's ticket")
    return done


if __name__ == "__main__":
    from app.db.session import SessionLocal, transaction

    with SessionLocal() as session, transaction(session):
        created = seed(session)
    if created:
        print("Seeded: " + ", ".join(created) + ".")
        print(f"Demo logins: alice@ / bob@ / carol@example.com, password {DEMO_PASSWORD!r}")
    else:
        print("Demo data already present; nothing to do.")
