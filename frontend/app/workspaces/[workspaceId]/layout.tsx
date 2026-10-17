import type { ReactNode } from "react";
import { RequireAuth } from "@/components/RequireAuth";
import { Sidebar } from "@/components/Sidebar";
import { WorkspaceGate, WorkspaceProvider } from "@/components/WorkspaceProvider";

type WorkspaceLayoutProps = {
  children: ReactNode;
  params: Promise<{ workspaceId: string }>;
};

// Shared shell for every page under /workspaces/[workspaceId]/...
// Logged in? → membership confirmed (role known)? → render the page.
export default async function WorkspaceLayout({ children, params }: WorkspaceLayoutProps) {
  const { workspaceId } = await params;
  return (
    <RequireAuth>
      <WorkspaceProvider workspaceId={workspaceId}>
        <div className="shell">
          <Sidebar workspaceId={workspaceId} />
          <main className="content">
            <WorkspaceGate>{children}</WorkspaceGate>
          </main>
        </div>
      </WorkspaceProvider>
    </RequireAuth>
  );
}
