"use client";

import Link from "next/link";
import { useParams, useRouter } from "next/navigation";
import { useEffect, useState } from "react";
import { EmptyState, ErrorState, LoadingState } from "@/components/AsyncStates";
import { PageHeader } from "@/components/PageHeader";
import { StatusBadge } from "@/components/StatusBadge";
import { useWorkspace } from "@/components/WorkspaceProvider";
import { ApiError, deleteTicket, describeError, getTicket, updateTicket } from "@/lib/api";
import type { Ticket, TicketStatus } from "@/lib/types";

const STATUSES: TicketStatus[] = ["OPEN", "IN_PROGRESS", "RESOLVED"];

export default function TicketDetailPage() {
  const { workspaceId, ticketId } = useParams<{ workspaceId: string; ticketId: string }>();
  const router = useRouter();
  const { canWrite, canDelete } = useWorkspace();
  const [ticket, setTicket] = useState<Ticket | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<ApiError | null>(null);
  const [reloadKey, setReloadKey] = useState(0);
  const [updating, setUpdating] = useState(false);
  const [updateError, setUpdateError] = useState<string | null>(null);
  const [confirmingDelete, setConfirmingDelete] = useState(false);

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
      setUpdateError(describeError(err));
    } finally {
      setUpdating(false);
    }
  }

  async function remove() {
    setUpdating(true);
    setUpdateError(null);
    try {
      await deleteTicket(workspaceId, ticketId);
      router.replace(`/workspaces/${workspaceId}/tickets`);
    } catch (err) {
      setUpdateError(describeError(err));
      setUpdating(false);
    }
  }

  const backLink = (
    <Link href={`/workspaces/${workspaceId}/tickets`} className="button">
      ← Back to tickets
    </Link>
  );

  // 404 / 422 (bad id): not in this workspace, as far as you can see. 403: you may not look.
  // Neither is a "system error", and retrying won't help.
  const notFound = error && (error.status === 404 || error.status === 422);
  const forbidden = error?.status === 403;

  return (
    <>
      <PageHeader title="Ticket" actions={backLink} />
      {loading && <LoadingState label="Loading ticket…" />}
      {!loading && notFound && (
        <EmptyState title="Ticket not found" hint="It does not exist in this workspace, or it was deleted." />
      )}
      {!loading && forbidden && <EmptyState title="No permission" hint={describeError(error)} />}
      {!loading && error && !notFound && !forbidden && (
        <ErrorState message={describeError(error)} requestId={error.requestId} onRetry={() => setReloadKey((k) => k + 1)} />
      )}
      {!loading && !error && ticket && (
        <section className="card detail">
          <h2>{ticket.subject}</h2>
          <dl>
            <dt>Status</dt>
            <dd className="status-edit">
              <StatusBadge status={ticket.status} />
              {/* VIEWER: no edit control. The backend would refuse with 403 anyway. */}
              {canWrite && (
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
              )}
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
          {canDelete && (
            <div className="danger-zone">
              {confirmingDelete ? (
                <>
                  <span>Delete this ticket permanently?</span>
                  <button className="button button-danger" onClick={remove} disabled={updating}>
                    Yes, delete
                  </button>
                  <button className="button" onClick={() => setConfirmingDelete(false)} disabled={updating}>
                    Cancel
                  </button>
                </>
              ) : (
                <button className="button button-danger" onClick={() => setConfirmingDelete(true)}>
                  Delete ticket
                </button>
              )}
            </div>
          )}
        </section>
      )}
    </>
  );
}
