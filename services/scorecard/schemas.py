from datetime import datetime
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field


class AnalysisEvent(BaseModel):
    """Inbound payload published by the Analyzer onto analysis-events."""

    schema_version: int = Field(default=1, ge=1)
    run_id: str = Field(min_length=1)
    trace_id: str | None = None
    scenario_ref: str | None = None
    agent_name: str | None = None
    score: int = Field(ge=0, le=100)
    passed: bool
    failure_types: list[str] = []
    severity: Literal["low", "medium", "high", "critical"] = "low"
    findings: list[dict] = []
    stats: dict = {}
    analyzed_at: str = Field(min_length=1)


class ScorecardOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    event_key: str
    run_id: str
    trace_id: str | None = None
    scenario_ref: str | None = None
    agent_name: str | None = None
    score: int
    passed: bool
    failure_types: list[str] = []
    severity: str
    findings: list[dict] = []
    analyzed_at: str
    captured_at: datetime | None = None
