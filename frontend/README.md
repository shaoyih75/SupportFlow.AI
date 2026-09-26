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
    tickets/page.tsx                  # status filter, 4 UI states
    assistant/page.tsx                # controlled form, mock answer with citations
components/
  Sidebar.tsx  PageHeader.tsx  DocumentCard.tsx  TicketCard.tsx
  StatusBadge.tsx  AsyncStates.tsx    # Loading / Empty / Error
lib/
  types.ts                            # Document, Ticket, Workspace, ProcessingJob...
  api.ts                              # the only frontend/backend boundary
  mock-data.ts                        # imported by api.ts only
```

Data flow: `page (state + useEffect) → lib/api.ts → mock data`. When FastAPI is connected, only `lib/api.ts` changes, and pages and components stay the same.

## Demo workspaces

Use the workspace switcher in the sidebar to see every async UI state:

| Workspace | Shows |
|-----------|-------|
| Acme Support | loading → success |
| New Team (empty) | empty state |
| Broken API (error demo) | error state with Retry |
