"use client";

import { useEffect, useState, type ReactNode } from "react";
import { getAccessToken, redirectToLogin } from "@/lib/auth";
import { LoadingState } from "./AsyncStates";

// UX only: skips a flash of protected pages for logged-out users.
// The real protection is the backend returning 401 without a valid token.
export function RequireAuth({ children }: { children: ReactNode }) {
  const [hasToken, setHasToken] = useState<boolean | null>(null);

  useEffect(() => {
    const token = getAccessToken();
    setHasToken(Boolean(token));
    if (!token) redirectToLogin();
  }, []);

  if (!hasToken) return <LoadingState label="Checking your session…" />;
  return <>{children}</>;
}
