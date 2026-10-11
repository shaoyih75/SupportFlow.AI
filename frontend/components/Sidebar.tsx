"use client";

import Link from "next/link";
import { usePathname, useRouter } from "next/navigation";
import { useEffect, useState } from "react";
import { getWorkspaces } from "@/lib/api";
import type { Workspace } from "@/lib/types";

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
  const [workspaces, setWorkspaces] = useState<Workspace[]>([]);
  const [apiOffline, setApiOffline] = useState(false);

  useEffect(() => {
    getWorkspaces()
      .then(setWorkspaces)
      .catch(() => setApiOffline(true));
  }, []);

  const base = `/workspaces/${workspaceId}`;
  // Keep the user on the same section when switching workspace.
  const section = pathname.slice(base.length);

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
        {workspaces.length === 0 && <option value={workspaceId}>{workspaceId}</option>}
        {workspaces.map((w) => (
          <option key={w.id} value={w.id}>
            {w.name}
          </option>
        ))}
      </select>

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

      <p className="sidebar-foot">
        {apiOffline ? "⚠ API offline: start FastAPI on :8000" : "Tickets: FastAPI · Documents: mock"}
      </p>
    </aside>
  );
}
