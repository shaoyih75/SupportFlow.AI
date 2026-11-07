// Frontend contract types. Field names are camelCase here; lib/api.ts maps
// the FastAPI snake_case JSON into these shapes, so components never see snake_case.

export type WorkspaceRole = "OWNER" | "MEMBER" | "VIEWER";

export type User = {
  id: string;
  name: string;
  email: string;
};

export type Workspace = {
  id: string;
  name: string;
  role: WorkspaceRole;
  memberCount: number;
};

// PENDING: upload started · UPLOADED: the server verified the file in S3 · EXPIRED: never arrived
export type DocumentStatus = "PENDING" | "UPLOADED" | "EXPIRED";

// Metadata from PostgreSQL. The file itself lives in S3 and is fetched with a short-lived download URL.
export type Document = {
  id: string;
  workspaceId: string;
  filename: string;
  contentType: string;
  sizeBytes: number;
  status: DocumentStatus;
  createdAt: string; // ISO 8601
  uploadedAt: string | null;
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
