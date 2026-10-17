"""Integration tests run against a real PostgreSQL test database.

TEST_DATABASE_URL (default: the docker compose `supportflow_test` database) is migrated
with Alembic once per test session, and every test starts from freshly seeded data.
"""

import os

from dotenv import load_dotenv

load_dotenv()
TEST_DATABASE_URL = os.environ.get(
    "TEST_DATABASE_URL", "postgresql+psycopg://supportflow:supportflow@localhost:5432/supportflow_test"
)
# Must happen before any `app` import: app.db.session builds its engine from DATABASE_URL.
os.environ["DATABASE_URL"] = TEST_DATABASE_URL

from pathlib import Path  # noqa: E402

import pytest  # noqa: E402
from alembic import command  # noqa: E402
from alembic.config import Config  # noqa: E402
from fastapi.testclient import TestClient  # noqa: E402
from sqlalchemy import text  # noqa: E402

from app.db.session import SessionLocal, engine, transaction  # noqa: E402
from app.main import app  # noqa: E402
from app.seed import seed  # noqa: E402

BACKEND_DIR = Path(__file__).resolve().parent.parent


@pytest.fixture(scope="session", autouse=True)
def migrated_database():
    cfg = Config(str(BACKEND_DIR / "alembic.ini"))
    cfg.set_main_option("script_location", str(BACKEND_DIR / "alembic"))
    cfg.set_main_option("sqlalchemy.url", TEST_DATABASE_URL)
    command.downgrade(cfg, "base")  # also proves downgrade works
    command.upgrade(cfg, "head")
    yield


@pytest.fixture(autouse=True)
def seeded_data():
    with engine.begin() as conn:
        conn.execute(text("TRUNCATE messages, tickets, documents, workspace_members, workspaces, users CASCADE"))
    with SessionLocal() as session, transaction(session):
        seed(session)
    yield


@pytest.fixture
def client():
    return TestClient(app)


def login(client: TestClient, email: str, password: str = "password123") -> dict[str, str]:
    """Log in through the real endpoint and return the Authorization header."""
    response = client.post("/api/auth/login", json={"email": email, "password": password})
    assert response.status_code == 200, response.text
    return {"Authorization": f"Bearer {response.json()['access_token']}"}


@pytest.fixture
def alice(client):  # OWNER of Acme + New Team
    return login(client, "alice@example.com")


@pytest.fixture
def bob(client):  # OWNER of Bob's workspace, MEMBER of Acme
    return login(client, "bob@example.com")


@pytest.fixture
def carol(client):  # VIEWER of Acme
    return login(client, "carol@example.com")


@pytest.fixture
def session():
    with SessionLocal() as s:
        yield s
