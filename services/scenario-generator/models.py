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


class Agent(Base):
    __tablename__ = "agents"

    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String(100), unique=True, nullable=False)
    description = Column(Text, nullable=True)
    task_domain = Column(String(100), nullable=False, default="general")
    is_active = Column(Boolean, nullable=False, default=True)
    created_at = Column(DateTime(timezone=True), nullable=False, server_default=func.now())
    updated_at = Column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
        onupdate=func.now(),
    )

    prompts = relationship(
        "AgentPrompt", back_populates="agent", cascade="all, delete-orphan"
    )
    tools = relationship("Tool", back_populates="agent", cascade="all, delete-orphan")
    scenarios = relationship(
        "Scenario", back_populates="agent", cascade="all, delete-orphan"
    )
    criteria = relationship(
        "EvaluationCriterion", back_populates="agent", cascade="all, delete-orphan"
    )


class AgentPrompt(Base):
    __tablename__ = "agent_prompts"
    __table_args__ = (Index("ix_agent_prompts_agent_id", "agent_id"),)

    id = Column(Integer, primary_key=True, autoincrement=True)
    agent_id = Column(Integer, ForeignKey("agents.id"), nullable=False)
    version = Column(String(20), nullable=False, default="v1")
    content = Column(Text, nullable=False)
    is_active = Column(Boolean, nullable=False, default=True)
    created_at = Column(DateTime(timezone=True), nullable=False, server_default=func.now())

    agent = relationship("Agent", back_populates="prompts")


class Tool(Base):
    __tablename__ = "tools"
    __table_args__ = (
        UniqueConstraint("agent_id", "name", name="uq_tools_agent_name"),
        Index("ix_tools_agent_id", "agent_id"),
    )

    id = Column(Integer, primary_key=True, autoincrement=True)
    agent_id = Column(Integer, ForeignKey("agents.id"), nullable=False)
    name = Column(String(100), nullable=False)
    description = Column(Text, nullable=True)
    input_schema = Column(JSONB, nullable=False, default=dict)
    mock_config = Column(JSONB, nullable=True)
    created_at = Column(DateTime(timezone=True), nullable=False, server_default=func.now())

    agent = relationship("Agent", back_populates="tools")


class Scenario(Base):
    __tablename__ = "scenarios"
    __table_args__ = (
        CheckConstraint(
            "severity IN ('low', 'medium', 'high', 'critical')",
            name="ck_scenarios_severity",
        ),
        Index("ix_scenarios_agent_id", "agent_id"),
        Index("ix_scenarios_prompt_id", "prompt_id"),
    )

    id = Column(Integer, primary_key=True, autoincrement=True)
    agent_id = Column(Integer, ForeignKey("agents.id"), nullable=False)
    prompt_id = Column(Integer, ForeignKey("agent_prompts.id"), nullable=True)
    title = Column(String(200), nullable=False)
    description = Column(Text, nullable=True)
    payload = Column(JSONB, nullable=False)
    expected_behavior = Column(Text, nullable=True)
    severity = Column(String(10), nullable=False, default="medium")
    created_at = Column(DateTime(timezone=True), nullable=False, server_default=func.now())

    agent = relationship("Agent", back_populates="scenarios")
    prompt = relationship("AgentPrompt")
    criteria = relationship(
        "EvaluationCriterion", back_populates="scenario", cascade="all, delete-orphan"
    )


class EvaluationCriterion(Base):
    __tablename__ = "evaluation_criteria"
    __table_args__ = (
        CheckConstraint(
            "criterion_type IN ('tool_call', 'safety', 'output_match', 'latency', 'custom')",
            name="ck_evaluation_criteria_type",
        ),
        CheckConstraint("weight >= 0", name="ck_evaluation_criteria_weight_nonneg"),
        Index("ix_evaluation_criteria_agent_id", "agent_id"),
        Index("ix_evaluation_criteria_scenario_id", "scenario_id"),
    )

    id = Column(Integer, primary_key=True, autoincrement=True)
    agent_id = Column(Integer, ForeignKey("agents.id"), nullable=False)
    scenario_id = Column(Integer, ForeignKey("scenarios.id"), nullable=True)
    name = Column(String(100), nullable=False)
    criterion_type = Column(String(20), nullable=False, default="custom")
    config = Column(JSONB, nullable=False, default=dict)
    weight = Column(Float, nullable=False, default=1.0)
    created_at = Column(DateTime(timezone=True), nullable=False, server_default=func.now())

    agent = relationship("Agent", back_populates="criteria")
    scenario = relationship("Scenario", back_populates="criteria")
