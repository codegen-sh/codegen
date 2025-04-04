import type { Metadata } from "next"
import RepoChatDashboard from "@/components/repo-chat-dashboard"

export const metadata: Metadata = {
  title: "Deep Research",
  description: "Chat with your codebase"
}

export default function Page() {
  return <RepoChatDashboard />
}

