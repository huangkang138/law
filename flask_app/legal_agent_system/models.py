"""法律 Agent 新增版本化实体，避免继续膨胀旧 db_models.py。"""

from sqlalchemy import Boolean, Column, DateTime, ForeignKey, Integer, JSON, String, Text, UniqueConstraint, func

from core.database import Base


class MatterFactAssertion(Base):
    __tablename__ = "matter_fact_assertions"
    id = Column(String, primary_key=True)
    matter_id = Column(String, ForeignKey("matters.id", ondelete="CASCADE"), nullable=False, index=True)
    client_id = Column(String, nullable=False, index=True)
    fact_key = Column(String, nullable=False, index=True)
    value_json = Column(JSON, nullable=False)
    source_type = Column(String, nullable=False)
    document_id = Column(String)
    fragment_id = Column(String)
    quote = Column(Text)
    confirmed_by_user = Column(Boolean, nullable=False, default=True)
    version = Column(Integer, nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    __table_args__ = (UniqueConstraint("matter_id", "fact_key", "version", name="uq_fact_assertion_version"),)


class AgentPlan(Base):
    __tablename__ = "agent_plans"
    id = Column(String, primary_key=True)
    run_id = Column(String, ForeignKey("agent_runs.id", ondelete="CASCADE"), nullable=False, index=True)
    version = Column(Integer, nullable=False)
    task_type = Column(String, nullable=False)
    input_fingerprint = Column(String, nullable=False, index=True)
    plan_json = Column(JSON, nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    __table_args__ = (UniqueConstraint("run_id", "version", name="uq_agent_plan_version"),)


class AgentRunAction(Base):
    __tablename__ = "agent_run_actions"
    id = Column(String, primary_key=True)
    run_id = Column(String, ForeignKey("agent_runs.id", ondelete="CASCADE"), nullable=False, index=True)
    idempotency_key = Column(String, nullable=False)
    action = Column(String, nullable=False)
    payload_hash = Column(String, nullable=False)
    response_json = Column(JSON)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    __table_args__ = (UniqueConstraint("run_id", "idempotency_key", name="uq_run_action_key"),)


class AgentEventOutbox(Base):
    __tablename__ = "agent_event_outbox"
    id = Column(String, primary_key=True)
    run_id = Column(String, ForeignKey("agent_runs.id", ondelete="CASCADE"), nullable=False, index=True)
    event_type = Column(String, nullable=False, index=True)
    payload_json = Column(JSON, nullable=False, default=dict)
    published_at = Column(DateTime(timezone=True))
    created_at = Column(DateTime(timezone=True), server_default=func.now(), index=True)
