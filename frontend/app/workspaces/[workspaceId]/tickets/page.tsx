"use client";

import { useParams } from "next/navigation";
import { useEffect, useState } from "react";
import { EmptyState, ErrorState, LoadingState } from "@/components/AsyncStates";
import { PageHeader } from "@/components/PageHeader";
import { TicketCard } from "@/components/TicketCard";
import { getTickets } from "@/lib/api";
import type { Ticket, TicketStatus } from "@/lib/types";

type StatusFilter = "ALL" | TicketStatus;
const STATUS_FILTERS: StatusFilter[] = ["ALL", "OPEN", "IN_PROGRESS", "RESOLVED"];

export default function TicketsPage() {
  const { workspaceId } = useParams<{ workspaceId: string }>();
  const [tickets, setTickets] = useState<Ticket[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [reloadKey, setReloadKey] = useState(0);
  const [statusFilter, setStatusFilter] = useState<StatusFilter>("ALL");

  useEffect(() => {
    let cancelled = false;
    setLoading(true);
    setError(null);
    getTickets(workspaceId)
      .then((tks) => !cancelled && setTickets(tks))
      .catch(() => !cancelled && setError("Failed to load tickets"))
      .finally(() => !cancelled && setLoading(false));
    return () => {
      cancelled = true;
    };
  }, [workspaceId, reloadKey]);

  const filtered = statusFilter === "ALL" ? tickets : tickets.filter((t) => t.status === statusFilter);

  return (
    <>
      <PageHeader title="Tickets" description="Customer support tickets for this workspace." />

      <div className="toolbar">
        <label className="field-label" htmlFor="ticket-status">
          Status
        </label>
        <select
          id="ticket-status"
          className="select select-inline"
          value={statusFilter}
          onChange={(e) => setStatusFilter(e.target.value as StatusFilter)}
        >
          {STATUS_FILTERS.map((s) => (
            <option key={s} value={s}>
              {s.replace("_", " ")}
            </option>
          ))}
        </select>
      </div>

      {loading && <LoadingState label="Loading tickets…" />}
      {!loading && error && <ErrorState message={error} onRetry={() => setReloadKey((k) => k + 1)} />}
      {!loading && !error && filtered.length === 0 && (
        <EmptyState title={tickets.length === 0 ? "No tickets yet" : "No tickets with this status"} />
      )}
      {!loading && !error && filtered.length > 0 && (
        <div className="list">
          {filtered.map((t) => (
            <TicketCard key={t.id} title={t.title} status={t.status} priority={t.priority} createdAt={t.createdAt} />
          ))}
        </div>
      )}
    </>
  );
}
