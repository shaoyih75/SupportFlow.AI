from datetime import datetime, timezone
from typing import Literal
from uuid import uuid4

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field

app = FastAPI(title="Northstar Workspace API", version="0.2.0", description="Mock backend skeleton for collaborative workspace documents.")
app.add_middleware(CORSMiddleware, allow_origins=["http://localhost:5173", "http://127.0.0.1:5173"], allow_credentials=True, allow_methods=["*"], allow_headers=["*"])

class Workspace(BaseModel):
    id: str
    name: str
    member_count: int

class Document(BaseModel):
    id: str
    workspace_id: str
    title: str
    content: str
    category: str
    updated_at: datetime
    is_favorite: bool = False

class CreateDocument(BaseModel):
    title: str = Field(min_length=1, max_length=120)
    content: str = ""
    category: str = "Uncategorized"

class Comment(BaseModel):
    document_id: str
    body: str = Field(min_length=1)
    author: str = "Jamie Wilson"

WORKSPACE = Workspace(id="northstar", name="Northstar Inc.", member_count=12)
DOCUMENTS = [
    Document(id="welcome", workspace_id=WORKSPACE.id, title="Welcome to Northstar", content="A calm, shared home for the way your team thinks.", category="Getting started", updated_at=datetime.now(timezone.utc), is_favorite=True),
    Document(id="handbook", workspace_id=WORKSPACE.id, title="Team handbook", content="How we work together, make decisions, and keep momentum.", category="Company", updated_at=datetime.now(timezone.utc)),
    Document(id="roadmap", workspace_id=WORKSPACE.id, title="Product roadmap", content="A living view of what we are building next.", category="Product", updated_at=datetime.now(timezone.utc)),
]
COMMENTS: list[Comment] = []

@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok", "service": "northstar-workspace-api", "data_mode": "mock"}

@app.get("/api/v1/workspaces", response_model=list[Workspace])
def list_workspaces() -> list[Workspace]:
    return [WORKSPACE]

@app.get("/api/v1/workspaces/{workspace_id}/documents", response_model=list[Document])
def list_documents(workspace_id: str) -> list[Document]:
    if workspace_id != WORKSPACE.id:
        raise HTTPException(status_code=404, detail="Workspace not found")
    return [document for document in DOCUMENTS if document.workspace_id == workspace_id]

@app.get("/api/v1/documents/{document_id}", response_model=Document)
def get_document(document_id: str) -> Document:
    document = next((item for item in DOCUMENTS if item.id == document_id), None)
    if document is None:
        raise HTTPException(status_code=404, detail="Document not found")
    return document

@app.post("/api/v1/workspaces/{workspace_id}/documents", response_model=Document, status_code=201)
def create_document(workspace_id: str, payload: CreateDocument) -> Document:
    if workspace_id != WORKSPACE.id:
        raise HTTPException(status_code=404, detail="Workspace not found")
    document = Document(id=f"doc-{uuid4().hex[:8]}", workspace_id=workspace_id, updated_at=datetime.now(timezone.utc), **payload.model_dump())
    DOCUMENTS.insert(0, document)
    return document

@app.post("/api/v1/documents/{document_id}/comments", response_model=Comment, status_code=201)
def add_comment(document_id: str, payload: Comment) -> Comment:
    get_document(document_id)
    comment = Comment(document_id=document_id, body=payload.body, author=payload.author)
    COMMENTS.append(comment)
    return comment
