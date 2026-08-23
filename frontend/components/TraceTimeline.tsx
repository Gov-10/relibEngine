import type { DemoTraceEvent } from "@/lib/demo";
import { fmtMs } from "@/lib/hooks";

const KIND_ICON: Record<DemoTraceEvent["kind"], string> = {
  llm_call: "◆",
  tool_call: "⚙",
  state_transition: "⇢",
  system: "■",
};

function jsonLine(label: string, obj: unknown): string {
  return `${label} ${JSON.stringify(obj)}`;
}

/** Chronological execution timeline for one run. */
export function TraceTimeline({ events }: { events: DemoTraceEvent[] }) {
  return (
    <div className="timeline">
      {events.map((e) => {
        const t0 = events[0]?.ts_offset_ms ?? 0;
        const at = e.ts_offset_ms - t0;
        return (
          <div className="tl-item" key={e.id}>
            <span
              className={`tl-node${e.destructive ? " destructive" : ""}`}
              style={
                e.status === "error"
                  ? { borderColor: "#fbbf24" }
                  : e.status === "timeout"
                    ? { borderColor: "#94a3b8" }
                    : undefined
              }
            >
              {KIND_ICON[e.kind]}
            </span>
            <div className="tl-head">
              <span className="tl-name">{e.name}</span>
              <span className={`badge badge-${e.kind === "llm_call" ? "medium" : e.kind === "tool_call" ? "baseline" : "neutral"}`}>
                {e.kind.replace("_", " ")}
              </span>
              {e.destructive && <span className="destructive-flag">DESTRUCTIVE</span>}
              {e.status !== "ok" && (
                <span className={`badge badge-${e.status === "error" ? "fail" : "neutral"}`}>
                  {e.status.toUpperCase()}
                </span>
              )}
              <span className="tl-lat">+{fmtMs(at)} · {fmtMs(e.latency_ms)}</span>
            </div>
            {(e.args || e.result) && (
              <div className="tl-body">
                {e.args && jsonLine("args  →", e.args)}
                {e.args && e.result && "\n"}
                {e.result && jsonLine("result ←", e.result)}
              </div>
            )}
          </div>
        );
      })}
    </div>
  );
}
