import type { DocumentStatus, SourceType } from "@/lib/types";
import { StatusBadge } from "./StatusBadge";

type DocumentCardProps = {
  title: string;
  sourceType: SourceType;
  status: DocumentStatus;
  updatedAt: string;
};

export function DocumentCard({ title, sourceType, status, updatedAt }: DocumentCardProps) {
  return (
    <article className="card">
      <div className="card-top">
        <span className="source-tag">{sourceType}</span>
        <StatusBadge status={status} />
      </div>
      <h3>{title}</h3>
      <p className="card-meta">Updated {new Date(updatedAt).toLocaleDateString()}</p>
    </article>
  );
}
