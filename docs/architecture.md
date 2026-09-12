# Northstar Workspace Document architecture

```mermaid
flowchart LR
    User[Workspace member] --> UI[React + TypeScript<br/>Document workspace]
    UI --> API[FastAPI REST API]
    API --> Domain[Workspace + document domain<br/>validation and permissions]
    Domain --> Repo[(Document repository<br/>mock data)]
    Domain --> Comments[Comments and activity]
    API --> Events[Future event layer<br/>notifications and indexing]
    Events --> Search[Future search service]
    Events --> Integrations[Future integrations<br/>Slack / Email / Drive]
```

## Request flow

1. A workspace member selects or edits a document in the React document workspace.
2. The frontend calls the FastAPI API for workspaces, documents, and comments.
3. The domain layer owns document validation, membership, and permission rules.
4. The repository currently serves mock documents in memory.
5. Comments and activity are kept as separate collaboration concerns.
6. The event layer, search, and external integrations are future extension points.

All current data is mock data. There is no database or external integration connected yet.
