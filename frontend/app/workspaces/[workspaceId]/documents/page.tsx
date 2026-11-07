"use client";

import { useParams } from "next/navigation";
import { useEffect, useState } from "react";
import { EmptyState, ErrorState, LoadingState } from "@/components/AsyncStates";
import { DocumentCard } from "@/components/DocumentCard";
import { DocumentUpload } from "@/components/DocumentUpload";
import { PageHeader } from "@/components/PageHeader";
import { useWorkspace } from "@/components/WorkspaceProvider";
import { describeError, getDocuments, getDownloadUrl } from "@/lib/api";
import type { Document, DocumentStatus } from "@/lib/types";

type StatusFilter = "ALL" | DocumentStatus;
const STATUS_FILTERS: StatusFilter[] = ["ALL", "UPLOADED", "PENDING", "EXPIRED"];

export default function DocumentsPage() {
  const { workspaceId } = useParams<{ workspaceId: string }>();
  const { canWrite, role } = useWorkspace();

  // Server data + request state
  const [documents, setDocuments] = useState<Document[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [reloadKey, setReloadKey] = useState(0);
  const [downloadError, setDownloadError] = useState<string | null>(null);

  // UI state (controlled inputs)
  const [query, setQuery] = useState("");
  const [statusFilter, setStatusFilter] = useState<StatusFilter>("ALL");

  useEffect(() => {
    let cancelled = false;
    setLoading(true);
    setError(null);
    getDocuments(workspaceId)
      .then((docs) => !cancelled && setDocuments(docs))
      .catch((err) => !cancelled && setError(describeError(err)))
      .finally(() => !cancelled && setLoading(false));
    return () => {
      cancelled = true;
    };
  }, [workspaceId, reloadKey]);

  // Derived data: computed from documents + query + statusFilter, so it is NOT state.
  const filtered = documents.filter(
    (doc) =>
      doc.filename.toLowerCase().includes(query.toLowerCase()) &&
      (statusFilter === "ALL" || doc.status === statusFilter),
  );

  async function download(doc: Document) {
    setDownloadError(null);
    try {
      // A fresh 5-minute link each time; the browser then downloads from S3 directly.
      window.location.href = await getDownloadUrl(workspaceId, doc.id);
    } catch (err) {
      setDownloadError(describeError(err));
    }
  }

  return (
    <>
      <PageHeader
        title="Documents"
        description="Files are stored in S3; this list is their metadata from PostgreSQL."
      />

      {canWrite ? (
        <DocumentUpload workspaceId={workspaceId} onUploaded={() => setReloadKey((k) => k + 1)} />
      ) : (
        <p className="notice">You have read-only access ({role}). Ask an OWNER for MEMBER access to upload documents.</p>
      )}

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
      {downloadError && <p className="field-error">{downloadError}</p>}

      {loading && <LoadingState label="Loading documents…" />}
      {!loading && error && <ErrorState message={error} onRetry={() => setReloadKey((k) => k + 1)} />}
      {!loading && !error && documents.length === 0 && (
        <EmptyState title="No documents yet" hint="Upload a PDF, TXT or Markdown file to start the knowledge base." />
      )}
      {!loading && !error && documents.length > 0 && filtered.length === 0 && (
        <EmptyState title="No documents match your filters" hint="Try a different search or status." />
      )}
      {!loading && !error && filtered.length > 0 && (
        <div className="card-grid">
          {filtered.map((doc) => (
            <DocumentCard key={doc.id} document={doc} onDownload={() => download(doc)} />
          ))}
        </div>
      )}
    </>
  );
}
