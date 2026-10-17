"""Lesson 6: authentication (401), membership (403), RBAC (403) and tenant isolation (404).

Seeded roles:  Alice = OWNER of Acme (workspace A) · Bob = OWNER of Bob's workspace (B), MEMBER of Acme
               Carol = VIEWER of Acme
"""

from datetime import datetime, timedelta, timezone
from uuid import uuid4

import jwt
import pytest
from sqlalchemy import select

from app.config import JWT_ALGORITHM, JWT_SECRET_KEY
from app.models import Ticket, WorkspaceMember
from app.seed import ACME_WS_ID, ALICE_ID, BOB_ID, BOB_WS_ID, NEW_TEAM_WS_ID

from .conftest import login

WS_A, WS_B = ACME_WS_ID, BOB_WS_ID


@pytest.fixture
def ticket_a(session):
    return session.scalar(select(Ticket).where(Ticket.workspace_id == WS_A).order_by(Ticket.created_at.desc()))


@pytest.fixture
def ticket_b(session):
    return session.scalar(select(Ticket).where(Ticket.workspace_id == WS_B))


def url(ws, ticket=None):
    return f"/api/workspaces/{ws}/tickets" + (f"/{ticket.id}" if ticket else "")


def token_for(sub: str, *, minutes: int = 5, key: str = JWT_SECRET_KEY) -> dict[str, str]:
    now = datetime.now(timezone.utc)
    token = jwt.encode({"sub": sub, "iat": now, "exp": now + timedelta(minutes=minutes)}, key, algorithm=JWT_ALGORITHM)
    return {"Authorization": f"Bearer {token}"}


# ---------- Completion Gate (doc order) ----------

def test_gate_1_alice_reads_her_own_ticket(client, alice, ticket_a):
    response = client.get(url(WS_A, ticket_a), headers=alice)
    assert response.status_code == 200
    assert response.json()["workspace_id"] == str(WS_A)


def test_gate_2_alice_cannot_enter_bobs_workspace(client, alice, ticket_b):
    response = client.get(url(WS_B, ticket_b), headers=alice)
    assert response.status_code == 403
    assert "Bob's secret ticket" not in response.text


def test_gate_3_bobs_ticket_id_in_alices_workspace_is_404_for_every_verb(client, alice, ticket_b, session):
    for method, body in [("get", None), ("patch", {"status": "RESOLVED"}), ("delete", None)]:
        response = client.request(method, url(WS_A, ticket_b), json=body, headers=alice)
        assert response.status_code == 404, method
        assert response.json()["error"]["code"] == "TICKET_NOT_FOUND"
        assert "Bob's secret ticket" not in response.text

    session.expire_all()
    still_there = session.get(Ticket, ticket_b.id)
    assert still_there is not None and still_there.status == "OPEN"  # neither changed nor deleted


def test_gate_4_viewer_cannot_update_but_owner_can(client, carol, alice, ticket_a, session):
    denied = client.patch(url(WS_A, ticket_a), json={"status": "RESOLVED"}, headers=carol)
    assert denied.status_code == 403
    session.expire_all()
    assert session.get(Ticket, ticket_a.id).status == "OPEN"  # rejected BEFORE any write

    allowed = client.patch(url(WS_A, ticket_a), json={"status": "RESOLVED"}, headers=alice)
    assert allowed.status_code == 200
    assert allowed.json()["status"] == "RESOLVED"


# ---------- 401: who are you? ----------

@pytest.mark.parametrize(
    "headers",
    [
        {},                                                     # no token at all
        {"Authorization": "Bearer not-a-jwt"},                  # garbage
        {"Authorization": "Basic YWxpY2U6cGFzc3dvcmQ="},        # wrong scheme
    ],
    ids=["missing", "malformed", "wrong-scheme"],
)
def test_requests_without_a_valid_token_are_401(client, headers):
    response = client.get(url(WS_A), headers=headers)
    assert response.status_code == 401
    assert response.headers["WWW-Authenticate"] == "Bearer"
    assert response.json()["error"]["code"] == "UNAUTHORIZED"


def test_expired_forged_and_unknown_user_tokens_are_401(client):
    expired = token_for(str(ALICE_ID), minutes=-1)
    forged = token_for(str(ALICE_ID), key="someone-elses-secret-key-0123456789abcdef")
    ghost = token_for(str(uuid4()))  # well-signed, but no such user
    for headers in (expired, forged, ghost):
        assert client.get(url(WS_A), headers=headers).status_code == 401


def test_login_does_not_reveal_which_emails_exist(client):
    wrong_password = client.post("/api/auth/login", json={"email": "alice@example.com", "password": "nope-nope"})
    unknown_email = client.post("/api/auth/login", json={"email": "nobody@example.com", "password": "nope-nope"})
    assert wrong_password.status_code == unknown_email.status_code == 401
    assert wrong_password.json()["error"]["message"] == unknown_email.json()["error"]["message"]


def test_me_returns_the_token_owner_without_password_hash(client, alice):
    response = client.get("/api/auth/me", headers=alice)
    assert response.status_code == 200
    assert response.json()["email"] == "alice@example.com"
    assert "password" not in response.text


def test_swagger_form_login_issues_a_working_token(client):
    response = client.post("/api/auth/token", data={"username": "alice@example.com", "password": "password123"})
    assert response.status_code == 200
    headers = {"Authorization": f"Bearer {response.json()['access_token']}"}
    assert client.get(url(WS_A), headers=headers).status_code == 200


# ---------- 403: membership ----------

def test_unknown_workspace_looks_the_same_as_a_forbidden_one(client, alice):
    assert client.get(url(uuid4()), headers=alice).status_code == 403


def test_suspended_member_is_locked_out_and_no_longer_lists_the_workspace(client, bob, session):
    assert client.get(url(WS_A), headers=bob).status_code == 200

    membership = session.scalar(
        select(WorkspaceMember).where(WorkspaceMember.workspace_id == WS_A, WorkspaceMember.user_id == BOB_ID)
    )
    membership.status = "SUSPENDED"
    session.commit()

    # Same token as before: permissions are read from the database on every request.
    assert client.get(url(WS_A), headers=bob).status_code == 403
    listed = [w["id"] for w in client.get("/api/workspaces", headers=bob).json()]
    assert str(WS_A) not in listed


# ---------- 403: RBAC table ----------

def test_viewer_can_read_but_not_create(client, carol, ticket_a):
    assert client.get(url(WS_A), headers=carol).status_code == 200
    assert client.get(url(WS_A, ticket_a), headers=carol).status_code == 200
    created = client.post(url(WS_A), json={"subject": "Viewer try", "priority": "LOW"}, headers=carol)
    assert created.status_code == 403


def test_member_can_write_but_only_owner_can_delete(client, bob, alice, ticket_a):
    assert client.post(url(WS_A), json={"subject": "Member ticket", "priority": "LOW"}, headers=bob).status_code == 201
    assert client.patch(url(WS_A, ticket_a), json={"priority": "LOW"}, headers=bob).status_code == 200
    assert client.delete(url(WS_A, ticket_a), headers=bob).status_code == 403
    assert client.delete(url(WS_A, ticket_a), headers=alice).status_code == 204


def test_only_owner_manages_members(client, alice, bob, carol):
    members_url = f"/api/workspaces/{NEW_TEAM_WS_ID}/members"
    acme_members_url = f"/api/workspaces/{WS_A}/members"

    assert client.post(acme_members_url, json={"email": "bob@example.com"}, headers=carol).status_code == 403
    assert client.post(acme_members_url, json={"email": "carol@example.com"}, headers=bob).status_code == 403

    added = client.post(members_url, json={"email": "carol@example.com", "role": "VIEWER"}, headers=alice)
    assert added.status_code == 201
    assert added.json()["role"] == "VIEWER"
    again = client.post(members_url, json={"email": "carol@example.com"}, headers=alice)
    assert again.status_code == 409

    last_owner = client.delete(f"{members_url}/{ALICE_ID}", headers=alice)
    assert last_owner.status_code == 409
    assert last_owner.json()["error"]["code"] == "LAST_OWNER"


def test_role_cannot_be_smuggled_in_the_request(client, carol, ticket_a):
    # Role comes from the database, never from a header or the body.
    response = client.patch(
        url(WS_A, ticket_a),
        json={"status": "RESOLVED", "role": "OWNER", "user_id": str(ALICE_ID)},
        headers={**carol, "X-Role": "OWNER", "X-User-Id": str(ALICE_ID)},
    )
    assert response.status_code == 403


def test_insecure_idor_demo_route_is_not_mounted_by_default(client, alice, ticket_b):
    response = client.get(f"/api/demo/insecure/tickets/{ticket_b.id}", headers=alice)
    assert response.status_code == 404
    assert "Bob's secret ticket" not in response.text


# ---------- Self-service: register → log in → create a workspace ----------

def test_register_rejects_invalid_input_with_field_errors(client):
    response = client.post("/api/auth/register", json={"name": "", "email": "not-an-email", "password": "short"})
    assert response.status_code == 422
    fields = {d["field"] for d in response.json()["error"]["details"]}
    assert fields == {"name", "email", "password"}  # the register form shows these next to each input


def test_new_user_creates_a_workspace_as_owner_and_can_create_tickets(client):
    registered = client.post(
        "/api/auth/register", json={"name": "Dana", "email": "dana@example.com", "password": "dana-pass"}
    )
    assert registered.status_code == 201
    headers = login(client, "dana@example.com", "dana-pass")
    # A brand-new user only sees the personal workspace created at registration, nobody else's.
    assert [w["id"] for w in client.get("/api/workspaces", headers=headers).json()] == [
        registered.json()["personal_workspace_id"]
    ]

    created = client.post("/api/workspaces", json={"name": "Dana's Team"}, headers=headers)
    assert created.status_code == 201
    workspace = created.json()
    assert (workspace["name"], workspace["role"], workspace["member_count"]) == ("Dana's Team", "OWNER", 1)

    ticket = client.post(url(workspace["id"]), json={"subject": "First ticket", "priority": "LOW"}, headers=headers)
    assert ticket.status_code == 201
    assert ticket.json()["workspace_id"] == workspace["id"]
    assert len(client.get("/api/workspaces", headers=headers).json()) == 2
