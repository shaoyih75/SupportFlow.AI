import type { Document } from "@/lib/types";
import { StatusBadge } from "./StatusBadge";

type DocumentCardProps = {
  document: Document;
  onDownload?: () => void; // only offered once the file is verified in S3
};

export function formatBytes(bytes: number): string {
  if (bytes < 1024) return `${bytes} B`;
  if (bytes < 1024 * 1024) return `${(bytes / 1024).toFixed(1)} KB`;
  return `${(bytes / 1024 / 1024).toFixed(1)} MB`;
}

export function DocumentCard({ document, onDownload }: DocumentCardProps) {
  const kind = document.filename.split(".").pop()?.toUpperCase() ?? "FILE";
  return (
    <article className="card">
      <div className="card-top">
        <span className="source-tag">{kind}</span>
        <StatusBadge status={document.status} />
      </div>
      <h3 className="document-name">{document.filename}</h3>
      <p className="card-meta">
        {formatBytes(document.sizeBytes)} · {new Date(document.createdAt).toLocaleDateString()}
      </p>
      {document.status === "UPLOADED" && onDownload && (
        <button className="button" onClick={onDownload}>
          Download
        </button>
      )}
    </article>
  );
}
