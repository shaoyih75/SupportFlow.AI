"use client";

import { useParams } from "next/navigation";
import { useEffect, useState } from "react";
import { EmptyState, ErrorState, LoadingState } from "@/components/AsyncStates";
import { PageHeader } from "@/components/PageHeader";
import { TicketCard } from "@/components/TicketCard";
import { TICKET_SUBJECT_INPUT_ID, TicketForm } from "@/components/TicketForm";
import { useWorkspace } from "@/components/WorkspaceProvider";
import { ApiError, describeError, getTickets } from "@/lib/api";
import type { Page, Ticket, TicketStatus } from "@/lib/types";

type StatusFilter = "ALL" | TicketStatus;
const STATUS_FILTERS: StatusFilter[] = ["ALL", "OPEN", "IN_PROGRESS", "RESOLVED"];
const PAGE_SIZE = 5;

export default function TicketsPage() {
  const { workspaceId } = useParams<{ workspaceId: string }>();
  const { canWrite, role } = useWorkspace();
  const [data, setData] = useState<Page<Ticket> | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<ApiError | null>(null);
  const [reloadKey, setReloadKey] = useState(0);

  // Filter and page are sent to the API as query params (server-side filtering).
  const [statusFilter, setStatusFilter] = useState<StatusFilter>("ALL");
  const [page, setPage] = useState(1);

  useEffect(() => {
    let cancelled = false;
    setLoading(true);
    setError(null);
    getTickets(workspaceId, {
      page,
      pageSize: PAGE_SIZE,
      status: statusFilter === "ALL" ? undefined : statusFilter,
    })
      .then((result) => !cancelled && setData(result))
      .catch((err) => !cancelled && setError(err instanceof ApiError ? err : new ApiError(0, "UNKNOWN", "Failed to load tickets")))
      .finally(() => !cancelled && setLoading(false));
    return () => {
      cancelled = true;
    };
  }, [workspaceId, statusFilter, page, reloadKey]);

  const totalPages = data ? Math.max(1, Math.ceil(data.total / data.pageSize)) : 1;

  function changeFilter(next: StatusFilter) {
    setStatusFilter(next);
    setPage(1);
  }

  function handleCreated() {
    // Show the new ticket: it is OPEN and newest, so it lands on page 1 of ALL/OPEN.
    if (statusFilter === "IN_PROGRESS" || statusFilter === "RESOLVED") setStatusFilter("ALL");
    setPage(1);
    setReloadKey((k) => k + 1);
  }

  return (
    <>
      <PageHeader title="Tickets" description="Customer support tickets, served by FastAPI." />

      {canWrite ? (
        <TicketForm workspaceId={workspaceId} onCreated={handleCreated} />
      ) : (
        <p className="notice">You have read-only access ({role}). Ask an OWNER for MEMBER access to create tickets.</p>
      )}

      <div className="toolbar">
        <div className="segmented" role="group" aria-label="Filter by status">
          {STATUS_FILTERS.map((s) => (
            <button key={s} className={s === statusFilter ? "active" : ""} onClick={() => changeFilter(s)}>
              {s.replace("_", " ")}
            </button>
          ))}
        </div>
        {data && !loading && <span className="muted">{data.total} ticket(s)</span>}
      </div>

      {loading && <LoadingState label="Loading tickets…" />}
      {!loading && error && (
        <ErrorState message={describeError(error)} requestId={error.requestId} onRetry={() => setReloadKey((k) => k + 1)} />
      )}
      {!loading && !error && data && data.items.length === 0 && (
        <EmptyState
          title={statusFilter === "ALL" ? "No tickets yet" : "No tickets with this status"}
          hint="Tickets created in this workspace will show up here."
          action={
            canWrite ? (
              <button className="button button-primary" onClick={() => document.getElementById(TICKET_SUBJECT_INPUT_ID)?.focus()}>
                Create ticket
              </button>
            ) : undefined
          }
        />
      )}
      {!loading && !error && data && data.items.length > 0 && (
        <>
          <div className="list">
            {data.items.map((t) => (
              <TicketCard
                key={t.id}
                subject={t.subject}
                status={t.status}
                priority={t.priority}
                createdAt={t.createdAt}
                href={`/workspaces/${workspaceId}/tickets/${t.id}`}
              />
            ))}
          </div>
          {totalPages > 1 && (
            <div className="pagination">
              <button className="button" disabled={page <= 1} onClick={() => setPage((p) => p - 1)}>
                ← Prev
              </button>
              <span className="muted">
                Page {page} of {totalPages}
              </span>
              <button className="button" disabled={page >= totalPages} onClick={() => setPage((p) => p + 1)}>
                Next →
              </button>
            </div>
          )}
        </>
      )}
    </>
  );
}
