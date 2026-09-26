import type { TicketPriority, TicketStatus } from "@/lib/types";
import { StatusBadge } from "./StatusBadge";

type TicketCardProps = {
  title: string;
  status: TicketStatus;
  priority: TicketPriority;
  createdAt: string;
};

export function TicketCard({ title, status, priority, createdAt }: TicketCardProps) {
  return (
    <article className="card ticket-card">
      <div>
        <h3>{title}</h3>
        <p className="card-meta">Opened {new Date(createdAt).toLocaleDateString()}</p>
      </div>
      <div className="ticket-badges">
        <StatusBadge status={priority} />
        <StatusBadge status={status} />
      </div>
    </article>
  );
}
