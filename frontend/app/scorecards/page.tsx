"use client";

import { useMemo } from "react";
import { api, type Scorecard } from "@/lib/api";
import { useApi, fmtTime } from "@/lib/hooks";
import {
  Card, EmptyNote, ErrorNote, LoadingNote, PassBadge, SeverityBadge, StatCard,
} from "@/components/ui";
import { TaxonomyBar, countFailureTypes } from "@/components/charts";

export default function ScorecardsPage() {
  const state = useApi<Scorecard[]>(api.listScorecards);

  const rows = state.status === "ready"
    ? [...state.data].sort((a, b) => b.analyzed_at.localeCompare(a.analyzed_at))
    : [];

  const agg = useMemo(() => {
    if (state.status !== "ready") return null;
    return {
      passed: rows.filter((r) => r.passed).length,
      failed: rows.filter((r) => !r.passed).length,
      avg: Math.round(rows.reduce((a, r) => a + r.score, 0) / Math.max(1, rows.length)),
      failures: countFailureTypes(rows.map((r) => r.failure_types ?? [])),
    };
  }, [state, rows]);

  return (
    <>
      <div className="page-header">
        <h1 className="page-title">Scorecards</h1>
        <div className="page-sub">
          Point-in-time reliability scorecards aggregated by the Scorecard Service
          — live via Kong.
        </div>
      </div>

      {state.status === "loading" && <LoadingNote />}
      {state.status === "error" && <ErrorNote message={state.error.message} />}
      {state.status === "empty" && (
        <EmptyNote>No scorecards yet — run an evaluation and let the pipeline
        analyze it.</EmptyNote>
      )}

      {agg && (
        <>
          <div className="grid grid-stats">
            <StatCard value={agg.avg} label="Mean score" />
            <StatCard value={rows.length} label="Scorecards" />
            <StatCard value={<span style={{ color: "var(--green)" }}>{agg.passed}</span>}
                      label="Passed" accent="#34d399" />
            <StatCard value={<span style={{ color: "var(--red)" }}>{agg.failed}</span>}
                      label="Failed" accent="#f87171" />
          </div>

          <div className="grid grid-half">
            <Card title="Failure taxonomy breakdown">
              <TaxonomyBar counts={agg.failures} />
            </Card>
            <Card title="Pass / fail breakdown">
              <div style={{ display: "flex", height: 14, borderRadius: 7, overflow: "hidden", gap: 2 }}>
                {agg.passed > 0 && (
                  <div style={{ width: `${(agg.passed / rows.length) * 100}%`,
                                background: "var(--green)" }} />
                )}
                {agg.failed > 0 && (
                  <div style={{ width: `${(agg.failed / rows.length) * 100}%`,
                                background: "var(--red)" }} />
                )}
              </div>
              <div className="pill-row" style={{ marginTop: 12 }}>
                <span className="badge badge-pass">passed {agg.passed}</span>
                <span className="badge badge-fail">failed {agg.failed}</span>
                <span className="badge badge-neutral">
                  pass rate {Math.round((agg.passed / rows.length) * 100)}%
                </span>
              </div>
            </Card>
          </div>

          <Card title={`All scorecards (${rows.length})`}>
            <div className="table-wrap">
              <table className="tbl">
                <thead>
                  <tr><th>Run</th><th>Agent</th><th>Scenario</th><th>Status</th>
                      <th>Score</th><th>Severity</th><th>Failure types</th><th>Analyzed</th></tr>
                </thead>
                <tbody>
                  {rows.map((s) => (
                    <tr key={s.id}>
                      <td className="mono">{s.run_id}</td>
                      <td>{s.agent_name ?? "—"}</td>
                      <td className="mono dim">#{s.scenario_ref ?? "—"}</td>
                      <td><PassBadge passed={s.passed} /></td>
                      <td className="mono">{s.score}</td>
                      <td><SeverityBadge severity={s.severity} /></td>
                      <td>
                        {(s.failure_types ?? []).length === 0
                          ? <span className="dimmer">—</span>
                          : <span className="mono dim">{s.failure_types.join(", ")}</span>}
                      </td>
                      <td className="dim">{fmtTime(s.analyzed_at)}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </Card>
        </>
      )}
    </>
  );
}
