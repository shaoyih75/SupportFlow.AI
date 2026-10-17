from uuid import uuid4

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware

from app.api import auth, demo_insecure, tickets, workspaces
from app.config import ENABLE_IDOR_DEMO
from app.errors import register_error_handlers

app = FastAPI(
    title="SupportFlow.AI API",
    version="0.5.0",
    description="Workspace and Ticket CRUD on PostgreSQL, with JWT login and workspace RBAC.",
)

# Only needed when the browser calls FastAPI directly (NEXT_PUBLIC_API_URL=http://localhost:8000/api).
# The default setup proxies /api through Next.js, which is same-origin and needs no CORS.
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://127.0.0.1:3000"],
    allow_methods=["*"],
    allow_headers=["*"],
    expose_headers=["X-Request-ID"],
)


@app.middleware("http")
async def add_request_id(request: Request, call_next):
    request.state.request_id = request.headers.get("X-Request-ID") or uuid4().hex[:12]
    response = await call_next(request)
    response.headers["X-Request-ID"] = request.state.request_id
    return response


register_error_handlers(app)


@app.get("/health", tags=["health"])
def health() -> dict[str, str]:
    return {"status": "ok"}


app.include_router(auth.router, prefix="/api")
app.include_router(workspaces.router, prefix="/api")
app.include_router(tickets.router, prefix="/api")

if ENABLE_IDOR_DEMO:
    app.include_router(demo_insecure.router, prefix="/api")
