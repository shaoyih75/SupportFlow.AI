"""Lesson 4: the five persistence checks, plus duplicate-email 409.
Each test names WHO stops the bad case: the database (constraints) or the service (rules)."""

from uuid import uuid4

import pytest
from psycopg import errors as pg_errors
from sqlalchemy import create_engine, func, select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.models import Ticket, User, Workspace, WorkspaceMember
from app.repositories.postgres import PostgresUserRepository, PostgresWorkspaceRepository
from app.schemas.auth import RegisterRequest
from app.seed import ACME_WS_ID, ALICE_ID, NEW_TEAM_WS_ID
from app.services.user_service import UserService

from .conftest import TEST_DATABASE_URL, login


def test_ticket_persists_after_api_restart(client, alice):
    created = client.post(
        f"/api/workspaces/{ACME_WS_ID}/tickets", json={"subject": "Survives a restart", "priority": "HIGH"}, headers=alice
    )
    assert created.status_code == 201
    ticket_id = created.json()["id"]

    # "Restart": throw away the app's process-level state by reading through a brand-new
    # engine and connection pool. Only data that reached PostgreSQL can still be found.
    fresh_engine = create_engine(TEST_DATABASE_URL)
    try:
        with Session(fresh_engine) as s:
            ticket = s.get(Ticket, ticket_id)
            assert ticket is not None
            assert ticket.subject == "Survives a restart"
    finally:
        fresh_engine.dispose()

    again = client.get(f"/api/workspaces/{ACME_WS_ID}/tickets/{ticket_id}", headers=alice)
    assert again.status_code == 200
    assert again.json()["id"] == ticket_id


def test_ticket_with_missing_workspace_is_rejected_by_foreign_key(session):
    # Bypasses the API on purpose: the database itself must refuse orphan rows.
    session.add(Ticket(workspace_id=uuid4(), subject="Orphan ticket", priority="LOW", status="OPEN"))
    with pytest.raises(IntegrityError) as exc_info:
        session.flush()
    assert isinstance(exc_info.value.orig, pg_errors.ForeignKeyViolation)


def test_duplicate_membership_is_rejected_by_unique_constraint(session):
    # Alice is already OWNER of Acme (seed). A second row for the same pair must fail.
    session.add(WorkspaceMember(workspace_id=ACME_WS_ID, user_id=ALICE_ID, role="MEMBER"))
    with pytest.raises(IntegrityError) as exc_info:
        session.flush()
    assert isinstance(exc_info.value.orig, pg_errors.UniqueViolation)
    assert "uq_workspace_member" in str(exc_info.value.orig)


def test_ticket_cannot_be_read_through_another_workspace(client, alice):
    # Alice belongs to both workspaces, so membership passes; the scoped query is what stops it.
    ticket_id = client.post(
        f"/api/workspaces/{ACME_WS_ID}/tickets", json={"subject": "Acme only", "priority": "LOW"}, headers=alice
    ).json()["id"]

    leaked = client.get(f"/api/workspaces/{NEW_TEAM_WS_ID}/tickets/{ticket_id}", headers=alice)
    assert leaked.status_code == 404
    assert leaked.json()["error"]["code"] == "TICKET_NOT_FOUND"
    assert "Acme only" not in leaked.text

    for method, body in [("patch", {"status": "RESOLVED"}), ("delete", None)]:
        response = client.request(
            method, f"/api/workspaces/{NEW_TEAM_WS_ID}/tickets/{ticket_id}", json=body, headers=alice
        )
        assert response.status_code == 404


class FailingWorkspaceRepository(PostgresWorkspaceRepository):
    def add_member(self, member):
        raise RuntimeError("simulated failure while creating the membership")


def test_register_rolls_back_user_and_workspace_when_membership_fails(session):
    service = UserService(session, PostgresUserRepository(session), FailingWorkspaceRepository(session))

    with pytest.raises(RuntimeError):
        service.register(RegisterRequest(name="Rollback", email="rollback@example.com", password="long-enough"))

    # User and Workspace were already flushed (INSERT sent) before the failure,
    # but the transaction was rolled back, so neither row survives.
    assert session.scalar(select(User).where(User.email == "rollback@example.com")) is None
    assert session.scalar(select(func.count()).select_from(Workspace).where(Workspace.name == "Rollback's Workspace")) == 0


def test_register_duplicate_email_returns_409(client):
    first = client.post(
        "/api/auth/register", json={"name": "Haoxuan", "email": "haoxuan@example.com", "password": "haoxuan-pass"}
    )
    assert first.status_code == 201
    assert "password" not in first.text  # neither the password nor its hash is ever returned

    workspace_id = first.json()["personal_workspace_id"]
    headers = login(client, "haoxuan@example.com", "haoxuan-pass")
    workspaces = client.get("/api/workspaces", headers=headers).json()
    assert [(w["id"], w["role"]) for w in workspaces] == [(workspace_id, "OWNER")]

    second = client.post(
        "/api/auth/register", json={"name": "Other", "email": "HAOXUAN@example.com", "password": "another-pass"}
    )
    assert second.status_code == 409
    assert second.json()["error"]["code"] == "EMAIL_ALREADY_EXISTS"
