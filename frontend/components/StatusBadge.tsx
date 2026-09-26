import type { DocumentStatus, JobStatus, TicketPriority, TicketStatus } from "@/lib/types";

// StatusBadge only needs the status value, not the whole Document/Ticket.
// Smaller props = lower coupling = reusable on every page.
export type BadgeValue = DocumentStatus | JobStatus | TicketStatus | TicketPriority;

type Tone = "success" | "warning" | "danger" | "info" | "neutral";

const TONES: Record<BadgeValue, Tone> = {
  READY: "success",
  SUCCEEDED: "success",
  RESOLVED: "success",
  PROCESSING: "warning",
  RUNNING: "warning",
  IN_PROGRESS: "warning",
  MEDIUM: "warning",
  FAILED: "danger",
  HIGH: "danger",
  PENDING: "info",
  OPEN: "info",
  LOW: "neutral",
};

type StatusBadgeProps = {
  status: BadgeValue;
};

export function StatusBadge({ status }: StatusBadgeProps) {
  return <span className={`badge badge-${TONES[status]}`}>{status.replace("_", " ")}</span>;
}
