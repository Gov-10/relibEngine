"use client";

import { useMemo } from "react";
import Link from "next/link";
import { api, type RegressionResult, type Scorecard } from "@/lib/api";
import { useApi, fmtTime } from "@/lib/hooks";
import {
  Badge, Card, EmptyNote, ErrorNote, LoadingNote,
  PassBadge, ScoreRing, SeverityBadge, StatCard,
} from "@/components/ui";
import { TaxonomyBar, countFailureTypes } from "@/components/charts";

export default function OverviewPage() {
  const scorecards = useApi<Scorecard[]>(api.listScorecards);
  const regressions = useApi<RegressionResult[]>(api.listRegressions);

  const stats = useMemo(() => {
    if (scorecards.status !== "ready") return null;
    const rows = scorecards.data;
    const latestByRun = new Map<string, Scorecard>();
    for (const s of rows) latestByRun.set(s.run_id, s);
    const runs = [...latestByRun.values()];
    const avg =
      runs.reduce((a, s) => a + s.score, 0) / Math.max(1, runs.length);
    return {
      avgScore: Math.round(avg),
      totalEvaluations: rows.length,
      totalRuns: runs.length,
      passed: runs.filter((s) => s.passed).length,
      failed: runs.filter((s) => !s.passed).length,
      critical: rows.filter(
        (s) => !s.passed && ["high", "critical"].includes(s.severity)
      ).length,
      recent: [...rows]
        .sort((a, b) => b.analyzed_at.localeCompare(a.analyzed_at))
        .slice(0, 8),
      failures: countFailureTypes(rows.map((r) => r.failure_types ?? [])),
    };
  }, [scorecards]);

  const regSummary = useMemo(() => {
    if (regressions.status !== "ready") return null;
    const rows = regressions.data;
    const regressed = rows.filter((r) => r.regression_status === "regressed");
    const improved = rows.filter((r) => r.regression_status === "improved");
    return { total: rows.length, regressed: regressed.length, improved: improved.length };
  }, [regressions]);

  return (
    <>
      <div className="page-header">
        <h1 className="page-title">Overview</h1>
        <div className="page-sub">
          Reliability posture across evaluated agent versions — served via Kong
          Gateway.
        </div>
      </div>

      {scorecards.status === "loading" && <LoadingNote label="Loading reliability data…" />}
      {scorecards.status === "error" && (
        <>
          <ErrorNote message={scorecards.error.message} />
          <p className="empty-note">
            Ensure the API Gateway is running (<code>docker compose up -d gateway</code>)
            and the Scorecard / Regression Tracker workers are up.
          </p>
        </>
      )}
      {scorecards.status === "empty" && (
        <EmptyNote>
          No evaluations recorded yet. Trigger one from{" "}
          <Link href="/run" style={{ color: "var(--accent)" }}>Run Evaluation</Link>.
        </EmptyNote>
      )}

      {stats && (
        <>
          <div className="grid grid-stats" style={{ gridTemplateColumns: "repeat(5, minmax(0,1fr))" }}>
            <div className="card" style={{ display: "flex", alignItems: "center", gap: 14 }}>
              <ScoreRing score={stats.avgScore} />
              <div>
                <div className="stat-label">Reliability</div>
                <div className="stat-label" style={{ textTransform: "none", letterSpacing: 0 }}>
                  mean score across{" "}
                  <b style={{ color: "var(--text-0)" }}>{stats.totalRuns}</b> runs
                </div>
              </div>
            </div>
            <StatCard value={stats.totalEvaluations} label="Total Evaluations"
                      foot={`${stats.totalRuns} distinct runs`} />
            <StatCard value={<span style={{ color: "var(--green)" }}>{stats.passed}</span>}
                      label="Passed Runs" accent="#34d399" />
            <StatCard value={<span style={{ color: "var(--red)" }}>{stats.failed}</span>}
                      label="Failed Runs" accent="#f87171" />
            <StatCard value={<span style={{ color: "#fb923c" }}>{stats.critical}</span>}
                      label="Critical Failures" accent="#fb923c"
                      foot="high & critical severity" />
          </div>

          <div className="grid grid-half">
            <Card title="Failure taxonomy — all evaluations">
              <TaxonomyBar counts={stats.failures} />
            </Card>
            <Card
              title="Regression movement"
              right={
                regSummary ? (
                  <Badge tone="neutral">{regSummary.total} tracked results</Badge>
                ) : undefined
              }
            >
              {regSummary && regSummary.total > 0 ? (
                <div style={{ display: "grid", gap: 10, marginTop: 4 }}>
                  <div style={{ display: "flex", justifyContent: "space-between" }}>
                    <span className="dim">Improved transitions</span>
                    <span className="delta-pos">▲ {regSummary.improved}</span>
                  </div>
                  <div style={{ display: "flex", justifyContent: "space-between" }}>
                    <span className="dim">Regressed transitions</span>
                    <span className="delta-neg">▼ {regSummary.regressed}</span>
                  </div>
                  <Link href="/regressions" className="btn btn-secondary"
                        style={{ justifyContent: "center", marginTop: 6 }}>
                    Open regression trends →
                  </Link>
                </div>
              ) : regressions.status === "ready" ? (
                <EmptyNote>No regression history yet.</EmptyNote>
              ) : (
                <LoadingNote />
              )}
            </Card>
          </div>

          <Card title="Recent evaluation status" right={
            <Link href="/evaluations" style={{ color: "var(--accent)", fontSize: 12 }}>
              view all →
            </Link>
          }>
            <div className="table-wrap">
              <table className="tbl">
                <thead>
                  <tr>
                    <th>Run</th><th>Agent</th><th>Status</th>
                    <th>Score</th><th>Severity</th><th>Failures</th><th>Analyzed</th>
                  </tr>
                </thead>
                <tbody>
                  {stats.recent.map((s) => (
                    <tr key={s.id}>
                      <td className="mono">{s.run_id}</td>
                      <td>{s.agent_name ?? "—"}</td>
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
