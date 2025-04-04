import "@/styles/globals.css"
import type { Metadata } from "next"
import type React from "react" // Import React

import { ThemeProvider } from "@/components/theme-provider"

export const metadata: Metadata = {
  title: "Codebase Analytics Dashboard",
  description: "Analytics dashboard for public GitHub repositories",
}

export default function RootLayout({
  children,
}: {
  children: React.ReactNode
}) {
  return (
    <html lang="en" suppressHydrationWarning>
      <body>
        <ThemeProvider attribute="class" defaultTheme="dark" enableSystem disableTransitionOnChange>
          {children}
        </ThemeProvider>
      </body>
    </html>
  )
}



import './globals.css'