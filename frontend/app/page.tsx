import { redirect } from "next/navigation";
import { DEFAULT_WORKSPACE_ID } from "@/lib/config";

// No auth yet: send everyone to the seeded default workspace.
export default function Home() {
  redirect(`/workspaces/${DEFAULT_WORKSPACE_ID}`);
}
