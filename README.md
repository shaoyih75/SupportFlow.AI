# SupportFlow.AI

Northstar Workspace Document skeleton: a FastAPI backend boundary and a polished React mock document workspace.

## Data mode

Everything is mocked for now. The frontend uses local mock documents, and the backend keeps its sample workspace, documents, and comments in memory. No real customer data, database, search service, or external integration is connected.

## Structure

```text
backend/app/main.py       # workspace/document API and in-memory mock repository
frontend/src/App.tsx      # document workspace UI and mock interactions
docs/architecture.mmd     # current Workspace Document architecture
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
- `GET /api/v1/workspaces`
- `GET /api/v1/workspaces/{workspace_id}/documents`
- `GET /api/v1/documents/{document_id}`
- `POST /api/v1/workspaces/{workspace_id}/documents`
- `POST /api/v1/documents/{document_id}/comments`
