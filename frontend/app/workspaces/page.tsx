"use client";

import Link from "next/link";
import { useRouter } from "next/navigation";
import { useEffect, useState, type FormEvent } from "react";
import { EmptyState, ErrorState, LoadingState } from "@/components/AsyncStates";
import { PageHeader } from "@/components/PageHeader";
import { RequireAuth } from "@/components/RequireAuth";
import { StatusBadge } from "@/components/StatusBadge";
import { ApiError, createWorkspace, describeError, getWorkspaces } from "@/lib/api";
import type { Workspace } from "@/lib/types";

// Anyone logged in can create a workspace; the backend makes them its OWNER.
function NewWorkspaceForm() {
  const router = useRouter();
  const [name, setName] = useState("");
  const [submitting, setSubmitting] = useState(false);
  const [error, setError] = useState<string | null>(null);

  async function handleSubmit(e: FormEvent<HTMLFormElement>) {
    e.preventDefault();
    if (!name.trim()) return setError("Enter a workspace name");
    setSubmitting(true);
    setError(null);
    try {
      const ws = await createWorkspace(name.trim());
      router.push(`/workspaces/${ws.id}/tickets`);
    } catch (err) {
      setError(describeError(err));
      setSubmitting(false);
    }
  }

  return (
    <form className="form-row new-workspace" onSubmit={handleSubmit}>
      <div className="form-field grow">
        <label className="field-label" htmlFor="workspace-name">
          New workspace
        </label>
        <input
          id="workspace-name"
          className={`input${error ? " input-invalid" : ""}`}
          placeholder="e.g. Acme Support"
          maxLength={100}
          value={name}
          onChange={(e) => setName(e.target.value)}
        />
        {error && <p className="field-error">{error}</p>}
      </div>
      <button className="button button-primary" type="submit" disabled={submitting}>
        {submitting ? "Creating…" : "Create workspace"}
      </button>
    </form>
  );
}

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
      <NewWorkspaceForm />
      {loading && <LoadingState label="Loading workspaces…" />}
      {!loading && error && (
        <ErrorState message={describeError(error)} requestId={error.requestId} onRetry={() => setReloadKey((k) => k + 1)} />
      )}
      {!loading && !error && workspaces.length === 0 && (
        <EmptyState
          title="No workspaces yet"
          hint="Create your first workspace above, or ask a workspace OWNER to add you to theirs."
        />
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
