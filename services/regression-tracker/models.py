from sqlalchemy import Boolean, Column, DateTime, Integer, String, func
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import declarative_base


Base = declarative_base()


class AnalysisEventLog(Base):
    __tablename__ = "analysis_events"

    id = Column(Integer, primary_key=True, autoincrement=True)
    event_key = Column(String(160), unique=True, nullable=False)
    run_id = Column(String(64), index=True, nullable=False)
    agent_name = Column(String(100))
    payload = Column(JSONB, nullable=False)
    consumed_at = Column(DateTime(timezone=True), server_default=func.now())


class RegressionResult(Base):
    __tablename__ = "regression_results"

    id = Column(Integer, primary_key=True, autoincrement=True)
    event_key = Column(String(160), unique=True, nullable=False)
    run_id = Column(String(64), index=True, nullable=False)
    trace_id = Column(String(64))
    scenario_ref = Column(String(64))
    agent_name = Column(String(100), index=True)
    agent_version = Column(String(50))
    git_commit = Column(String(64))
    score = Column(Integer, nullable=False)
    passed = Column(Boolean, nullable=False)
    failure_types = Column(JSONB, default=list)
    severity = Column(String(20), nullable=False)
    previous_run_id = Column(String(64))
    previous_score = Column(Integer)
    score_delta = Column(Integer)
    failure_delta = Column(JSONB, default=dict)
    regression_status = Column(String(20), nullable=False)
    analyzed_at = Column(String(64), nullable=False)
    captured_at = Column(DateTime(timezone=True), server_default=func.now())
