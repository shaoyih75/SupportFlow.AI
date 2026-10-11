# SupportFlow.AI Frontend

Next.js (App Router) + React + TypeScript. Next.js handles routing and layout; the UI itself is plain React: components, props, state, events and async data.

## Run

```bash
npm install
npm run dev        # http://localhost:3000
npm run build      # production build + type check
```

## Architecture

```text
app/
  layout.tsx                          # root <html> shell
  page.tsx                            # redirects to the default workspace
  workspaces/[workspaceId]/
    layout.tsx                        # shared shell: Sidebar + content
    page.tsx                          # Dashboard
    documents/page.tsx                # search + status filter, 4 UI states
    tickets/page.tsx                  # FastAPI list/create, server-side filter + pagination
    tickets/[ticketId]/page.tsx       # ticket detail, 404 → "Ticket not found"
    assistant/page.tsx                # controlled form, mock answer with citations
components/
  Sidebar.tsx  PageHeader.tsx  DocumentCard.tsx  TicketCard.tsx  TicketForm.tsx
  StatusBadge.tsx  AsyncStates.tsx    # Loading / Empty / Error
lib/
  types.ts                            # Document, Ticket, Workspace, ProcessingJob...
  api.ts                              # the only frontend/backend boundary (fetch + ApiError)
  config.ts                           # seeded default workspace id
  mock-data.ts                        # Documents mock, imported by api.ts only
```

Data flow: `page (state + useEffect) → lib/api.ts → /api (Next.js proxy) → FastAPI`. Documents still use mock data inside `lib/api.ts`.

The backend must be running for Workspaces and Tickets. See the root [README](../README.md).

## Seeded workspaces

| Workspace | Shows |
|-----------|-------|
| Acme Support | tickets list, filter, pagination, create |
| New Team | empty state |
| (stop FastAPI) | error state with Retry; sidebar shows "API offline" |
| `/tickets/<bad id>` | "Ticket not found" |
