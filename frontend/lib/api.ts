// Frontend/backend boundary. Every page gets data through these functions.
// Today they return mock data after a fake network delay; next lesson their
// bodies become fetch() calls to FastAPI and the React components stay unchanged.

import { mockDocuments, mockTickets, mockWorkspaces } from "./mock-data";
import type { AssistantAnswer, Document, Ticket, Workspace } from "./types";

const MOCK_DELAY_MS = 500;

// "ws-broken" lets us see the error state in the UI without a real server.
const BROKEN_WORKSPACE_ID = "ws-broken";

function delay(ms = MOCK_DELAY_MS) {
  return new Promise((resolve) => setTimeout(resolve, ms));
}

export class ApiError extends Error {
  constructor(
    public status: number,
    message: string,
  ) {
    super(message);
    this.name = "ApiError";
  }
}

async function assertWorkspaceReachable(workspaceId: string) {
  await delay();
  if (workspaceId === BROKEN_WORKSPACE_ID) {
    throw new ApiError(500, "Server error while loading workspace data");
  }
  if (!mockWorkspaces.some((w) => w.id === workspaceId)) {
    throw new ApiError(404, "Workspace not found");
  }
}

export async function getWorkspaces(): Promise<Workspace[]> {
  await delay(150);
  return mockWorkspaces;
}

export async function getDocuments(workspaceId: string): Promise<Document[]> {
  await assertWorkspaceReachable(workspaceId);
  return mockDocuments.filter((d) => d.workspaceId === workspaceId);
}

export async function getTickets(workspaceId: string): Promise<Ticket[]> {
  await assertWorkspaceReachable(workspaceId);
  return mockTickets.filter((t) => t.workspaceId === workspaceId);
}

export async function askAssistant(workspaceId: string, question: string): Promise<AssistantAnswer> {
  await assertWorkspaceReachable(workspaceId);
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
