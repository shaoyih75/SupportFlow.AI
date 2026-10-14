# SupportFlow.AI

AI knowledge workflow platform for support teams. A FastAPI backend (Workspace + Ticket CRUD) and a Next.js + React frontend.

> **第一次搭建环境？先看 [新人上手指南（中文，逐步说明）](docs/onboarding.zh-CN.md)。** 每一步都写了要输入什么、成功时会看到什么、出错了怎么办。

## Getting started (new machine)

From an empty Mac to the app running at http://localhost:3000 in about 20–30 minutes (mostly downloads). You will use **three terminal windows**: one for database commands, one for the backend, one for the frontend.

### 0. Install the tools (once)

| Tool | Check | Need | Install |
|---|---|---|---|
| Git | `git --version` | any | `xcode-select --install` |
| Python | `python3 --version` | 3.11+ | `brew install python` |
| Node.js | `node -v` | 20.9+ | `brew install node` |
| Docker Desktop | `docker --version` | any | `brew install --cask docker-desktop` (details in [Database with Docker](#database-with-docker-step-by-step)) |
| TablePlus (optional) | | | `brew install --cask tableplus` |

After installing Docker Desktop, open it from Applications and wait until the whale icon in the menu bar stops animating. Then, in a **new** terminal:

```bash
docker run --rm hello-world     # prints "Hello from Docker!"
```

When Homebrew asks for `Password:`, type your Mac login password and press Enter. Nothing appears on screen while you type.

### 1. Get the code

```bash
cd ~/Documents/projects                      # any folder works
git clone https://github.com/shaoyih75/SupportFlow.AI.git
cd SupportFlow.AI
git checkout feature/postgres-persistence    # until this branch is merged into main
```

### 2. Start the database (terminal 1, project root)

```bash
docker compose up -d --wait db               # first run downloads PostgreSQL (~150 MB)
docker compose ps                            # STATUS shows (healthy)
```

### 3. Set up and start the backend (terminal 2, `backend/`)

```bash
cd ~/Documents/projects/SupportFlow.AI/backend
python3 -m venv .venv                        # virtual environment for this project
source .venv/bin/activate                    # the prompt now starts with (.venv)
pip install -r requirements.txt
cp .env.example .env                         # DATABASE_URL / TEST_DATABASE_URL
alembic upgrade head                         # create the six tables
alembic current                              # shows: 0001 (head)
python -m app.seed                           # demo users, workspaces, tickets (safe to re-run)
uvicorn app.main:app --reload --port 8000
```

Check: http://localhost:8000/docs shows the API docs.

Run `alembic upgrade head`, **not** `alembic revision --autogenerate`: the migration file already exists; `revision` is only for after you change `app/models.py`.

### 4. Start the frontend (terminal 3, `frontend/`)

```bash
cd ~/Documents/projects/SupportFlow.AI/frontend
npm install
npm run dev                                  # http://localhost:3000
```

The frontend calls `/api/*`, which Next.js proxies to `http://localhost:8000/api/*`, so the backend must be running.

### 5. Check that everything works

1. Open **Tickets**: 5 demo tickets are listed.
2. Create a ticket: it appears at the top.
3. In terminal 2 press `Ctrl + C`, start `uvicorn app.main:app --reload --port 8000` again, refresh the page: **the new ticket is still there**.
4. Run the tests (in `backend/` with `.venv` active; stop uvicorn first or use another terminal):

```bash
pytest -q                                    # 6 passed
```

### 6. Look at the tables in TablePlus (optional)

Create a new **PostgreSQL** connection:

| Field | Value |
|---|---|
| Host | `localhost` |
| Port | `5432` |
| User | `supportflow` |
| Password | `supportflow` |
| Database | `supportflow` |

Click **Test** (fields turn green), then **Connect**, and double-click `tickets`. Press `⌘ + R` to refresh after changing data in the app. A connection with Database `supportflow_test` shows the test database, which pytest wipes on every run.

Prefer the terminal? `docker compose exec db psql -U supportflow` opens a SQL shell (see [Step 5](#step-5-look-inside-the-database-optional) below).

### Every day after that

No installs, migrations or seeding needed; your data is still there.

```bash
# terminal 1, project root (Docker Desktop must be open)
docker compose up -d --wait db

# terminal 2, backend/
source .venv/bin/activate
uvicorn app.main:app --reload --port 8000

# terminal 3, frontend/
npm run dev
```

After pulling new code, also run `pip install -r requirements.txt` and `alembic upgrade head` (backend) and `npm install` (frontend) in case dependencies or migrations changed.

### Common errors

| Error | Cause | Fix |
|---|---|---|
| `command not found: docker` / `Cannot connect to the Docker daemon` | Docker Desktop not installed or not running | Open Docker, wait for the whale icon, open a new terminal |
| `Connection refused … port 5432` | The database container is not running | `docker compose up -d --wait db` in the project root |
| `No 'script_location' key found` | `alembic` was run outside `backend/` | `cd backend` first |
| `Target database is not up to date` | `alembic revision` was run instead of `upgrade` | Run `alembic upgrade head` |
| `command not found: alembic` / `uvicorn` / `pytest` | The virtual environment is not active | `source .venv/bin/activate` in `backend/` |
| `address already in use` on 8000 or 3000 | Another app uses the port | Stop it, or use `--port 8001` and start the frontend with `BACKEND_URL=http://localhost:8001 npm run dev` |
| The sidebar shows "API offline" | The backend is not running | Start uvicorn in terminal 2 |

More Docker-specific problems: [Troubleshooting](#troubleshooting).

## Data mode

- **Workspaces, Tickets and registration**: FastAPI on **PostgreSQL** (SQLAlchemy 2.0 + Alembic). Data survives API and container restarts.
- **Documents and the AI Assistant**: still mock data inside the frontend (`frontend/lib/mock-data.ts`). The `documents` and `messages` tables already exist for the next lessons.
- No login yet: requests act as the seeded user Alice. Send `X-User-Id: 00000000-0000-0000-0000-000000000002` to act as Bob.

## Structure

```text
docker-compose.yml        # PostgreSQL 17 (+ supportflow_test database for pytest)
backend/
  alembic/versions/       # versioned schema changes (0001_initial_core_schema)
  app/
    main.py               # app, CORS, request id middleware, routers
    api/                  # Routers: HTTP → function calls, status codes
    schemas/              # Pydantic Create / Update / Response = API contract
    services/             # business rules, membership checks, transaction boundaries
    repositories/         # base.py (Protocols) + postgres.py (SQLAlchemy queries)
    models.py             # SQLAlchemy ORM models = how data is stored
    db/                   # Base, engine, Session, transaction()
    deps.py               # Depends(): session, repositories, services, current user
    seed.py               # demo data with fixed ids
  tests/                  # integration tests against real PostgreSQL
frontend/
  app/  components/  lib/api.ts
```

## Data model

```mermaid
erDiagram
    users ||--o{ workspace_members : "has"
    workspaces ||--o{ workspace_members : "has"
    users ||--o{ workspaces : "owns"
    workspaces ||--o{ documents : "contains"
    workspaces ||--o{ tickets : "contains"
    tickets ||--o{ messages : "contains"
    users |o--o{ messages : "writes"

    users {
        uuid id PK
        string email UK
    }
    workspaces {
        uuid id PK
        uuid owner_user_id FK
    }
    workspace_members {
        uuid id PK
        uuid workspace_id FK
        uuid user_id FK
        string role
        string status
    }
    documents {
        uuid id PK
        uuid workspace_id FK
        string status
    }
    tickets {
        uuid id PK
        uuid workspace_id FK
        string status
        string priority
    }
    messages {
        uuid id PK
        uuid ticket_id FK
        uuid author_user_id FK
    }
```

- **Workspace is the tenant boundary.** Documents and Tickets carry `workspace_id`; Messages inherit it through their Ticket (no second `workspace_id` that could disagree).
- **users ↔ workspaces is many-to-many** through `workspace_members`, which also stores `role` and `status`.
- `UNIQUE (workspace_id, user_id)` on `workspace_members` and `UNIQUE (email)` on `users` are enforced by PostgreSQL, so concurrent requests cannot create duplicates.

### Indexes and the query each one serves

| Index | Query |
|---|---|
| `tickets (workspace_id, status, created_at)` | `WHERE workspace_id = ? AND status = ? ORDER BY created_at DESC LIMIT n`, the filtered ticket list |
| `tickets (workspace_id, created_at)` | `WHERE workspace_id = ? ORDER BY created_at DESC LIMIT n`, the default list (no status filter) |
| `workspace_members (user_id)` | `WHERE user_id = ?`: "which workspaces am I in" (`GET /api/workspaces`) |
| `uq_workspace_member (workspace_id, user_id)` | Uniqueness, and also the membership check run on every workspace-scoped request |

`documents` and `messages` have no extra indexes yet: no API queries them so far.

## Database with Docker (step by step)

PostgreSQL runs in a Docker container, so everyone gets the same database version and setup from one command. Only the database runs in Docker; FastAPI and Next.js run directly on your machine.

### Step 1: Install Docker Desktop (once)

1. Download **Docker Desktop for Mac – Apple Silicon** from https://www.docker.com/products/docker-desktop/ (pick the Intel version only on an Intel Mac; check with `uname -m`: `arm64` = Apple Silicon).
   Or with Homebrew: `brew install --cask docker-desktop`. When it asks for `Password:`, type your Mac login password and press Enter. **Nothing appears on screen while you type**; that is normal.
2. Open **Docker** from Applications. Accept the terms; signing in is optional (you can skip it).
3. Wait until the whale icon in the menu bar stops animating. Docker must be running whenever you use `docker` commands.
4. Open a **new** terminal window and check:

```bash
docker --version
docker compose version
docker run --rm hello-world      # prints "Hello from Docker!"
```

### Step 2: Understand what `docker-compose.yml` sets up

| Setting | Value | What it does |
|---|---|---|
| `services: db` | | One service called `db`; `docker compose … db` refers to it |
| `image` | `postgres:17` | Official PostgreSQL 17 image, downloaded on first run (~150 MB) |
| `environment` | user / password / database = `supportflow` | Created automatically on first start. These must match `DATABASE_URL` in `backend/.env` |
| `ports` | `5432:5432` | Your Mac's port 5432 → the container's port 5432, so the app can connect to `localhost:5432` |
| `volumes: pgdata` | `/var/lib/postgresql/data` | **Named volume**: database files live outside the container, so they survive restarts |
| `volumes: postgres-init.sql` | `/docker-entrypoint-initdb.d/` | **Bind mount**: on the very first start, creates the `supportflow_test` database for pytest |
| `healthcheck` | `pg_isready` every 2s | Marks the container `healthy` once PostgreSQL actually accepts connections |

How the connection string maps to it:

```text
postgresql+psycopg://supportflow:supportflow@localhost:5432/supportflow
                     user        password    host      port  database
```

### Step 3: Start the database

Run from the project root (the folder that contains `docker-compose.yml`):

```bash
cd SupportFlow.AI
docker compose up -d --wait db     # -d: run in background; --wait: return only when healthy
docker compose ps                  # STATUS should show (healthy)
```

The first run prints something like:

```text
✔ Network supportflowai_default   Created
✔ Volume "supportflowai_pgdata"   Created
✔ Container supportflowai-db-1    Healthy
```

### Step 4: Create the tables and demo data

```bash
cd backend
source .venv/bin/activate
cp .env.example .env               # only the first time
alembic upgrade head               # runs the existing migration(s): creates the six tables
python -m app.seed                 # demo users, workspaces and tickets (safe to re-run)
```

Use `alembic upgrade head` here, **not** `alembic revision --autogenerate`. `revision` writes a *new* migration file and is only needed after you change `app/models.py`.

### Step 5: Look inside the database (optional)

```bash
docker compose exec db psql -U supportflow            # interactive SQL shell; \q to quit
docker compose exec db psql -U supportflow -c "\dt"   # list tables
docker compose exec db psql -U supportflow -c "\d tickets"   # one table: columns, indexes, check constraints, foreign keys
docker compose exec db psql -U supportflow -c "SELECT subject, status FROM tickets;"
```

Run these from the project root. `psql` runs *inside* the container, so you don't need PostgreSQL installed on your Mac.

Why not `psql "$DATABASE_URL"`? `DATABASE_URL` is read by Python (`app/config.py`), not set in your terminal, so `$DATABASE_URL` is empty there. Its `postgresql+psycopg://` prefix is also SQLAlchemy-only; `psql` needs `postgresql://…`.

### Everyday commands

| Command | What happens | Data |
|---|---|---|
| `docker compose up -d --wait db` | Start (or restart) the database | kept |
| `docker compose ps` | Show status | kept |
| `docker compose logs -f db` | Follow the database logs (`Ctrl + C` to stop following) | kept |
| `docker compose stop` | Stop the container | kept |
| `docker compose down` | Stop **and remove** the container | kept (the volume stays) |
| Quit Docker Desktop / restart your Mac | | kept |
| `docker compose down -v` | Remove the container **and the volume** | ⚠️ **deleted** |

To start over from an empty database: `docker compose down -v`, then repeat Steps 3 and 4.

### Troubleshooting

| Error | Cause | Fix |
|---|---|---|
| `command not found: docker` | Docker Desktop not installed, or never opened | Finish Step 1, open Docker, open a new terminal |
| `Cannot connect to the Docker daemon` | Docker Desktop is not running | Open Docker and wait for the whale icon |
| `Connection refused … port 5432` (from alembic / uvicorn) | The database container is not running | `docker compose up -d --wait db` |
| `port is already allocated` / `address already in use` on 5432 | Another PostgreSQL is using 5432 | Stop it (e.g. `brew services stop postgresql@17`), or change the left side of `ports` to `"5433:5432"` and the port in `backend/.env` |
| `database "supportflow_test" does not exist` | The volume was created before the init script existed | `docker compose down -v` and start again (deletes local data) |
| `password authentication failed` | `.env` does not match `docker-compose.yml` | Use the values from `backend/.env.example` |

## Development commands

### Database commands

```bash
alembic current                         # which migration the database is on
alembic history                         # all migrations
alembic revision --autogenerate -m "…"  # draft a new migration: ALWAYS read it before upgrading
alembic downgrade -1                    # undo the last migration

docker compose exec db psql -U supportflow -c "\dt"          # list tables
docker compose exec db psql -U supportflow -c "\d tickets"   # columns, indexes, constraints
```

### Tests

```bash
cd backend && source .venv/bin/activate
pytest -q        # migrates supportflow_test (downgrade base → upgrade head), reseeds before each test
```

| Test | Who stops the bad case |
|---|---|
| ticket persists after API restart | PostgreSQL (data is not in process memory) |
| ticket with a missing workspace | PostgreSQL foreign key |
| duplicate membership | PostgreSQL unique constraint |
| read a ticket through another workspace → 404 | Repository query scoped by `(workspace_id, ticket_id)` |
| register rolls back when membership fails | Service transaction boundary |
| duplicate email → 409 | Service check + unique constraint |

## Environment variables (frontend)

| Variable | Default | Purpose |
|---|---|---|
| `BACKEND_URL` | `http://localhost:8000` | Where the Next.js `/api` proxy forwards requests |
| `NEXT_PUBLIC_API_URL` | `/api` | Base URL the browser calls. Set to `http://localhost:8000/api` to bypass the proxy (uses CORS) |

Copy `frontend/.env.example` to `frontend/.env.local` to change them.

## API surface

| Method | Endpoint | Success | Notes |
|---|---|---|---|
| GET | `/health` | 200 | |
| POST | `/api/auth/register` | 201 | user + personal workspace + OWNER membership in one transaction; 409 on duplicate email |
| GET | `/api/workspaces` | 200 | workspaces the current user belongs to |
| POST | `/api/workspaces` | 201 | creator becomes OWNER |
| GET | `/api/workspaces/{wid}/tickets` | 200 | `page`, `page_size` (1–100), `status`, `priority` |
| POST | `/api/workspaces/{wid}/tickets` | 201 | body `{subject, priority}`; status starts `OPEN` |
| GET | `/api/workspaces/{wid}/tickets/{id}` | 200 | 404 if the ticket is not in that workspace |
| PATCH | `/api/workspaces/{wid}/tickets/{id}` | 200 | any of `subject`, `priority`, `status` |
| DELETE | `/api/workspaces/{wid}/tickets/{id}` | 204 | |

Ticket item routes moved from `/api/tickets/{id}` (Lesson 2) under the workspace, so every ticket lookup is scoped by `(workspace_id, ticket_id)`. Request and response bodies did not change.

Errors always look like:

```json
{ "error": { "code": "TICKET_NOT_FOUND", "message": "Ticket not found", "request_id": "671c197047d1" } }
```

422 responses also include `details: [{ "field": "subject", "message": "..." }]`.

### curl examples

```bash
WS=11111111-1111-1111-1111-111111111111   # seeded "Acme Support"

curl "localhost:8000/api/workspaces/$WS/tickets?status=OPEN&page=1&page_size=20"

curl -X POST "localhost:8000/api/workspaces/$WS/tickets" \
  -H "Content-Type: application/json" \
  -d '{"subject": "Customer cannot log in", "priority": "HIGH"}'

# 422: subject too short
curl -X POST "localhost:8000/api/workspaces/$WS/tickets" \
  -H "Content-Type: application/json" -d '{"subject": "ab", "priority": "HIGH"}'

# 404: an Acme ticket read through the "New Team" workspace
curl "localhost:8000/api/workspaces/22222222-2222-2222-2222-222222222222/tickets/<acme-ticket-id>"

# 403: Alice is not a member of Bob's workspace
curl "localhost:8000/api/workspaces/33333333-3333-3333-3333-333333333333/tickets"
```

## Remote access (Cloudflare quick tunnel)

With both servers running:

```bash
cloudflared tunnel --url http://localhost:3000
```

It prints a `https://<random>.trycloudflare.com` URL that anyone can open. Only port 3000 needs a tunnel because the browser reaches FastAPI through the Next.js `/api` proxy. Press `Ctrl + C` to close it; the URL stops working immediately.
