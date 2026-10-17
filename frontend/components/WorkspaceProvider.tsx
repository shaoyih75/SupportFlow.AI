"use client";

import Link from "next/link";
import { createContext, useContext, useEffect, useState, type ReactNode } from "react";
import { ApiError, describeError, getWorkspace } from "@/lib/api";
import type { Workspace, WorkspaceRole } from "@/lib/types";
import { EmptyState, ErrorState, LoadingState } from "./AsyncStates";

type WorkspaceAccess = {
  workspace: Workspace | null;
  role: WorkspaceRole | null;
  // Mirrors the backend RBAC table so the UI can hide what would be refused anyway.
  canWrite: boolean;
  canDelete: boolean;
  loading: boolean;
  error: ApiError | null;
  reload: () => void;
};

const WorkspaceContext = createContext<WorkspaceAccess | null>(null);

export function useWorkspace(): WorkspaceAccess {
  const value = useContext(WorkspaceContext);
  if (!value) throw new Error("useWorkspace must be used inside <WorkspaceProvider>");
  return value;
}

export function WorkspaceProvider({ workspaceId, children }: { workspaceId: string; children: ReactNode }) {
  const [workspace, setWorkspace] = useState<Workspace | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<ApiError | null>(null);
  const [reloadKey, setReloadKey] = useState(0);

  useEffect(() => {
    let cancelled = false;
    setLoading(true);
    setError(null);
    getWorkspace(workspaceId)
      .then((ws) => !cancelled && setWorkspace(ws))
      .catch((err) => !cancelled && setError(err instanceof ApiError ? err : new ApiError(0, "UNKNOWN", describeError(err))))
      .finally(() => !cancelled && setLoading(false));
    return () => {
      cancelled = true;
    };
  }, [workspaceId, reloadKey]);

  const role = workspace?.role ?? null;
  const value: WorkspaceAccess = {
    workspace,
    role,
    canWrite: role === "OWNER" || role === "MEMBER",
    canDelete: role === "OWNER",
    loading,
    error,
    reload: () => setReloadKey((k) => k + 1),
  };
  return <WorkspaceContext.Provider value={value}>{children}</WorkspaceContext.Provider>;
}

// Renders the page only once membership is confirmed; otherwise a clear 403 / error screen.
export function WorkspaceGate({ children }: { children: ReactNode }) {
  const { loading, error, reload } = useWorkspace();

  if (loading) return <LoadingState label="Checking workspace access…" />;
  if (error?.status === 403) {
    // A 403 is shown as "no access", not disguised as "not found".
    return (
      <EmptyState
        title="You don't have access to this workspace"
        hint="Ask a workspace OWNER to add you, or pick one of your own workspaces."
        action={
          <Link href="/workspaces" className="button button-primary">
            My workspaces
          </Link>
        }
      />
    );
  }
  if (error) return <ErrorState message={describeError(error)} requestId={error.requestId} onRetry={reload} />;
  return <>{children}</>;
}
