"use client";

import { api } from "@/lib/api";
import { useApi, fmtTime } from "@/lib/hooks";
import {
  Badge, Card, EmptyNote, ErrorNote, LoadingNote,
  PassBadge, SeverityBadge, StatCard, StatusDelta,
} from "@/components/ui";
import { liveToSeries } from "@/components/charts";
import type { DemoRegressionSeries } from "@/lib/demo";
import { TrendChart } from "@/components/charts";

const STATUS_TONE = {
  baseline: "baseline",
  improved: "improved",
  regressed: "regressed",
  unchanged: "unchanged",
} as const;

export default function RegressionsPage() {
  const state = useApi(api.listRegressions);
  const rows = state.status === "ready"
    ? [...state.data].sort((a, b) => b.analyzed_at.localeCompare(a.analyzed_at))
    : [];

  if (state.status === "loading") return <LoadingNote />;
  if (state.status === "error") return (
    <>
      <div className="page-header">
        <h1 className="page-title">Regressions</h1>
      </div>
      <ErrorNote message={state.error.message} />
    </>
  );
  if (state.status === "empty") return (
    <>
      <div className="page-header">
        <h1 className="page-title">Regressions</h1>
        <div className="page-sub">Score movement across agent versions — live via Kong.</div>
      </div>
      <EmptyNote>No regression history yet.</EmptyNote>
    </>
  );

  const regressedCount = rows.filter((r) => r.regression_status === "regressed").length;
  const improvedCount = rows.filter((r) => r.regression_status === "improved").length;
  const series: DemoRegressionSeries[] = liveToSeries(rows);

  return (
    <>
      <div className="page-header">
        <h1 className="page-title">Regressions</h1>
        <div className="page-sub">
          Score movement across agent versions and commits — live via Kong.
        </div>
      </div>

      <div className="grid grid-stats">
        <StatCard value={rows.length} label="Tracked results" />
        <StatCard value={<span style={{ color: "var(--red)" }}>{regressedCount}</span>}
                  label="Regressions" accent="#f87171" />
        <StatCard value={<span style={{ color: "var(--green)" }}>{improvedCount}</span>}
                  label="Improvements" accent="#34d399" />
        <StatCard value={series.length} label="Agents tracked" />
      </div>

      {series.map((s) => {
        const agentRows = rows
          .filter((r) => (r.agent_name ?? "") === s.agent)
          .sort((a, b) => b.analyzed_at.localeCompare(a.analyzed_at));
        const failureDeltaAgg: Record<string, number> = {};
        for (const p of agentRows)
          for (const [k, v] of Object.entries(p.failure_delta ?? {}))
            failureDeltaAgg[k] = (failureDeltaAgg[k] ?? 0) + v;

        return (
          <Card key={s.agent}
                title={`Trend — ${s.agent}`}
                right={<Badge tone="neutral">{s.points[s.points.length - 1]?.version ?? "—"}</Badge>}>
            {s.points.length >= 2 ? (
              <TrendChart series={s} />
            ) : (
              <EmptyNotEnough />
            )}

            <div style={{ display: "grid", gap: 14, gridTemplateColumns: "minmax(0,3fr) minmax(0,2fr)", marginTop: 10 }}>
              <div className="table-wrap">
                <table className="tbl">
                  <thead>
                    <tr><th>Run</th><th>Version</th><th>Commit</th><th>Status</th>
                        <th>Score</th><th>Δ</th><th>Pass</th><th>Severity</th><th>When</th></tr>
                  </thead>
                  <tbody>
                    {agentRows.map((r) => (
                      <tr key={r.id}>
                        <td className="mono">{r.run_id}</td>
                        <td className="mono">{r.agent_version ?? "—"}</td>
                        <td className="mono dimmer">{r.git_commit ?? "—"}</td>
                        <td><Badge tone={STATUS_TONE[r.regression_status]}>{r.regression_status}</Badge></td>
                        <td className="mono">
                          {r.previous_score !== null && (
                            <span className="dimmer">{r.previous_score} → </span>
                          )}
                          <b>{r.score}</b>
                        </td>
                        <td><StatusDelta delta={r.score_delta} /></td>
                        <td><PassBadge passed={r.passed} /></td>
                        <td><SeverityBadge severity={r.severity} /></td>
                        <td className="dim">{fmtTime(r.analyzed_at)}</td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>

              <div>
                <div className="card-title" style={{ margin: "4px 0 12px" }}>
                  Net failure-type change
                </div>
                <NetFailureDeltas deltas={failureDeltaAgg} />
              </div>
            </div>
          </Card>
        );
      })}
    </>
  );
}

function EmptyNotEnough() {
  return (
    <EmptyNote>
      One data point so far — trend chart appears from the second evaluation.
    </EmptyNote>
  );
}

function NetFailureDeltas({ deltas }: { deltas: Record<string, number> }) {
  const entries = Object.entries(deltas).filter(([, v]) => v !== 0);
  if (!entries.length)
    return <EmptyNote>No net failure-type changes tracked yet.</EmptyNote>;
  return (
    <div className="pill-row">
      {entries.map(([k, v]) => (
        <span key={k} className="badge badge-neutral">
          {k.replace(/_/g, " ")}{" "}
          <span className={v > 0 ? "delta-neg" : "delta-pos"}>
            {v > 0 ? `+${v}` : v}
          </span>
        </span>
      ))}
    </div>
  );
}
