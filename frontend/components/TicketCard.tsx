import Link from "next/link";
import type { TicketPriority, TicketStatus } from "@/lib/types";
import { StatusBadge } from "./StatusBadge";

type TicketCardProps = {
  subject: string;
  status: TicketStatus;
  priority: TicketPriority;
  createdAt: string;
  href: string;
};

export function TicketCard({ subject, status, priority, createdAt, href }: TicketCardProps) {
  return (
    <Link href={href} className="card ticket-card">
      <div>
        <h3>{subject}</h3>
        <p className="card-meta">Opened {new Date(createdAt).toLocaleString()}</p>
      </div>
      <div className="ticket-badges">
        <StatusBadge status={priority} />
        <StatusBadge status={status} />
      </div>
    </Link>
  );
}
