from typing import Literal

from pydantic import BaseModel, ConfigDict, Field


class FailureFinding(BaseModel):
    failure_type: Literal[
        "unsafe_destructive_action",
        "tool_call_loop",
        "goal_drift",
        "timeout",
        "hallucinated_confidence",
    ]
    severity: Literal["low", "medium", "high", "critical"]
    evidence: list[dict] = []


class AnalysisStats(BaseModel):
    steps: int
    errors: int
    destructive_attempts: int
    run_status: str
    duration_ms: float | None = None


class ReliabilityResult(BaseModel):
    model_config = ConfigDict(protected_namespaces=())

    run_id: str
    trace_id: str
    scenario_ref: str | None = None
    agent_name: str | None = None
    score: int = Field(ge=0, le=100)
    passed: bool
    failure_types: list[
        Literal[
            "unsafe_destructive_action",
            "tool_call_loop",
            "goal_drift",
            "timeout",
            "hallucinated_confidence",
        ]
    ] = []
    severity: Literal["low", "medium", "high", "critical"] = "low"
    findings: list[FailureFinding] = []
    stats: AnalysisStats
    explanation: str = ""
    analyzed_at: str
    event_published: bool = False
    event_topic: str | None = None
    event_error: str | None = None


class AnalysisRequest(BaseModel):
    include_explanation: bool = True
