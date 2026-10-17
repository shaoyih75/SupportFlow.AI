"use client";

import Link from "next/link";
import { usePathname, useRouter } from "next/navigation";
import { useEffect, useState } from "react";
import { getMe, getWorkspaces } from "@/lib/api";
import { clearAccessToken } from "@/lib/auth";
import type { User, Workspace } from "@/lib/types";
import { StatusBadge } from "./StatusBadge";
import { useWorkspace } from "./WorkspaceProvider";

type SidebarProps = {
  workspaceId: string;
};

const NAV_ITEMS = [
  { segment: "", label: "Dashboard" },
  { segment: "/documents", label: "Documents" },
  { segment: "/tickets", label: "Tickets" },
  { segment: "/assistant", label: "AI Assistant" },
];

export function Sidebar({ workspaceId }: SidebarProps) {
  const pathname = usePathname();
  const router = useRouter();
  const { role } = useWorkspace();
  const [workspaces, setWorkspaces] = useState<Workspace[]>([]);
  const [me, setMe] = useState<User | null>(null);
  const [apiOffline, setApiOffline] = useState(false);

  useEffect(() => {
    // Only workspaces where the current user has an ACTIVE membership come back.
    getWorkspaces()
      .then(setWorkspaces)
      .catch(() => setApiOffline(true));
    getMe()
      .then(setMe)
      .catch(() => setMe(null));
  }, []);

  function logout() {
    clearAccessToken();
    router.replace("/login");
  }

  const base = `/workspaces/${workspaceId}`;
  // Keep the user on the same section when switching workspace.
  const section = pathname.slice(base.length);
  const inList = workspaces.some((w) => w.id === workspaceId);

  return (
    <aside className="sidebar">
      <div className="brand">
        <span className="brand-mark">S</span> SupportFlow<span className="brand-ai">.AI</span>
      </div>

      <label className="field-label" htmlFor="workspace-select">
        Workspace
      </label>
      <select
        id="workspace-select"
        className="select"
        value={workspaceId}
        onChange={(e) => router.push(`/workspaces/${e.target.value}${section}`)}
      >
        {!inList && <option value={workspaceId}>{workspaces.length ? "No access" : "Loading…"}</option>}
        {workspaces.map((w) => (
          <option key={w.id} value={w.id}>
            {w.name}
          </option>
        ))}
      </select>
      {role && (
        <p className="sidebar-role">
          Your role <StatusBadge status={role} />
        </p>
      )}

      <nav className="nav">
        {NAV_ITEMS.map((item) => {
          const href = base + item.segment;
          const active = pathname === href;
          return (
            <Link key={item.label} href={href} className={active ? "nav-link active" : "nav-link"}>
              {item.label}
            </Link>
          );
        })}
      </nav>

      <div className="sidebar-user">
        {me && (
          <p>
            <strong>{me.name}</strong>
            <span className="muted">{me.email}</span>
          </p>
        )}
        <button className="button" onClick={logout}>
          Log out
        </button>
        <p className="sidebar-foot">
          {apiOffline ? "⚠ API offline: start FastAPI on :8000" : "Tickets: FastAPI · Documents: mock"}
        </p>
      </div>
    </aside>
  );
}
