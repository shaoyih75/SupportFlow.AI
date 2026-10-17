// Where the access token lives in the browser.
// Class demo: localStorage (simple, but readable by any script on the page).
// Production apps usually keep it in a Secure, HttpOnly, SameSite cookie instead
// (JavaScript can't read it), which then also needs CSRF protection.

const TOKEN_KEY = "supportflow.access_token";

export function getAccessToken(): string | null {
  try {
    return window.localStorage.getItem(TOKEN_KEY);
  } catch {
    return null;
  }
}

export function setAccessToken(token: string) {
  window.localStorage.setItem(TOKEN_KEY, token);
}

export function clearAccessToken() {
  try {
    window.localStorage.removeItem(TOKEN_KEY);
  } catch {
    // storage unavailable: nothing to clear
  }
}

export function redirectToLogin() {
  if (window.location.pathname === "/login") return;
  const next = window.location.pathname + window.location.search;
  window.location.assign(`/login?next=${encodeURIComponent(next)}`);
}

// Only allow same-site paths after login, never "//evil.com" or "https://…" (open redirect).
export function safeNextPath(next: string | null): string {
  return next && next.startsWith("/") && !next.startsWith("//") ? next : "/workspaces";
}
