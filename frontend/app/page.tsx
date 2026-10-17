import { redirect } from "next/navigation";

// /workspaces lists the workspaces of the logged-in user (and sends logged-out users to /login).
export default function Home() {
  redirect("/workspaces");
}
