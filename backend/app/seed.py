"""Demo data with fixed ids (the frontend and curl examples rely on them).

Run after migrating:  python -m app.seed
Safe to run twice: it does nothing if Alice already exists.
"""

from datetime import datetime, timedelta, timezone
from uuid import UUID

ALICE_ID = UUID("00000000-0000-0000-0000-000000000001")
BOB_ID = UUID("00000000-0000-0000-0000-000000000002")
ACME_WS_ID = UUID("11111111-1111-1111-1111-111111111111")
NEW_TEAM_WS_ID = UUID("22222222-2222-2222-2222-222222222222")
BOB_WS_ID = UUID("33333333-3333-3333-3333-333333333333")


def seed(session) -> bool:
    from app.models import Ticket, User, Workspace, WorkspaceMember

    if session.get(User, ALICE_ID) is not None:
        return False

    now = datetime.now(timezone.utc)
    session.add_all([User(id=ALICE_ID, name="Alice Chen", email="alice@example.com"),
                     User(id=BOB_ID, name="Bob Lee", email="bob@example.com")])
    session.flush()

    for ws_id, name, owner in [
        (ACME_WS_ID, "Acme Support", ALICE_ID),
        (NEW_TEAM_WS_ID, "New Team", ALICE_ID),
        (BOB_WS_ID, "Bob's Private Workspace", BOB_ID),  # Alice is NOT a member → 403 demo
    ]:
        session.add(Workspace(id=ws_id, name=name, owner_user_id=owner, created_at=now - timedelta(days=30)))
        session.flush()
        session.add(WorkspaceMember(workspace_id=ws_id, user_id=owner, role="OWNER"))
    session.add(WorkspaceMember(workspace_id=ACME_WS_ID, user_id=BOB_ID, role="MEMBER"))

    for subject, priority, status, hours_ago in [
        ("Customer cannot reset password", "HIGH", "OPEN", 1),
        ("Refund request for duplicate charge", "MEDIUM", "IN_PROGRESS", 5),
        ("How to export invoices as CSV?", "LOW", "RESOLVED", 30),
        ("API returns 429 during bulk import", "HIGH", "OPEN", 3),
        ("Update billing contact email", "LOW", "RESOLVED", 60),
    ]:
        session.add(Ticket(workspace_id=ACME_WS_ID, subject=subject, priority=priority, status=status,
                           created_at=now - timedelta(hours=hours_ago)))
    session.add(Ticket(workspace_id=BOB_WS_ID, subject="Bob's secret ticket", priority="LOW", status="OPEN"))
    return True


if __name__ == "__main__":
    from app.db.session import SessionLocal, transaction

    with SessionLocal() as session, transaction(session):
        created = seed(session)
    print("Seeded demo data." if created else "Demo data already present; nothing to do.")
