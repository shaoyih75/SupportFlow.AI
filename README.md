# SupportFlow.AI

AI knowledge workflow platform for support teams. A FastAPI backend (Workspace + Ticket CRUD, JWT login, workspace RBAC) and a Next.js + React frontend.

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
alembic current                              # shows: 0002 (head)
python -m app.seed                           # demo users (password123), workspaces, tickets (safe to re-run)
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

1. Log in as `alice@example.com` / `password123` (or click a demo account), open **Acme Support → Tickets**: 5 demo tickets are listed.
2. Create a ticket: it appears at the top.
3. In terminal 2 press `Ctrl + C`, start `uvicorn app.main:app --reload --port 8000` again, refresh the page: **the new ticket is still there**.
4. Run the tests (in `backend/` with `.venv` active; stop uvicorn first or use another terminal):

```bash
pytest -q                                    # 26 passed
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
- **Login**: email + password → JWT access token, sent as `Authorization: Bearer <token>`. Demo users (password `password123`): `alice@example.com` (OWNER of Acme), `bob@example.com` (MEMBER of Acme, OWNER of his own workspace), `carol@example.com` (VIEWER of Acme). See [Permission model](#permission-model).
- **Your own account**: on the login page, click **Create an account** (`/register`). Registering creates a personal workspace where you are OWNER; on **My workspaces** use **New workspace** to create more (you become their OWNER and land on its Tickets page).

## Structure

```text
docker-compose.yml        # PostgreSQL 17 (+ supportflow_test database for pytest)
backend/
  alembic/versions/       # versioned schema changes (0001 core schema, 0002 auth + VIEWER role)
  app/
    main.py               # app, CORS, request id middleware, routers
    api/                  # Routers: HTTP → function calls, status codes
    schemas/              # Pydantic Create / Update / Response = API contract
    services/             # business rules, membership checks, transaction boundaries
    repositories/         # base.py (Protocols) + postgres.py (SQLAlchemy queries)
    models.py             # SQLAlchemy ORM models = how data is stored
    auth/security.py      # bcrypt password hashing, JWT create/decode
    db/                   # Base, engine, Session, transaction()
    deps.py               # Depends(): current user (JWT), membership + role checks, services
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

## Permission model

Every workspace request answers four questions, in this order. The first "no" stops the request **before** any business logic or write runs.

| Step | Question | Where | Fails with |
|---|---|---|---|
| Authentication | Who are you? | `get_current_user`: verifies the JWT, loads the user by its `sub` | **401** missing / invalid / expired token |
| Membership | Do you belong to this workspace? | `require_workspace_member`: an **ACTIVE** row in `workspace_members` | **403** (also for an unknown workspace id, so ids can't be probed) |
| Authorization | May your role do this? | `require_workspace_role(...)` | **403** |
| Tenant isolation | Is the resource in this workspace? | `TicketRepository.get_in_workspace(workspace_id=, ticket_id=)`: one query with both ids | **404**: from your scope it does not exist |

**Identity comes only from the token.** The JWT's `sub` is the user id; it holds no roles. Roles and membership status are read from the database on every request, so removing or suspending a member takes effect immediately, not when their token expires (60 min). The API never trusts a `user_id`, `role` or workspace list sent by the client.

**Membership status:** only `ACTIVE` grants access. `INVITED`, `SUSPENDED` and `REMOVED` rows are kept for history but are refused.

**Roles (RBAC):**

| Action | OWNER | MEMBER | VIEWER |
|---|---|---|---|
| View the workspace, its tickets and members | ✅ | ✅ | ✅ |
| Create and update tickets | ✅ | ✅ | ❌ 403 |
| Delete tickets | ✅ | ❌ 403 | ❌ 403 |
| Add or remove members | ✅ | ❌ 403 | ❌ 403 |

The table lives in one place, `app/deps.py` (`can_read`, `can_write_tickets`, `can_delete_tickets`, `can_manage_members`). The frontend hides controls a role can't use (VIEWER sees no create form or status menu; only OWNER sees Delete), but that is only for convenience: the API refuses the request anyway.

**IDOR, before and after.** Before: `GET /tickets/{ticket_id}` loaded the ticket by its global id, so any logged-in user who knew Bob's ticket id could read it (200). After: the route is `/workspaces/{workspace_id}/tickets/{ticket_id}`, membership is checked for `workspace_id`, and the query filters on both ids, so Alice gets 403 in Bob's workspace and 404 when she puts Bob's ticket id under her own workspace. To show the bug in class, start the API with `ENABLE_IDOR_DEMO=1`, which mounts the deliberately insecure `GET /api/demo/insecure/tickets/{ticket_id}` (off by default; a test checks it stays off).

**Token storage (frontend).** The demo keeps the token in `localStorage`. Production apps usually use a `Secure`, `HttpOnly`, `SameSite` cookie instead (scripts can't read it), which then also needs CSRF protection.

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
| **Lesson 4** | |
| ticket persists after API restart | PostgreSQL (data is not in process memory) |
| ticket with a missing workspace | PostgreSQL foreign key |
| duplicate membership | PostgreSQL unique constraint |
| read a ticket through another workspace → 404 | Repository query scoped by `(workspace_id, ticket_id)` |
| register rolls back when membership fails | Service transaction boundary |
| duplicate email → 409 | Service check + unique constraint |
| **Lesson 6** (`tests/test_auth_rbac.py`) | |
| missing, malformed, expired, forged token → 401 | `get_current_user` |
| Alice in Bob's workspace / unknown workspace / suspended member → 403 | `require_workspace_member` |
| VIEWER create/update, MEMBER delete, non-OWNER manage members → 403 | `require_workspace_role` |
| Bob's ticket id under Alice's workspace (GET / PATCH / DELETE) → 404, data unchanged | scoped repository query |
| role / user_id smuggled in body or headers → still 403 | identity only from the token |
| insecure IDOR demo route is not mounted by default | `ENABLE_IDOR_DEMO` flag |
| register with invalid input → 422 per field; new user creates a workspace as OWNER and a ticket in it | `RegisterRequest` / `WorkspaceService.create` |

## Environment variables

Backend (`backend/.env`, see `.env.example`):

| Variable | Default | Purpose |
|---|---|---|
| `DATABASE_URL` | local Docker database | SQLAlchemy connection string |
| `JWT_SECRET_KEY` | an insecure dev-only value | Signs access tokens. **Set a long random value outside development**: `python -c "import secrets; print(secrets.token_urlsafe(48))"` |
| `ACCESS_TOKEN_EXPIRE_MINUTES` | `60` | Token lifetime |
| `ENABLE_IDOR_DEMO` | off | `1` mounts the deliberately insecure Class 6 demo endpoint |

Frontend:

| Variable | Default | Purpose |
|---|---|---|
| `BACKEND_URL` | `http://localhost:8000` | Where the Next.js `/api` proxy forwards requests |
| `NEXT_PUBLIC_API_URL` | `/api` | Base URL the browser calls. Set to `http://localhost:8000/api` to bypass the proxy (uses CORS) |

Copy `frontend/.env.example` to `frontend/.env.local` to change them.

## API surface

| Method | Endpoint | Success | Who | Notes |
|---|---|---|---|---|
| GET | `/health` | 200 | anyone | |
| POST | `/api/auth/register` | 201 | anyone | user + personal workspace + OWNER membership in one transaction; 409 on duplicate email |
| POST | `/api/auth/login` | 200 | anyone | JSON `{email, password}` → `{access_token, token_type: "bearer"}`; 401 on bad credentials |
| POST | `/api/auth/token` | 200 | anyone | same, as a form (`username` = email): powers Swagger's **Authorize** button |
| GET | `/api/auth/me` | 200 | logged in | the token's user |
| GET | `/api/workspaces` | 200 | logged in | workspaces with an ACTIVE membership, with your role |
| POST | `/api/workspaces` | 201 | logged in | creator becomes OWNER |
| GET | `/api/workspaces/{wid}` | 200 | any member | includes your role |
| GET | `/api/workspaces/{wid}/members` | 200 | any member | |
| POST | `/api/workspaces/{wid}/members` | 201 | OWNER | body `{email, role}`; 404 unknown email, 409 already a member |
| DELETE | `/api/workspaces/{wid}/members/{user_id}` | 204 | OWNER | sets status REMOVED; 409 for the last OWNER |
| GET | `/api/workspaces/{wid}/tickets` | 200 | any member | `page`, `page_size` (1–100), `status`, `priority` |
| POST | `/api/workspaces/{wid}/tickets` | 201 | OWNER, MEMBER | body `{subject, priority}`; status starts `OPEN` |
| GET | `/api/workspaces/{wid}/tickets/{id}` | 200 | any member | 404 if the ticket is not in that workspace |
| PATCH | `/api/workspaces/{wid}/tickets/{id}` | 200 | OWNER, MEMBER | any of `subject`, `priority`, `status` |
| DELETE | `/api/workspaces/{wid}/tickets/{id}` | 204 | OWNER | |

Every workspace route answers 401 without a valid token and 403 for non-members, before checking anything else.

Ticket item routes moved from `/api/tickets/{id}` (Lesson 2) under the workspace, so every ticket lookup is scoped by `(workspace_id, ticket_id)`. Request and response bodies did not change.

Errors always look like:

```json
{ "error": { "code": "TICKET_NOT_FOUND", "message": "Ticket not found", "request_id": "671c197047d1" } }
```

422 responses also include `details: [{ "field": "subject", "message": "..." }]`.

### curl examples

```bash
API=http://localhost:8000/api
WS_A=11111111-1111-1111-1111-111111111111   # Acme Support (Alice OWNER, Bob MEMBER, Carol VIEWER)
WS_B=33333333-3333-3333-3333-333333333333   # Bob's Private Workspace

login() {
  curl -s -X POST "$API/auth/login" -H "Content-Type: application/json" \
    -d "{\"email\": \"$1@example.com\", \"password\": \"password123\"}" \
    | python3 -c "import sys, json; print(json.load(sys.stdin)['access_token'])"
}
ALICE_TOKEN=$(login alice)
CAROL_TOKEN=$(login carol)

# 401: no token
curl -i "$API/workspaces/$WS_A/tickets"

# 200: Alice lists her tickets
curl -H "Authorization: Bearer $ALICE_TOKEN" "$API/workspaces/$WS_A/tickets?status=OPEN"

# 201: create · 422: subject too short
curl -X POST "$API/workspaces/$WS_A/tickets" -H "Authorization: Bearer $ALICE_TOKEN" \
  -H "Content-Type: application/json" -d '{"subject": "Customer cannot log in", "priority": "HIGH"}'
curl -X POST "$API/workspaces/$WS_A/tickets" -H "Authorization: Bearer $ALICE_TOKEN" \
  -H "Content-Type: application/json" -d '{"subject": "ab", "priority": "HIGH"}'

# 403: Alice is not a member of Bob's workspace
curl -i -H "Authorization: Bearer $ALICE_TOKEN" "$API/workspaces/$WS_B/tickets"

# 404: Bob's ticket id put under Alice's workspace (the IDOR fix)
curl -i -H "Authorization: Bearer $ALICE_TOKEN" "$API/workspaces/$WS_A/tickets/<bob-ticket-id>"

# 403: Carol is a VIEWER
curl -i -X PATCH "$API/workspaces/$WS_A/tickets/<acme-ticket-id>" -H "Authorization: Bearer $CAROL_TOKEN" \
  -H "Content-Type: application/json" -d '{"status": "RESOLVED"}'
```

In Swagger (http://localhost:8000/docs): click **Authorize**, enter `alice@example.com` / `password123`, and every request is sent with the token.

## Remote access (Cloudflare quick tunnel)

With both servers running:

```bash
cloudflared tunnel --url http://localhost:3000
```

It prints a `https://<random>.trycloudflare.com` URL that anyone can open. Only port 3000 needs a tunnel because the browser reaches FastAPI through the Next.js `/api` proxy. Press `Ctrl + C` to close it; the URL stops working immediately.
