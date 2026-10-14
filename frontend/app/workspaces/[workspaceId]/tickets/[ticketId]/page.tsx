"use client";

import Link from "next/link";
import { useParams } from "next/navigation";
import { useEffect, useState } from "react";
import { EmptyState, ErrorState, LoadingState } from "@/components/AsyncStates";
import { PageHeader } from "@/components/PageHeader";
import { StatusBadge } from "@/components/StatusBadge";
import { ApiError, getTicket, updateTicket } from "@/lib/api";
import type { Ticket, TicketStatus } from "@/lib/types";

const STATUSES: TicketStatus[] = ["OPEN", "IN_PROGRESS", "RESOLVED"];

export default function TicketDetailPage() {
  const { workspaceId, ticketId } = useParams<{ workspaceId: string; ticketId: string }>();
  const [ticket, setTicket] = useState<Ticket | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<ApiError | null>(null);
  const [reloadKey, setReloadKey] = useState(0);
  const [updating, setUpdating] = useState(false);
  const [updateError, setUpdateError] = useState<string | null>(null);

  useEffect(() => {
    let cancelled = false;
    setLoading(true);
    setError(null);
    getTicket(workspaceId, ticketId)
      .then((t) => !cancelled && setTicket(t))
      .catch((err) => !cancelled && setError(err instanceof ApiError ? err : new ApiError(0, "UNKNOWN", "Failed to load ticket")))
      .finally(() => !cancelled && setLoading(false));
    return () => {
      cancelled = true;
    };
  }, [workspaceId, ticketId, reloadKey]);

  async function changeStatus(status: TicketStatus) {
    setUpdating(true);
    setUpdateError(null);
    try {
      setTicket(await updateTicket(workspaceId, ticketId, { status }));
    } catch (err) {
      setUpdateError(err instanceof Error ? err.message : "Failed to update ticket");
    } finally {
      setUpdating(false);
    }
  }

  const backLink = (
    <Link href={`/workspaces/${workspaceId}/tickets`} className="button">
      ← Back to tickets
    </Link>
  );

  // 404 / 422 (bad id) are "not found" for the user; retrying won't help.
  const notFound = error && (error.status === 404 || error.status === 422);

  return (
    <>
      <PageHeader title="Ticket" actions={backLink} />
      {loading && <LoadingState label="Loading ticket…" />}
      {!loading && notFound && <EmptyState title="Ticket not found" hint={`No ticket with id "${ticketId}".`} />}
      {!loading && error && !notFound && (
        <ErrorState message={error.message} requestId={error.requestId} onRetry={() => setReloadKey((k) => k + 1)} />
      )}
      {!loading && !error && ticket && (
        <section className="card detail">
          <h2>{ticket.subject}</h2>
          <dl>
            <dt>Status</dt>
            <dd className="status-edit">
              <StatusBadge status={ticket.status} />
              <select
                className="select select-inline"
                aria-label="Change status"
                value={ticket.status}
                disabled={updating}
                onChange={(e) => changeStatus(e.target.value as TicketStatus)}
              >
                {STATUSES.map((s) => (
                  <option key={s} value={s}>
                    {s.replace("_", " ")}
                  </option>
                ))}
              </select>
              {updating && <span className="muted">Saving…</span>}
            </dd>
            <dt>Priority</dt>
            <dd><StatusBadge status={ticket.priority} /></dd>
            <dt>Created</dt>
            <dd>{new Date(ticket.createdAt).toLocaleString()}</dd>
            <dt>ID</dt>
            <dd className="mono">{ticket.id}</dd>
          </dl>
          {updateError && <p className="field-error">{updateError}</p>}
        </section>
      )}
    </>
  );
}
