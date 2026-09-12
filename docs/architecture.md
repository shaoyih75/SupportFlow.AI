# SupportFlow architecture

```mermaid
flowchart LR
    Agent[Support agent] --> UI[React + TypeScript\nMock dashboard]
    UI --> API[FastAPI REST API]
    API --> Domain[Ticket domain\nvalidation + status]
    Domain --> Repo[(Ticket repository)]
    API --> Events[Future event queue\nnotifications / AI]
    Events --> Integrations[Email + Chat providers]
    Domain --> Analytics[Future analytics service]
```

The current skeleton keeps persistence in memory so the API and UI boundaries are easy to understand. A production implementation can replace the repository with Postgres without changing the route contract, then add authentication, background events, provider adapters, and AI-assisted classification behind the domain layer.
