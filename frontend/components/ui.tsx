import type { ReactNode } from "react";

export function Card({
  title,
  right,
  children,
}: {
  title?: string;
  right?: ReactNode;
  children: ReactNode;
}) {
  return (
    <div className="card">
      {title && (
        <div className="card-title">
          <span>{title}</span>
          {right}
        </div>
      )}
      {children}
    </div>
  );
}

export type BadgeTone =
  | "pass" | "fail" | "low" | "medium" | "high" | "critical"
  | "baseline" | "improved" | "regressed" | "unchanged" | "neutral" | "demo";

export function Badge({ tone, children }: { tone: BadgeTone; children: ReactNode }) {
  return <span className={`badge badge-${tone}`}>{children}</span>;
}

export function PassBadge({ passed }: { passed: boolean }) {
  return <Badge tone={passed ? "pass" : "fail"}>{passed ? "PASS" : "FAIL"}</Badge>;
}

export function SeverityBadge({ severity }: { severity: string }) {
  const tone = ["low", "medium", "high", "critical"].includes(severity)
    ? (severity as BadgeTone)
    : "neutral";
  return <Badge tone={tone}>{severity.toUpperCase()}</Badge>;
}

export function StatusDelta({ delta }: { delta: number | null }) {
  if (delta === null || delta === undefined)
    return <span className="dimmer">—</span>;
  const cls = delta > 0 ? "delta-pos" : delta < 0 ? "delta-neg" : "delta-zero";
  const sign = delta > 0 ? "+" : "";
  return (
    <span className={cls}>
      {sign}{delta}
    </span>
  );
}

export function StatCard({
  value,
  label,
  foot,
  accent,
}: {
  value: ReactNode;
  label: string;
  foot?: ReactNode;
  accent?: string;
}) {
  return (
    <div className="card" style={accent ? { borderTop: `2px solid ${accent}` } : undefined}>
      <div className="stat-value" style={accent ? { color: accent } : undefined}>
        {value}
      </div>
      <div className="stat-label">{label}</div>
      {foot && <div className="stat-foot">{foot}</div>}
    </div>
  );
}

export function ScoreRing({ score }: { score: number }) {
  const r = 38;
  const c = 2 * Math.PI * r;
  const pct = Math.max(0, Math.min(100, score));
  const color = pct >= 80 ? "#34d399" : pct >= 55 ? "#fbbf24" : "#f87171";
  return (
    <div className="score-ring">
      <svg width="92" height="92" viewBox="0 0 92 92">
        <circle cx="46" cy="46" r={r} stroke="#1d2740" strokeWidth="8" fill="none" />
        <circle
          cx="46" cy="46" r={r}
          stroke={color} strokeWidth="8" fill="none"
          strokeLinecap="round"
          strokeDasharray={`${(pct / 100) * c} ${c}`}
        />
      </svg>
      <div className="score-ring-num" style={{ color }}>
        {Math.round(pct)}
      </div>
    </div>
  );
}

export function LoadingNote({ label = "Loading…" }: { label?: string }) {
  return <div className="loading-note">{label}</div>;
}

export function ErrorNote({ message }: { message: string }) {
  return <div className="error-note">API error — {message}</div>;
}

export function EmptyNote({ children }: { children: ReactNode }) {
  return <div className="empty-note">{children}</div>;
}

export function DemoTag() {
  return (
    <Badge tone="demo" >
      <span title="Rendered from isolated demo data — this view has no gateway route by design.">
        DEMO DATA
      </span>
    </Badge>
  );
}
