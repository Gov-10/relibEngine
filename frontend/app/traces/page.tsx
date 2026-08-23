"use client";

import { useState } from "react";
import Link from "next/link";
import { Card, DemoTag, EmptyNote } from "@/components/ui";
import { TraceTimeline } from "@/components/TraceTimeline";
import { DEMO_EVALUATIONS, demoTraceFor } from "@/lib/demo";
import { fmtMs } from "@/lib/hooks";

/**
 * Trace Explorer.
 *
 * Trace Capturer writes exclusively to the Trace Store (no HTTP API by
 * architecture), so traces shown here come from the isolated demo dataset.
 */
export default function TracesPage() {
  const [runId, setRunId] = useState(DEMO_EVALUATIONS[0].run_id);
  const events = demoTraceFor(runId);
  const totalLatency = events.reduce((a, e) => a + e.latency_ms, 0);
  const destructive = events.filter((e) => e.destructive).length;
  const errors = events.filter((e) => e.status !== "ok").length;

  return (
    <>
      <div className="page-header" style={{ display: "flex", justifyContent: "space-between", alignItems: "start" }}>
        <div>
          <h1 className="page-title">Trace Explorer</h1>
          <div className="page-sub">
            Chronological LLM / tool execution timeline captured during sandbox runs.
          </div>
        </div>
        <DemoTag />
      </div>

      <Card title="Select run">
        <select value={runId} onChange={(e) => setRunId(e.target.value)} style={{ maxWidth: 340 }}>
          {DEMO_EVALUATIONS.map((e) => (
            <option key={e.run_id} value={e.run_id}>
              {e.run_id} — {e.scenario_title.slice(0, 46)}
            </option>
          ))}
        </select>
        <div className="pill-row" style={{ marginTop: 12 }}>
          <span className="badge badge-neutral">{events.length} steps</span>
          <span className="badge badge-neutral">total {fmtMs(totalLatency)}</span>
          <span className="badge badge-neutral">{events.filter((e) => e.kind === "llm_call").length} LLM calls</span>
          <span className="badge badge-neutral">{events.filter((e) => e.kind === "tool_call").length} tool calls</span>
          {destructive > 0 && <span className="badge badge-critical">{destructive} destructive</span>}
          {errors > 0 && <span className="badge badge-medium">{errors} errors/timeouts</span>}
          <Link href="/evaluations" style={{ color: "var(--accent)", fontSize: 12 }}>
            related evaluation →
          </Link>
        </div>
      </Card>

      <Card title={`Execution timeline — ${runId}`}>
        {events.length === 0 ? (
          <EmptyNote>No trace events for this run.</EmptyNote>
        ) : (
          <TraceTimeline events={events} />
        )}
      </Card>
    </>
  );
}
