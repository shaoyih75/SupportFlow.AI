"use client";

import { useRef, useState } from "react";
import { describeError, MAX_UPLOAD_BYTES, UPLOAD_ACCEPT, uploadContentType, uploadDocument, type UploadStep } from "@/lib/api";
import { formatBytes } from "./DocumentCard";

const STEP_LABELS: Record<UploadStep, string> = {
  init: "1/3 Asking the API for an upload link…",
  upload: "2/3 Uploading to S3",
  verify: "3/3 Server is verifying the file in S3…",
};

type DocumentUploadProps = {
  workspaceId: string;
  onUploaded: () => void;
};

export function DocumentUpload({ workspaceId, onUploaded }: DocumentUploadProps) {
  const inputRef = useRef<HTMLInputElement>(null);
  const [file, setFile] = useState<File | null>(null);
  const [step, setStep] = useState<UploadStep | null>(null);
  const [percent, setPercent] = useState(0);
  const [error, setError] = useState<string | null>(null);
  const uploading = step !== null;

  function choose(selected: File | null) {
    setError(null);
    setFile(selected);
    // Fail fast on the obvious problems; the server checks again anyway.
    if (selected && !uploadContentType(selected.name)) setError("Only PDF, TXT and Markdown (.md) files are supported");
    else if (selected && selected.size > MAX_UPLOAD_BYTES) setError("Files must be 10 MB or smaller");
  }

  async function handleUpload() {
    if (!file || error) return;
    try {
      await uploadDocument(workspaceId, file, (nextStep, nextPercent) => {
        setStep(nextStep);
        setPercent(nextPercent);
      });
      setFile(null);
      if (inputRef.current) inputRef.current.value = "";
      onUploaded();
    } catch (err) {
      setError(describeError(err));
    } finally {
      setStep(null);
      setPercent(0);
    }
  }

  return (
    <section className="card upload" aria-label="Upload a document">
      <div className="upload-row">
        <input
          ref={inputRef}
          type="file"
          accept={UPLOAD_ACCEPT}
          disabled={uploading}
          onChange={(e) => choose(e.target.files?.[0] ?? null)}
          aria-label="Choose a file"
        />
        <button className="button button-primary" onClick={handleUpload} disabled={!file || !!error || uploading}>
          {uploading ? "Uploading…" : "Upload"}
        </button>
      </div>
      <p className="muted">PDF, TXT or Markdown, up to 10 MB.{file && ` Selected: ${file.name} (${formatBytes(file.size)})`}</p>

      {step && (
        <div className="upload-progress" role="status">
          <span>
            {STEP_LABELS[step]}
            {step === "upload" && ` ${percent}%`}
          </span>
          <progress max={100} value={step === "init" ? 0 : percent} />
        </div>
      )}
      {error && <p className="field-error">{error}</p>}
    </section>
  );
}
