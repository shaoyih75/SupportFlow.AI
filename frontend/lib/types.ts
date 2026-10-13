// Frontend contract types. Field names are camelCase here; lib/api.ts maps
// the FastAPI snake_case JSON into these shapes, so components never see snake_case.

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
  subject: string;
  status: TicketStatus;
  priority: TicketPriority;
  createdAt: string;
};

export type TicketCreate = {
  subject: string;
  priority: TicketPriority;
};

// PATCH body: send only the fields that change.
export type TicketUpdate = Partial<TicketCreate> & { status?: TicketStatus };

export type Page<T> = {
  items: T[];
  page: number;
  pageSize: number;
  total: number;
};

export type Citation = {
  documentId: string;
  documentTitle: string;
};

export type AssistantAnswer = {
  answer: string;
  citations: Citation[];
};
