from sqlalchemy import (
    Boolean,
    CheckConstraint,
    Column,
    DateTime,
    Float,
    ForeignKey,
    Index,
    Integer,
    String,
    Text,
    UniqueConstraint,
    func,
)
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import relationship

from database import Base


class Run(Base):
    __tablename__ = "runs"
    __table_args__ = (
        CheckConstraint(
            "status IN ('running', 'completed', 'failed', 'timeout', 'cancelled')",
            name="ck_runs_status",
        ),
        Index("ix_runs_status", "status"),
        Index("ix_runs_started_at", "started_at"),
    )

    id = Column(Integer, primary_key=True, autoincrement=True)
    run_id = Column(String(64), unique=True, nullable=False)
    trace_id = Column(String(64), unique=True, nullable=False)
    scenario_ref = Column(String(64), nullable=True)
    temporal_workflow_id = Column(String(255), nullable=True)
    agent_name = Column(String(100), nullable=True)
    status = Column(String(20), nullable=False, default="running")
    total_latency_ms = Column(Float, nullable=True)
    llm_call_count = Column(Integer, nullable=False, default=0)
    tool_call_count = Column(Integer, nullable=False, default=0)
    metadata_json = Column(JSONB, nullable=True)
    started_at = Column(DateTime(timezone=True), nullable=False, server_default=func.now())
    finished_at = Column(DateTime(timezone=True), nullable=True)
    created_at = Column(DateTime(timezone=True), nullable=False, server_default=func.now())

    steps = relationship(
        "TraceStep",
        back_populates="run",
        cascade="all, delete-orphan",
        order_by="TraceStep.step_index",
    )


class TraceStep(Base):
    __tablename__ = "trace_steps"
    __table_args__ = (
        UniqueConstraint("run_id", "step_index", name="uq_steps_run_step_index"),
        CheckConstraint(
            "step_type IN ('llm_call', 'tool_call', 'state_transition', 'console')",
            name="ck_steps_step_type",
        ),
        CheckConstraint(
            "failure_type IS NULL OR failure_type IN "
            "('tool_loop', 'hallucinated_confidence', 'goal_drift', 'safety_violation', 'other')",
            name="ck_steps_failure_type",
        ),
        CheckConstraint(
            "(failure_flag = FALSE) OR (failure_flag = TRUE AND failure_type IS NOT NULL)",
            name="ck_steps_failure_pairing",
        ),
        Index("ix_steps_tool_name", "tool_name"),
        Index("ix_steps_step_type", "step_type"),
        Index("ix_steps_failure_flag", "failure_flag"),
        Index("ix_steps_created_at", "created_at"),
    )

    id = Column(Integer, primary_key=True, autoincrement=True)
    run_id = Column(Integer, ForeignKey("runs.id"), nullable=False)
    step_index = Column(Integer, nullable=False)
    span_id = Column(String(64), nullable=True)
    parent_span_id = Column(String(64), nullable=True)
    step_type = Column(String(20), nullable=False)
    tool_name = Column(String(100), nullable=True)
    llm_model = Column(String(100), nullable=True)
    system_prompt = Column(Text, nullable=True)
    input_data = Column(JSONB, nullable=True)
    output_data = Column(JSONB, nullable=True)
    error_text = Column(Text, nullable=True)
    latency_ms = Column(Float, nullable=False, default=0.0)
    tokens_prompt = Column(Integer, nullable=True)
    tokens_completion = Column(Integer, nullable=True)
    failure_flag = Column(Boolean, nullable=False, default=False)
    failure_type = Column(String(30), nullable=True)
    created_at = Column(DateTime(timezone=True), nullable=False, server_default=func.now())

    run = relationship("Run", back_populates="steps")
