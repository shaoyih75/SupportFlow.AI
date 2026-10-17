"use client";

import Link from "next/link";
import { useEffect, useState } from "react";
import { EmptyState, ErrorState, LoadingState } from "@/components/AsyncStates";
import { PageHeader } from "@/components/PageHeader";
import { RequireAuth } from "@/components/RequireAuth";
import { StatusBadge } from "@/components/StatusBadge";
import { ApiError, describeError, getWorkspaces } from "@/lib/api";
import type { Workspace } from "@/lib/types";

function WorkspaceList() {
  const [workspaces, setWorkspaces] = useState<Workspace[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<ApiError | null>(null);
  const [reloadKey, setReloadKey] = useState(0);

  useEffect(() => {
    let cancelled = false;
    setLoading(true);
    setError(null);
    getWorkspaces()
      .then((ws) => !cancelled && setWorkspaces(ws))
      .catch((err) => !cancelled && setError(err instanceof ApiError ? err : new ApiError(0, "UNKNOWN", describeError(err))))
      .finally(() => !cancelled && setLoading(false));
    return () => {
      cancelled = true;
    };
  }, [reloadKey]);

  return (
    <main className="content content-narrow">
      <PageHeader title="My workspaces" description="Only workspaces where you are an active member are listed." />
      {loading && <LoadingState label="Loading workspaces…" />}
      {!loading && error && (
        <ErrorState message={describeError(error)} requestId={error.requestId} onRetry={() => setReloadKey((k) => k + 1)} />
      )}
      {!loading && !error && workspaces.length === 0 && (
        <EmptyState title="No workspaces yet" hint="Ask a workspace OWNER to add you." />
      )}
      {!loading && !error && workspaces.length > 0 && (
        <div className="list">
          {workspaces.map((w) => (
            <Link key={w.id} href={`/workspaces/${w.id}`} className="card ticket-card">
              <div>
                <h3>{w.name}</h3>
                <p className="card-meta">{w.memberCount} member(s)</p>
              </div>
              <StatusBadge status={w.role} />
            </Link>
          ))}
        </div>
      )}
    </main>
  );
}

export default function WorkspacesPage() {
  return (
    <RequireAuth>
      <WorkspaceList />
    </RequireAuth>
  );
}
