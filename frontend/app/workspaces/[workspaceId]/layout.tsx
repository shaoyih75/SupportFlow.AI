import type { ReactNode } from "react";
import { Sidebar } from "@/components/Sidebar";

type WorkspaceLayoutProps = {
  children: ReactNode;
  params: Promise<{ workspaceId: string }>;
};

// Shared shell for every page under /workspaces/[workspaceId]/...
export default async function WorkspaceLayout({ children, params }: WorkspaceLayoutProps) {
  const { workspaceId } = await params;
  return (
    <div className="shell">
      <Sidebar workspaceId={workspaceId} />
      <main className="content">{children}</main>
    </div>
  );
}
