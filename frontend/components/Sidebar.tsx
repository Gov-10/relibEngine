"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";
import { API_BASE_URL } from "@/lib/api";

const NAV = [
  {
    section: "Monitoring",
    links: [
      { href: "/", label: "Overview", icon: "▦" },
      { href: "/evaluations", label: "Evaluations", icon: "◈" },
      { href: "/traces", label: "Trace Explorer", icon: "⌁" },
    ],
  },
  {
    section: "Reliability",
    links: [
      { href: "/scorecards", label: "Scorecards", icon: "▤" },
      { href: "/regressions", label: "Regressions", icon: "↯" },
    ],
  },
  {
    section: "Actions",
    links: [{ href: "/run", label: "Run Evaluation", icon: "▶" }],
  },
];

export function Sidebar() {
  const pathname = usePathname();
  return (
    <aside className="sidebar">
      <div className="brand">
        <div className="brand-mark">R</div>
        <div>
          <div className="brand-name">Relib Engine</div>
          <div className="brand-sub">Agent Reliability</div>
        </div>
      </div>

      {NAV.map((group) => (
        <div key={group.section}>
          <div className="nav-section">{group.section}</div>
          {group.links.map((l) => (
            <Link
              key={l.href}
              href={l.href}
              className={`nav-link${pathname === l.href ? " active" : ""}`}
            >
              <span className="nav-icon">{l.icon}</span>
              {l.label}
            </Link>
          ))}
        </div>
      ))}

      <div className="sidebar-footer">
        <span className="gateway-dot" />
        via Kong Gateway
        <div style={{ marginTop: 3, fontFamily: "var(--mono)", fontSize: 10.5 }}>
          {API_BASE_URL.replace(/^https?:\/\//, "")}
        </div>
      </div>
    </aside>
  );
}
