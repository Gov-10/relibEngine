"use client";

import { taxonomyMeta, type DemoRegressionSeries } from "@/lib/demo";
import type { RegressionResult } from "@/lib/api";

/** Hand-rolled SVG line chart of reliability scores across versions. */
export function TrendChart({ series }: { series: DemoRegressionSeries }) {
  const pts = series.points;
  if (pts.length < 1) return null;
  const W = 640;
  const H = 190;
  const padX = 42;
  const padY = 18;
  const scores = pts.map((p) => p.score);
  const min = Math.min(...scores) - 8;
  const max = Math.max(...scores) + 8;
  const span = Math.max(10, max - min);
  const x = (i: number) =>
    padX + (i * (W - padX - 16)) / Math.max(1, pts.length - 1);
  const y = (s: number) => padY + (H - padY * 2) * (1 - (s - min) / span);

  const path = pts.map((p, i) => `${i === 0 ? "M" : "L"}${x(i)},${y(p.score)}`).join(" ");
  const area = `${path} L${x(pts.length - 1)},${H - padY} L${x(0)},${H - padY} Z`;

  return (
    <svg viewBox={`0 0 ${W} ${H}`} style={{ width: "100%", height: "auto" }}>
      <defs>
        <linearGradient id="trendFill" x1="0" y1="0" x2="0" y2="1">
          <stop offset="0%" stopColor="#5b8cff" stopOpacity="0.28" />
          <stop offset="100%" stopColor="#5b8cff" stopOpacity="0" />
        </linearGradient>
      </defs>
      {[40, 60, 80].map((g) =>
        g > min && g < max ? (
          <line key={g} x1={padX} x2={W - 16} y1={y(g)} y2={y(g)}
                stroke="#232d44" strokeDasharray="3 5" strokeWidth="1" />
        ) : null
      )}
      <path d={area} fill="url(#trendFill)" />
      <path d={path} fill="none" stroke="#5b8cff" strokeWidth="2.2" />
      {pts.map((p, i) => (
        <g key={p.run_id}>
          <circle cx={x(i)} cy={y(p.score)} r="4.6"
                  fill={p.status === "regressed" ? "#f87171" : p.passed ? "#34d399" : "#fbbf24"}
                  stroke="#101623" strokeWidth="2" />
          <text x={x(i)} y={y(p.score) - 11} textAnchor="middle"
                fill="#9aa7bd" fontSize="10.5">{p.score}</text>
          <text x={x(i)} y={H - 3} textAnchor="middle"
                fill="#64718a" fontSize="10" fontFamily="monospace">{p.version}</text>
        </g>
      ))}
    </svg>
  );
}

/** Horizontal failure-taxonomy distribution bar (live aggregate or demo). */
export function TaxonomyBar({ counts }: { counts: Record<string, number> }) {
  const entries = Object.entries(counts).filter(([, n]) => n > 0);
  const total = entries.reduce((a, [, n]) => a + n, 0);
  if (!total) return <div className="empty-note">No failures recorded.</div>;
  return (
    <div>
      <div style={{ display: "flex", height: 14, borderRadius: 7, overflow: "hidden", gap: 2 }}>
        {entries.map(([k, n]) => (
          <div key={k}
               title={`${taxonomyMeta(k).label}: ${n}`}
               style={{ width: `${(n / total) * 100}%`, background: taxonomyMeta(k).color }} />
        ))}
      </div>
      <div className="pill-row" style={{ marginTop: 12 }}>
        {entries
          .sort((a, b) => b[1] - a[1])
          .map(([k, n]) => (
            <span key={k} className="badge badge-neutral">
              <span style={{ width: 8, height: 8, borderRadius: "50%",
                             background: taxonomyMeta(k).color, display: "inline-block" }} />
              {taxonomyMeta(k).label}&nbsp;<b>{n}</b>
            </span>
          ))}
      </div>
    </div>
  );
}

export function liveToSeries(rows: RegressionResult[]): DemoRegressionSeries[] {
  const byAgent = new Map<string, RegressionResult[]>();
  for (const r of rows) {
    const key = r.agent_name ?? "unknown";
    byAgent.set(key, [...(byAgent.get(key) ?? []), r]);
  }
  return [...byAgent.entries()].map(([agent, rows]) => ({
    agent,
    // oldest first for left-to-right chronology
    points: [...rows]
      .sort((a, b) => a.analyzed_at.localeCompare(b.analyzed_at))
      .map((r) => ({
        version: r.agent_version ?? "—",
        commit: r.git_commit,
        run_id: r.run_id,
        score: r.score,
        passed: r.passed,
        status: r.regression_status,
        analyzed_at: r.analyzed_at,
      })),
  }));
}

export function countFailureTypes(scorecardFailureTypes: string[][]): Record<string, number> {
  const out: Record<string, number> = {};
  for (const types of scorecardFailureTypes)
    for (const t of types) out[t] = (out[t] ?? 0) + 1;
  return out;
}
