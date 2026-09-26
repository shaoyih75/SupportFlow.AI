// The three non-success UI states every async page needs.
// loading ≠ empty ≠ error: each means something different to the user.

export function LoadingState({ label = "Loading…" }: { label?: string }) {
  return (
    <div className="state state-loading" role="status">
      <span className="spinner" aria-hidden /> {label}
    </div>
  );
}

export function EmptyState({ title, hint }: { title: string; hint?: string }) {
  return (
    <div className="state">
      <strong>{title}</strong>
      {hint && <p>{hint}</p>}
    </div>
  );
}

export function ErrorState({ message, onRetry }: { message: string; onRetry: () => void }) {
  return (
    <div className="state state-error" role="alert">
      <strong>{message}</strong>
      <button className="button" onClick={onRetry}>
        Retry
      </button>
    </div>
  );
}
