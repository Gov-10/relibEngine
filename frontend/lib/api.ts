// =============================================================================
// Centralized API client — ALL backend communication goes through the Kong
// API Gateway (the ONLY entry point, per ARCHITECTURE.md). No microservice is
// ever addressed directly.
//
// Gateway routes available today (Task 5.1):
//   POST /api/scenarios/generate          Scenario Generator
//   GET  /api/scenarios/{id}              Scenario Generator
//   GET  /api/scorecards                  Scorecard Service
//   GET  /api/scorecards/run/{run_id}           (+ /latest)
//   GET  /api/regressions                 Regression Tracker
//   GET  /api/regressions/agent/{name}          (+ /latest)
//   GET  /api/regressions/run/{run_id}
//   *    /api/auth/**                     Auth Service (not yet implemented -> 503)
//
// Trace Store and Analyzer expose no gateway routes by design; the Evaluation
// and Trace views therefore render isolated demo data (see lib/demo.ts).
// =============================================================================

export const API_BASE_URL: string =
  process.env.NEXT_PUBLIC_API_BASE_URL ?? "http://localhost:8000";

export type Severity = "low" | "medium" | "high" | "critical";
export type RegressionStatus =
  | "baseline"
  | "improved"
  | "regressed"
  | "unchanged";

export interface Scorecard {
  id: number;
  event_key: string;
  run_id: string;
  trace_id: string | null;
  scenario_ref: string | null;
  agent_name: string | null;
  score: number;
  passed: boolean;
  failure_types: string[];
  severity: string;
  findings: Record<string, unknown>[];
  analyzed_at: string;
  captured_at: string | null;
}

export interface RegressionResult {
  id: number;
  event_key: string;
  run_id: string;
  trace_id: string | null;
  scenario_ref: string | null;
  agent_name: string | null;
  agent_version: string | null;
  git_commit: string | null;
  score: number;
  passed: boolean;
  failure_types: string[];
  severity: string;
  previous_run_id: string | null;
  previous_score: number | null;
  score_delta: number | null;
  failure_delta: Record<string, number>;
  regression_status: RegressionStatus;
  analyzed_at: string;
  captured_at: string | null;
}

export interface ToolDefinitionPayload {
  name: string;
  description?: string;
  input_schema?: Record<string, unknown>;
}

export interface GenerateScenariosRequest {
  agent_name: string;
  description?: string;
  task_domain: string;
  system_prompt: string;
  prompt_version?: string;
  tools: ToolDefinitionPayload[];
  num_scenarios: number;
}

export interface GeneratedScenario {
  id: number;
  title: string;
  severity: string;
  payload: Record<string, unknown>;
  expected_behavior: string | null;
}

export interface ScenarioJobInfo {
  scenario_id: number;
  job_id: string;
  published: boolean;
  detail: string | null;
}

export interface GenerateScenariosResponse {
  agent_id: number;
  prompt_id: number;
  generated_by: string;
  scenarios: GeneratedScenario[];
  jobs: ScenarioJobInfo[];
}

export class ApiError extends Error {
  status: number;
  constructor(status: number, message: string) {
    super(message);
    this.status = status;
    this.name = "ApiError";
  }
}

async function request<T>(path: string, init?: RequestInit): Promise<T> {
  let res: Response;
  try {
    res = await fetch(`${API_BASE_URL}${path}`, {
      ...init,
      headers: { "Content-Type": "application/json", ...(init?.headers ?? {}) },
      cache: "no-store",
    });
  } catch {
    throw new ApiError(0, `API Gateway unreachable at ${API_BASE_URL}`);
  }
  if (!res.ok) {
    let detail = res.statusText;
    try {
      const body = await res.json();
      detail = typeof body?.detail === "string" ? body.detail : JSON.stringify(body);
    } catch {
      /* keep statusText */
    }
    throw new ApiError(res.status, `${res.status}: ${detail}`);
  }
  return res.json() as Promise<T>;
}

export const api = {
  listScorecards: () => request<Scorecard[]>("/api/scorecards"),
  latestScorecardForRun: (runId: string) =>
    request<Scorecard>(`/api/scorecards/run/${encodeURIComponent(runId)}/latest`),
  scorecardsForRun: (runId: string) =>
    request<Scorecard[]>(`/api/scorecards/run/${encodeURIComponent(runId)}`),
  listRegressions: () => request<RegressionResult[]>("/api/regressions"),
  regressionsForAgent: (agentName: string) =>
    request<RegressionResult[]>(`/api/regressions/agent/${encodeURIComponent(agentName)}`),
  latestRegressionForAgent: (agentName: string) =>
    request<RegressionResult>(`/api/regressions/agent/${encodeURIComponent(agentName)}/latest`),
  regressionForRun: (runId: string) =>
    request<RegressionResult>(`/api/regressions/run/${encodeURIComponent(runId)}`),
  generateScenarios: (payload: GenerateScenariosRequest) =>
    request<GenerateScenariosResponse>("/api/scenarios/generate", {
      method: "POST",
      body: JSON.stringify(payload),
    }),
};
