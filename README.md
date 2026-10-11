# SupportFlow.AI

AI knowledge workflow platform for support teams. A FastAPI backend (Workspace + Ticket CRUD) and a Next.js + React frontend.

## Data mode

- **Workspaces and Tickets**: real FastAPI endpoints, stored in an in-memory repository (data resets on restart). PostgreSQL comes next.
- **Documents and the AI Assistant**: still mock data inside the frontend (`frontend/lib/mock-data.ts`).
- No login yet: requests act as the seeded user Alice. Send `X-User-Id: 00000000-0000-0000-0000-000000000002` to act as Bob.

## Structure

```text
backend/app/
  main.py                 # app, CORS, request id middleware, routers
  api/                    # Routers: HTTP → function calls, status codes
  schemas/                # Pydantic Create / Update / Response schemas
  services/               # business rules + workspace membership checks
  repositories/memory.py  # in-memory storage + seed data
  deps.py                 # Depends(): current user, services, repository
  errors.py               # unified error body
frontend/
  app/                    # Next.js routes (Dashboard, Documents, Tickets, AI Assistant)
  components/             # reusable React components
  lib/api.ts              # typed API client (frontend/backend boundary)
```

## Run it (two terminals)

```bash
# Terminal 1: backend
cd backend
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
uvicorn app.main:app --reload --port 8000
```

```bash
# Terminal 2: frontend
cd frontend
npm install
npm run dev
```

Open http://localhost:3000. The frontend calls `/api/*`, which Next.js proxies to `http://localhost:8000/api/*`.
API docs: http://localhost:8000/docs.

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
| GET | `/api/workspaces` | 200 | workspaces the current user belongs to |
| POST | `/api/workspaces` | 201 | creator becomes OWNER |
| GET | `/api/workspaces/{wid}/tickets` | 200 | `page`, `page_size` (1–100), `status`, `priority` |
| POST | `/api/workspaces/{wid}/tickets` | 201 | body `{subject, priority}`; status starts `OPEN` |
| GET | `/api/tickets/{id}` | 200 | |
| PATCH | `/api/tickets/{id}` | 200 | **not implemented: class challenge** |
| DELETE | `/api/tickets/{id}` | 204 | |

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

# 403: Alice is not a member of Bob's workspace
curl "localhost:8000/api/workspaces/33333333-3333-3333-3333-333333333333/tickets"
```

## Remote access (Cloudflare quick tunnel)

With both servers running:

```bash
cloudflared tunnel --url http://localhost:3000
```

It prints a `https://<random>.trycloudflare.com` URL that anyone can open. Only port 3000 needs a tunnel because the browser reaches FastAPI through the Next.js `/api` proxy. Press `Ctrl + C` to close it; the URL stops working immediately.
