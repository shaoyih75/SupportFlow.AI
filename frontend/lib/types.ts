// Frontend contract types. These mirror the Phase 1 data model
// (users / workspaces / documents / processing_jobs) plus Tickets.
// When the FastAPI backend lands, lib/api.ts maps snake_case JSON into these.

export type WorkspaceRole = "OWNER" | "MEMBER";

export type Workspace = {
  id: string;
  name: string;
  role: WorkspaceRole;
  memberCount: number;
};

export type DocumentStatus = "READY" | "PROCESSING" | "FAILED";
export type SourceType = "pdf" | "docx" | "markdown" | "url";

export type Document = {
  id: string;
  workspaceId: string;
  title: string;
  sourceType: SourceType;
  status: DocumentStatus;
  updatedAt: string; // ISO 8601
};

export type JobStatus = "PENDING" | "RUNNING" | "SUCCEEDED" | "FAILED";

export type ProcessingJob = {
  id: string;
  documentId: string;
  status: JobStatus;
  errorMessage: string | null;
  createdAt: string;
};

export type TicketStatus = "OPEN" | "IN_PROGRESS" | "RESOLVED";
export type TicketPriority = "LOW" | "MEDIUM" | "HIGH";

export type Ticket = {
  id: string;
  workspaceId: string;
  title: string;
  status: TicketStatus;
  priority: TicketPriority;
  createdAt: string;
};

export type Citation = {
  documentId: string;
  documentTitle: string;
};

export type AssistantAnswer = {
  answer: string;
  citations: Citation[];
};
