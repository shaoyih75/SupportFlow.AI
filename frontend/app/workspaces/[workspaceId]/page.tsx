"use client";

import Link from "next/link";
import { useParams } from "next/navigation";
import { useEffect, useState } from "react";
import { ErrorState, LoadingState } from "@/components/AsyncStates";
import { PageHeader } from "@/components/PageHeader";
import { getDocuments, getTickets } from "@/lib/api";
import type { Document, Ticket } from "@/lib/types";

export default function DashboardPage() {
  const { workspaceId } = useParams<{ workspaceId: string }>();
  const [documents, setDocuments] = useState<Document[]>([]);
  const [tickets, setTickets] = useState<Ticket[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [reloadKey, setReloadKey] = useState(0);

  useEffect(() => {
    let cancelled = false;
    setLoading(true);
    setError(null);
    Promise.all([getDocuments(workspaceId), getTickets(workspaceId)])
      .then(([docs, tks]) => {
        if (cancelled) return;
        setDocuments(docs);
        setTickets(tks);
      })
      .catch(() => !cancelled && setError("Failed to load dashboard"))
      .finally(() => !cancelled && setLoading(false));
    return () => {
      cancelled = true;
    };
  }, [workspaceId, reloadKey]);

  const base = `/workspaces/${workspaceId}`;
  const stats = [
    { label: "Documents", value: documents.length, href: `${base}/documents` },
    { label: "Ready", value: documents.filter((d) => d.status === "READY").length, href: `${base}/documents` },
    { label: "Processing", value: documents.filter((d) => d.status === "PROCESSING").length, href: `${base}/documents` },
    { label: "Open tickets", value: tickets.filter((t) => t.status !== "RESOLVED").length, href: `${base}/tickets` },
  ];

  return (
    <>
      <PageHeader title="Dashboard" description="Workspace overview: knowledge base health and support load." />
      {loading && <LoadingState />}
      {!loading && error && <ErrorState message={error} onRetry={() => setReloadKey((k) => k + 1)} />}
      {!loading && !error && (
        <div className="stat-grid">
          {stats.map((s) => (
            <Link key={s.label} href={s.href} className="card stat">
              <span className="stat-value">{s.value}</span>
              <span className="stat-label">{s.label}</span>
            </Link>
          ))}
        </div>
      )}
    </>
  );
}
