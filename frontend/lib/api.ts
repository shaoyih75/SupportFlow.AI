// Frontend/backend boundary. Every page gets data through these functions.
// Workspaces and Tickets come from FastAPI; Documents and the Assistant are still mock.

import { mockDocuments } from "./mock-data";
import type {
  AssistantAnswer,
  Document,
  Page,
  Ticket,
  TicketCreate,
  TicketPriority,
  TicketUpdate,
  TicketStatus,
  Workspace,
} from "./types";

// "/api" goes through the Next.js proxy (next.config.ts). Override with NEXT_PUBLIC_API_URL.
const API_URL = process.env.NEXT_PUBLIC_API_URL ?? "/api";

// ---------- errors ----------

export type FieldErrors = Record<string, string>;

export class ApiError extends Error {
  constructor(
    public status: number,
    public code: string,
    message: string,
    public fieldErrors: FieldErrors = {},
    public requestId: string | null = null,
  ) {
    super(message);
    this.name = "ApiError";
  }

  // Parses the backend's unified body: { error: { code, message, details?, request_id? } }
  static async fromResponse(response: Response): Promise<ApiError> {
    const body = await response.json().catch(() => null);
    const error = body?.error;
    const fieldErrors: FieldErrors = {};
    for (const d of error?.details ?? []) fieldErrors[d.field] = d.message;
    return new ApiError(
      response.status,
      error?.code ?? `HTTP_${response.status}`,
      error?.message ?? response.statusText,
      fieldErrors,
      error?.request_id ?? response.headers.get("X-Request-ID"),
    );
  }
}

async function request<T>(path: string, init?: RequestInit): Promise<T> {
  let response: Response;
  try {
    response = await fetch(`${API_URL}${path}`, {
      ...init,
      headers: { "Content-Type": "application/json", ...init?.headers },
    });
  } catch {
    throw new ApiError(0, "NETWORK_ERROR", "Cannot reach the API server. Is FastAPI running?");
  }
  if (!response.ok) throw await ApiError.fromResponse(response);
  if (response.status === 204) return undefined as T;
  return response.json();
}

// ---------- snake_case JSON → camelCase types ----------

type WorkspaceJson = { id: string; name: string; role: Workspace["role"]; member_count: number };
type TicketJson = {
  id: string;
  workspace_id: string;
  subject: string;
  status: TicketStatus;
  priority: TicketPriority;
  created_at: string;
};
type PageJson<T> = { items: T[]; page: number; page_size: number; total: number };

const toWorkspace = (w: WorkspaceJson): Workspace => ({
  id: w.id,
  name: w.name,
  role: w.role,
  memberCount: w.member_count,
});

const toTicket = (t: TicketJson): Ticket => ({
  id: t.id,
  workspaceId: t.workspace_id,
  subject: t.subject,
  status: t.status,
  priority: t.priority,
  createdAt: t.created_at,
});

// ---------- workspaces ----------

export async function getWorkspaces(): Promise<Workspace[]> {
  const data = await request<WorkspaceJson[]>("/workspaces");
  return data.map(toWorkspace);
}

// ---------- tickets ----------

export type TicketQuery = {
  page?: number;
  pageSize?: number;
  status?: TicketStatus;
  priority?: TicketPriority;
};

export async function getTickets(workspaceId: string, query: TicketQuery = {}): Promise<Page<Ticket>> {
  const params = new URLSearchParams();
  if (query.page) params.set("page", String(query.page));
  if (query.pageSize) params.set("page_size", String(query.pageSize));
  if (query.status) params.set("status", query.status);
  if (query.priority) params.set("priority", query.priority);
  const qs = params.toString();

  const data = await request<PageJson<TicketJson>>(`/workspaces/${workspaceId}/tickets${qs ? `?${qs}` : ""}`);
  return { items: data.items.map(toTicket), page: data.page, pageSize: data.page_size, total: data.total };
}

// Ticket routes are nested under the workspace: the backend looks tickets up by
// (workspace_id, ticket_id), so a ticket can never be read through another workspace.
export async function getTicket(workspaceId: string, ticketId: string): Promise<Ticket> {
  return toTicket(await request<TicketJson>(`/workspaces/${workspaceId}/tickets/${ticketId}`));
}

export async function createTicket(workspaceId: string, input: TicketCreate): Promise<Ticket> {
  const data = await request<TicketJson>(`/workspaces/${workspaceId}/tickets`, {
    method: "POST",
    body: JSON.stringify(input),
  });
  return toTicket(data);
}

export async function updateTicket(workspaceId: string, ticketId: string, input: TicketUpdate): Promise<Ticket> {
  const data = await request<TicketJson>(`/workspaces/${workspaceId}/tickets/${ticketId}`, {
    method: "PATCH",
    body: JSON.stringify(input),
  });
  return toTicket(data);
}

export async function deleteTicket(workspaceId: string, ticketId: string): Promise<void> {
  await request<void>(`/workspaces/${workspaceId}/tickets/${ticketId}`, { method: "DELETE" });
}

// ---------- documents + assistant (still mock) ----------

function delay(ms = 500) {
  return new Promise((resolve) => setTimeout(resolve, ms));
}

export async function getDocuments(workspaceId: string): Promise<Document[]> {
  await delay();
  return mockDocuments.filter((d) => d.workspaceId === workspaceId);
}

export async function askAssistant(workspaceId: string, question: string): Promise<AssistantAnswer> {
  await delay();
  const words = question.toLowerCase().split(/\W+/).filter((w) => w.length > 3);
  const matches = mockDocuments.filter(
    (d) =>
      d.workspaceId === workspaceId &&
      d.status === "READY" &&
      words.some((w) => d.title.toLowerCase().includes(w)),
  );

  if (matches.length === 0) {
    return {
      answer: "I couldn't find enough evidence in this workspace's documents to answer that.",
      citations: [],
    };
  }
  return {
    answer: `Mock answer: based on ${matches.length} document(s), here is what the knowledge base says. Real retrieval + LLM answers arrive in a later phase.`,
    citations: matches.map((d) => ({ documentId: d.id, documentTitle: d.title })),
  };
}
