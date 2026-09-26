"use client";

import { useParams } from "next/navigation";
import { useEffect, useState } from "react";
import { EmptyState, ErrorState, LoadingState } from "@/components/AsyncStates";
import { DocumentCard } from "@/components/DocumentCard";
import { PageHeader } from "@/components/PageHeader";
import { getDocuments } from "@/lib/api";
import type { Document, DocumentStatus } from "@/lib/types";

type StatusFilter = "ALL" | DocumentStatus;
const STATUS_FILTERS: StatusFilter[] = ["ALL", "READY", "PROCESSING", "FAILED"];

export default function DocumentsPage() {
  const { workspaceId } = useParams<{ workspaceId: string }>();

  // Server data + request state
  const [documents, setDocuments] = useState<Document[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [reloadKey, setReloadKey] = useState(0);

  // UI state (controlled inputs)
  const [query, setQuery] = useState("");
  const [statusFilter, setStatusFilter] = useState<StatusFilter>("ALL");

  useEffect(() => {
    let cancelled = false;
    setLoading(true);
    setError(null);
    getDocuments(workspaceId)
      .then((docs) => !cancelled && setDocuments(docs))
      .catch(() => !cancelled && setError("Failed to load documents"))
      .finally(() => !cancelled && setLoading(false));
    return () => {
      cancelled = true;
    };
  }, [workspaceId, reloadKey]);

  // Derived data: computed from documents + query + statusFilter, so it is NOT state.
  const filtered = documents.filter(
    (doc) =>
      doc.title.toLowerCase().includes(query.toLowerCase()) &&
      (statusFilter === "ALL" || doc.status === statusFilter),
  );

  return (
    <>
      <PageHeader title="Documents" description="Knowledge base documents registered in this workspace." />

      <div className="toolbar">
        <input
          className="input"
          value={query}
          onChange={(e) => setQuery(e.target.value)}
          placeholder="Search documents"
          aria-label="Search documents"
        />
        <div className="segmented" role="group" aria-label="Filter by status">
          {STATUS_FILTERS.map((s) => (
            <button key={s} className={s === statusFilter ? "active" : ""} onClick={() => setStatusFilter(s)}>
              {s}
            </button>
          ))}
        </div>
      </div>

      {loading && <LoadingState label="Loading documents…" />}
      {!loading && error && <ErrorState message={error} onRetry={() => setReloadKey((k) => k + 1)} />}
      {!loading && !error && documents.length === 0 && (
        <EmptyState title="No documents yet" hint="Documents registered in this workspace will show up here." />
      )}
      {!loading && !error && documents.length > 0 && filtered.length === 0 && (
        <EmptyState title="No documents match your filters" hint="Try a different search or status." />
      )}
      {!loading && !error && filtered.length > 0 && (
        <div className="card-grid">
          {filtered.map((doc) => (
            <DocumentCard
              key={doc.id}
              title={doc.title}
              sourceType={doc.sourceType}
              status={doc.status}
              updatedAt={doc.updatedAt}
            />
          ))}
        </div>
      )}
    </>
  );
}
