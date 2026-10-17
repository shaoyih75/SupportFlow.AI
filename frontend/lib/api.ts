// Frontend/backend boundary. Every page gets data through these functions.
// Workspaces and Tickets come from FastAPI; Documents and the Assistant are still mock.
//
// Auth: every request carries `Authorization: Bearer <token>`. The UI may hide buttons a role
// can't use, but the backend re-checks every request: the frontend is never the security boundary.

import { clearAccessToken, getAccessToken, redirectToLogin } from "./auth";
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
  User,
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

// Human messages per status, so 401 / 403 / 404 never all look like "something broke".
const STATUS_MESSAGES: Record<number, string> = {
  401: "Your session has expired. Please log in again.",
  403: "You do not have permission for this action.",
  404: "Not found, or not visible to you.",
};

type RequestOptions = RequestInit & { auth?: boolean };

async function request<T>(path: string, { auth = true, ...init }: RequestOptions = {}): Promise<T> {
  const token = auth ? getAccessToken() : null;
  let response: Response;
  try {
    response = await fetch(`${API_URL}${path}`, {
      ...init,
      headers: {
        "Content-Type": "application/json",
        ...init.headers,
        ...(token ? { Authorization: `Bearer ${token}` } : {}),
      },
    });
  } catch {
    throw new ApiError(0, "NETWORK_ERROR", "Cannot reach the API server. Is FastAPI running?");
  }

  if (!response.ok) {
    const error = await ApiError.fromResponse(response);
    if (response.status === 401 && auth) {
      // No trusted identity: drop the stale token and send the user to log in.
      clearAccessToken();
      redirectToLogin();
    }
    throw error;
  }
  if (response.status === 204) return undefined as T;
  return response.json();
}

// What to show the user. The backend's own message stays on error.message for debugging.
export function describeError(error: unknown): string {
  if (error instanceof ApiError) return STATUS_MESSAGES[error.status] ?? error.message;
  return error instanceof Error ? error.message : "Something went wrong";
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

// ---------- auth ----------

type UserJson = { id: string; name: string; email: string };

export async function login(email: string, password: string): Promise<string> {
  // auth: false — no token yet, and a 401 here means "wrong password", not "session expired".
  const data = await request<{ access_token: string; token_type: string }>("/auth/login", {
    method: "POST",
    body: JSON.stringify({ email, password }),
    auth: false,
  });
  return data.access_token;
}

// Creates the account (plus a personal workspace on the backend). Does not log in: call login() next.
// 409 EMAIL_ALREADY_EXISTS for a taken email, 422 with fieldErrors for invalid input.
export async function register(name: string, email: string, password: string): Promise<User> {
  // auth: false — a 401/409 here is about the form, not an expired session.
  const data = await request<{ user: UserJson; personal_workspace_id: string }>("/auth/register", {
    method: "POST",
    body: JSON.stringify({ name, email, password }),
    auth: false,
  });
  return { id: data.user.id, name: data.user.name, email: data.user.email };
}

export async function getMe(): Promise<User> {
  const u = await request<UserJson>("/auth/me");
  return { id: u.id, name: u.name, email: u.email };
}

// ---------- workspaces ----------

export async function getWorkspaces(): Promise<Workspace[]> {
  const data = await request<WorkspaceJson[]>("/workspaces");
  return data.map(toWorkspace);
}

// The backend makes the current user the new workspace's OWNER (role comes back in the response).
export async function createWorkspace(name: string): Promise<Workspace> {
  const data = await request<WorkspaceJson>("/workspaces", { method: "POST", body: JSON.stringify({ name }) });
  return toWorkspace(data);
}

// 403 when the current user has no ACTIVE membership; also returns the user's role here.
export async function getWorkspace(workspaceId: string): Promise<Workspace> {
  return toWorkspace(await request<WorkspaceJson>(`/workspaces/${workspaceId}`));
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
