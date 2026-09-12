# SupportFlow.AI

Support operations workspace skeleton: a FastAPI backend boundary and a polished React mock frontend.

## Data mode

Everything is mocked for now. The frontend uses local mock data, and the backend keeps its sample tickets in memory. No real customer data, database, email provider, or AI provider is connected.

## Structure

```text
backend/
  app/main.py       # API app, models, in-memory repository, routes
  requirements.txt
frontend/
  src/App.tsx       # mock support workspace UI and interactions
  src/App.css       # responsive visual system
docs/
  architecture.mmd  # system architecture diagram
```

## Run the frontend

```bash
cd frontend
npm install
npm run dev
```

Open http://localhost:5173.

## Run the backend

```bash
cd backend
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
uvicorn app.main:app --reload --port 8000
```

API docs are available at http://localhost:8000/docs.

## API surface

- `GET /health`
- `GET /api/v1/tickets?status=open`
- `GET /api/v1/tickets/{ticket_id}`
- `POST /api/v1/tickets`
- `POST /api/v1/tickets/{ticket_id}/replies`

The frontend currently uses local mock data so it can be designed and reviewed independently of the API. Connecting a database or external provider is intentionally left as a later integration step.
