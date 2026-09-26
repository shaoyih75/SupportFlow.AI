import { redirect } from "next/navigation";

// No auth yet: send everyone to the default mock workspace.
export default function Home() {
  redirect("/workspaces/ws-acme");
}
