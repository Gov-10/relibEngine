from sqlalchemy import Boolean, Column, DateTime, Float, Integer, String, Text
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import declarative_base


Base = declarative_base()


class Run(Base):
    __tablename__ = "runs"

    id = Column(Integer, primary_key=True)
    run_id = Column(String(64))
    trace_id = Column(String(64))
    scenario_ref = Column(String(64))
    temporal_workflow_id = Column(String(255))
    agent_name = Column(String(100))
    status = Column(String(20))
    total_latency_ms = Column(Float)
    llm_call_count = Column(Integer)
    tool_call_count = Column(Integer)
    metadata_json = Column(JSONB)
    started_at = Column(DateTime(timezone=True))
    finished_at = Column(DateTime(timezone=True))
    created_at = Column(DateTime(timezone=True))


class TraceStep(Base):
    __tablename__ = "trace_steps"

    id = Column(Integer, primary_key=True)
    run_id = Column(Integer)
    step_index = Column(Integer)
    span_id = Column(String(64))
    parent_span_id = Column(String(64))
    step_type = Column(String(20))
    tool_name = Column(String(100))
    llm_model = Column(String(100))
    system_prompt = Column(Text)
    input_data = Column(JSONB)
    output_data = Column(JSONB)
    error_text = Column(Text)
    latency_ms = Column(Float)
    tokens_prompt = Column(Integer)
    tokens_completion = Column(Integer)
    failure_flag = Column(Boolean)
    failure_type = Column(String(30))
    created_at = Column(DateTime(timezone=True))
