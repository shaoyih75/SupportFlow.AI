from datetime import datetime, timezone
from typing import Literal
from uuid import uuid4

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field

app = FastAPI(title="SupportFlow API", version="0.1.0", description="Backend skeleton for support operations.")
app.add_middleware(CORSMiddleware, allow_origins=["http://localhost:5173"], allow_credentials=True, allow_methods=["*"], allow_headers=["*"])

Status = Literal["open", "pending", "resolved"]

class Ticket(BaseModel):
    id: str
    customer: str
    subject: str
    message: str
    status: Status
    priority: Literal["high", "normal"] = "normal"
    channel: Literal["Email", "Chat"]
    tag: str
    created_at: datetime

class CreateTicket(BaseModel):
    customer: str = Field(min_length=2)
    subject: str = Field(min_length=3)
    message: str = Field(min_length=1)
    channel: Literal["Email", "Chat"] = "Email"
    priority: Literal["high", "normal"] = "normal"
    tag: str = "General"

class Reply(BaseModel):
    message: str = Field(min_length=1)

TICKETS = [
    Ticket(id="SF-1048", customer="Ava Thompson", subject="Unable to sync my workspace", message="The sync has been running for more than 20 minutes.", status="open", priority="high", channel="Email", tag="Integrations", created_at=datetime.now(timezone.utc)),
    Ticket(id="SF-1047", customer="Marcus Chen", subject="Invoice shows the wrong plan", message="I upgraded last week but this month still shows the old plan.", status="pending", channel="Chat", tag="Billing", created_at=datetime.now(timezone.utc)),
]

@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok", "service": "supportflow-api"}

@app.get("/api/v1/tickets", response_model=list[Ticket])
def list_tickets(status: Status | None = None) -> list[Ticket]:
    return [ticket for ticket in TICKETS if status is None or ticket.status == status]

@app.get("/api/v1/tickets/{ticket_id}", response_model=Ticket)
def get_ticket(ticket_id: str) -> Ticket:
    ticket = next((item for item in TICKETS if item.id == ticket_id), None)
    if ticket is None:
        raise HTTPException(status_code=404, detail="Ticket not found")
    return ticket

@app.post("/api/v1/tickets", response_model=Ticket, status_code=201)
def create_ticket(payload: CreateTicket) -> Ticket:
    ticket = Ticket(id=f"SF-{uuid4().hex[:6].upper()}", status="open", created_at=datetime.now(timezone.utc), **payload.model_dump())
    TICKETS.insert(0, ticket)
    return ticket

@app.post("/api/v1/tickets/{ticket_id}/replies")
def reply_to_ticket(ticket_id: str, payload: Reply) -> dict[str, str]:
    get_ticket(ticket_id)
    return {"ticket_id": ticket_id, "message": payload.message, "status": "queued"}
