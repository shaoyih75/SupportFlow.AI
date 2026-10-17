"use client";

import Link from "next/link";
import { useRouter } from "next/navigation";
import { useState, type FormEvent } from "react";
import { ApiError, login } from "@/lib/api";
import { safeNextPath, setAccessToken } from "@/lib/auth";

const DEMO_ACCOUNTS = [
  { email: "alice@example.com", note: "OWNER of Acme Support" },
  { email: "bob@example.com", note: "MEMBER of Acme, OWNER of his own workspace" },
  { email: "carol@example.com", note: "VIEWER of Acme (read-only)" },
];

export default function LoginPage() {
  const router = useRouter();
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [submitting, setSubmitting] = useState(false);
  const [error, setError] = useState<string | null>(null);

  async function handleSubmit(e: FormEvent<HTMLFormElement>) {
    e.preventDefault();
    setSubmitting(true);
    setError(null);
    try {
      const token = await login(email, password);
      setAccessToken(token);
      const next = new URLSearchParams(window.location.search).get("next");
      router.replace(safeNextPath(next));
    } catch (err) {
      if (err instanceof ApiError && err.status === 401) setError("Invalid email or password");
      else if (err instanceof ApiError && err.status === 422) setError("Enter a valid email address");
      else setError(err instanceof Error ? err.message : "Login failed");
    } finally {
      setSubmitting(false);
    }
  }

  return (
    <main className="login">
      <form className="card login-card" onSubmit={handleSubmit}>
        <div className="brand">
          <span className="brand-mark">S</span> SupportFlow<span className="brand-ai">.AI</span>
        </div>
        <h1>Log in</h1>

        <div className="form-field">
          <label className="field-label" htmlFor="email">
            Email
          </label>
          <input
            id="email"
            className="input"
            type="email"
            autoComplete="username"
            value={email}
            onChange={(e) => setEmail(e.target.value)}
            required
          />
        </div>
        <div className="form-field">
          <label className="field-label" htmlFor="password">
            Password
          </label>
          <input
            id="password"
            className="input"
            type="password"
            autoComplete="current-password"
            value={password}
            onChange={(e) => setPassword(e.target.value)}
            required
          />
        </div>
        {error && <p className="field-error">{error}</p>}
        <button className="button button-primary" type="submit" disabled={submitting}>
          {submitting ? "Logging in…" : "Log in"}
        </button>
        <p className="muted auth-switch">
          New here? <Link href="/register">Create an account</Link>
        </p>

        <div className="demo-accounts">
          <p className="field-label">Demo accounts · password: password123</p>
          {DEMO_ACCOUNTS.map((a) => (
            <button
              key={a.email}
              type="button"
              className="demo-account"
              onClick={() => {
                setEmail(a.email);
                setPassword("password123");
              }}
            >
              <strong>{a.email}</strong>
              <span className="muted">{a.note}</span>
            </button>
          ))}
        </div>
      </form>
    </main>
  );
}
