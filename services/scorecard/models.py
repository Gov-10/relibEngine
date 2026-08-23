from sqlalchemy import Boolean, Column, DateTime, Integer, String, func
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import declarative_base


Base = declarative_base()


class Scorecard(Base):
    __tablename__ = "scorecards"

    id = Column(Integer, primary_key=True, autoincrement=True)
    event_key = Column(String(160), unique=True, nullable=False)
    run_id = Column(String(64), index=True, nullable=False)
    trace_id = Column(String(64))
    scenario_ref = Column(String(64))
    agent_name = Column(String(100))
    score = Column(Integer, nullable=False)
    passed = Column(Boolean, nullable=False)
    failure_types = Column(JSONB, default=list)
    severity = Column(String(20), nullable=False)
    findings = Column(JSONB, default=list)
    analyzed_at = Column(String(64), nullable=False)
    captured_at = Column(DateTime(timezone=True), server_default=func.now())
