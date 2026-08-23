import type { Metadata } from "next";
import "./globals.css";
import { Sidebar } from "@/components/Sidebar";

export const metadata: Metadata = {
  title: "Relib Engine — Agent Reliability Dashboard",
  description:
    "CI/CD pipeline for autonomous AI agents: adversarial scenario generation, sandboxed execution, failure analysis, and regression tracking.",
};

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="en">
      <body>
        <div className="shell">
          <Sidebar />
          <main className="main">{children}</main>
        </div>
      </body>
    </html>
  );
}
