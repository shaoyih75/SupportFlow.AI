import type { Document, Ticket, Workspace } from "./types";

// Only lib/api.ts should import this file. Pages and components never read mock data directly.

export const mockWorkspaces: Workspace[] = [
  { id: "ws-acme", name: "Acme Support", role: "OWNER", memberCount: 8 },
  { id: "ws-empty", name: "New Team (empty)", role: "MEMBER", memberCount: 1 },
  { id: "ws-broken", name: "Broken API (error demo)", role: "MEMBER", memberCount: 3 },
];

export const mockDocuments: Document[] = [
  { id: "doc-101", workspaceId: "ws-acme", title: "Employee Handbook", sourceType: "pdf", status: "READY", updatedAt: "2026-09-24T10:12:00Z" },
  { id: "doc-102", workspaceId: "ws-acme", title: "Refund Policy 2026", sourceType: "docx", status: "READY", updatedAt: "2026-09-23T16:40:00Z" },
  { id: "doc-103", workspaceId: "ws-acme", title: "Onboarding Checklist", sourceType: "markdown", status: "PROCESSING", updatedAt: "2026-09-25T08:05:00Z" },
  { id: "doc-104", workspaceId: "ws-acme", title: "API Rate Limit FAQ", sourceType: "url", status: "PROCESSING", updatedAt: "2026-09-25T09:30:00Z" },
  { id: "doc-105", workspaceId: "ws-acme", title: "Legacy Pricing Sheet", sourceType: "pdf", status: "FAILED", updatedAt: "2026-09-20T13:15:00Z" },
  { id: "doc-106", workspaceId: "ws-acme", title: "Escalation Playbook", sourceType: "docx", status: "READY", updatedAt: "2026-09-18T11:00:00Z" },
];

export const mockTickets: Ticket[] = [
  { id: "tk-1", workspaceId: "ws-acme", title: "Customer cannot reset password", status: "OPEN", priority: "HIGH", createdAt: "2026-09-25T07:10:00Z" },
  { id: "tk-2", workspaceId: "ws-acme", title: "Refund request for duplicate charge", status: "IN_PROGRESS", priority: "MEDIUM", createdAt: "2026-09-24T15:22:00Z" },
  { id: "tk-3", workspaceId: "ws-acme", title: "How to export invoices as CSV?", status: "RESOLVED", priority: "LOW", createdAt: "2026-09-22T09:45:00Z" },
  { id: "tk-4", workspaceId: "ws-acme", title: "API returns 429 during bulk import", status: "OPEN", priority: "HIGH", createdAt: "2026-09-25T11:02:00Z" },
  { id: "tk-5", workspaceId: "ws-acme", title: "Update billing contact email", status: "RESOLVED", priority: "LOW", createdAt: "2026-09-19T14:30:00Z" },
];
