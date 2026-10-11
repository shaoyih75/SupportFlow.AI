import type { ReactNode } from "react";

// The three non-success UI states every async page needs.
// loading ≠ empty ≠ error: each means something different to the user.

export function LoadingState({ label = "Loading…" }: { label?: string }) {
  return (
    <div className="state state-loading" role="status">
      <span className="spinner" aria-hidden /> {label}
    </div>
  );
}

type EmptyStateProps = {
  title: string;
  hint?: string;
  action?: ReactNode;
};

export function EmptyState({ title, hint, action }: EmptyStateProps) {
  return (
    <div className="state">
      <strong>{title}</strong>
      {hint && <p>{hint}</p>}
      {action}
    </div>
  );
}

type ErrorStateProps = {
  message: string;
  requestId?: string | null;
  onRetry?: () => void;
};

export function ErrorState({ message, requestId, onRetry }: ErrorStateProps) {
  return (
    <div className="state state-error" role="alert">
      <strong>{message}</strong>
      {requestId && <p className="request-id">Request ID: {requestId}</p>}
      {onRetry && (
        <button className="button" onClick={onRetry}>
          Retry
        </button>
      )}
    </div>
  );
}
