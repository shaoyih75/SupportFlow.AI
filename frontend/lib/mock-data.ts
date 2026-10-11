import { DEFAULT_WORKSPACE_ID } from "./config";
import type { Document } from "./types";

// Only lib/api.ts should import this file. Pages and components never read mock data directly.
// Workspaces and Tickets now come from FastAPI; only Documents are still mocked.

const ACME = DEFAULT_WORKSPACE_ID;

export const mockDocuments: Document[] = [
  { id: "doc-101", workspaceId: ACME, title: "Employee Handbook", sourceType: "pdf", status: "READY", updatedAt: "2026-09-24T10:12:00Z" },
  { id: "doc-102", workspaceId: ACME, title: "Refund Policy 2026", sourceType: "docx", status: "READY", updatedAt: "2026-09-23T16:40:00Z" },
  { id: "doc-103", workspaceId: ACME, title: "Onboarding Checklist", sourceType: "markdown", status: "PROCESSING", updatedAt: "2026-09-25T08:05:00Z" },
  { id: "doc-104", workspaceId: ACME, title: "API Rate Limit FAQ", sourceType: "url", status: "PROCESSING", updatedAt: "2026-09-25T09:30:00Z" },
  { id: "doc-105", workspaceId: ACME, title: "Legacy Pricing Sheet", sourceType: "pdf", status: "FAILED", updatedAt: "2026-09-20T13:15:00Z" },
  { id: "doc-106", workspaceId: ACME, title: "Escalation Playbook", sourceType: "docx", status: "READY", updatedAt: "2026-09-18T11:00:00Z" },
];
