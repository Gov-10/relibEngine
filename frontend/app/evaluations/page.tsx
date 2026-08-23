"use client";

import { useState } from "react";
import { api } from "@/lib/api";
import { useApi, fmtTime } from "@/lib/hooks";
import {
  Badge, Card, DemoTag, EmptyNote, ErrorNote, LoadingNote,
  PassBadge, SeverityBadge,
} from "@/components/ui";
import { DEMO_EVALUATIONS, taxonomyMeta, type DemoEvaluation } from "@/lib/demo";

/**
 * Evaluation view.
 *
 * The Analyzer exposes no gateway route by architecture (it is an internal
 * Kafka/DB service), so this view renders the isolated demo dataset and
 * enriches it with any LIVE scorecard rows that share a run_id.
 */
export default function EvaluationsPage() {
  const scorecards = useApi(api.listScorecards);
  const [selected, setSelected] = useState<DemoEvaluation | null>(DEMO_EVALUATIONS[0]);

  const liveForRun =
    selected && scorecards.status === "ready"
      ? scorecards.data.filter((s) => s.run_id === selected.run_id)
      : [];

  return (
    <>
      <div className="page-header" style={{ display: "flex", justifyContent: "space-between", alignItems: "start" }}>
        <div>
          <h1 className="page-title">Evaluations</h1>
          <div className="page-sub">
            Failure classifications, severity and evidence per evaluated run.
          </div>
        </div>
        <DemoTag />
      </div>

      <div className="grid grid-half" style={{ gridTemplateColumns: "minmax(0,7fr) minmax(0,5fr)" }}>
        <Card title={`Evaluation runs (${DEMO_EVALUATIONS.length})`}>
          <div className="table-wrap">
            <table className="tbl">
              <thead>
                <tr><th>Run</th><th>Agent</th><th>Ver.</th><th>Status</th><th>Score</th><th>Severity</th></tr>
              </thead>
              <tbody>
                {DEMO_EVALUATIONS.map((e) => (
                  <tr key={e.id} onClick={() => setSelected(e)}
                      style={{ cursor: "pointer",
                               background: selected?.id === e.id ? "rgba(91,140,255,.08)" : undefined }}>
                    <td className="mono">{e.run_id}</td>
                    <td>{e.agent_name}</td>
                    <td className="mono dim">{e.agent_version}</td>
                    <td><PassBadge passed={e.status === "passed"} /></td>
                    <td className="mono">{e.score}</td>
                    <td><SeverityBadge severity={e.severity} /></td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </Card>

        {selected && (
          <Card title="Run detail">
            <div style={{ display: "grid", gap: 4 }}>
              <div style={{ fontSize: 16, fontWeight: 650 }}>{selected.scenario_title}</div>
              <div className="dim">
                agent <b style={{ color: "var(--text-0)" }}>{selected.agent_name}</b>{" "}
                <span className="mono">{selected.agent_version}</span> @{" "}
                <span className="mono">{selected.git_commit}</span>
                {" · "}scenario ref <span className="mono">#{selected.scenario_ref}</span>
              </div>
              <div style={{ display: "flex", gap: 8, margin: "10px 0 2px" }}>
                <PassBadge passed={selected.status === "passed"} />
                <SeverityBadge severity={selected.severity} />
                <span className="dimmer" style={{ fontSize: 12 }}>
                  analyzed {fmtTime(selected.analyzed_at)}
                </span>
              </div>

              <div style={{ marginTop: 12 }} className="card-title" >Failure classifications</div>
              {selected.failure_types.length ? (
                <div className="pill-row">
                  {selected.failure_types.map((f) => (
                    <span key={f} className="badge badge-neutral"
                          style={{ borderLeft: `3px solid ${taxonomyMeta(f).color}` }}>
                      {taxonomyMeta(f).label}
                    </span>
                  ))}
                </div>
              ) : (
                <EmptyNote>Clean run — no failure modes triggered.</EmptyNote>
              )}

              <div style={{ marginTop: 14 }} className="card-title">Evidence / findings</div>
              {selected.findings.length === 0 && (
                <EmptyNote>No findings attached to this evaluation.</EmptyNote>
              )}
              {selected.findings.map((f) => (
                <div key={f.code} className="finding-card"
                     style={{ borderLeftColor: "var(--amber)" }}>
                  <div className="finding-code">{f.code}</div>
                  <div style={{ fontWeight: 600, margin: "3px 0 5px" }}>{f.summary}</div>
                  <div className="dim" style={{ fontSize: 12.5 }}>{f.evidence}</div>
                  <div className="conf-bar"><div style={{ width: `${f.confidence * 100}%` }} /></div>
                  <div className="dimmer" style={{ fontSize: 11, marginTop: 3 }}>
                    classifier confidence {(f.confidence * 100).toFixed(0)}%
                  </div>
                </div>
              ))}

              {liveForRun.length > 0 && (
                <>
                  <div style={{ marginTop: 14 }} className="card-title">
                    Live scorecards for {selected.run_id}
                  </div>
                  {liveForRun.map((s) => (
                    <div key={s.id} style={{ display: "flex", gap: 8, alignItems: "center" }}>
                      <PassBadge passed={s.passed} />
                      <span className="mono dim">score {s.score}</span>
                      <Badge tone="improved">live via Kong</Badge>
                    </div>
                  ))}
                </>
              )}
            </div>
          </Card>
        )}
      </div>

      {scorecards.status === "error" && (
        <p className="dimmer" style={{ marginTop: 12 }}>
          Note: live scorecard enrichment unavailable ({scorecards.error.message}) —
          demo dataset still rendered.
        </p>
      )}
      {scorecards.status === "loading" && <LoadingNote label="Checking live scorecards…" />}
    </>
  );
}
