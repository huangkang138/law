"""阶段 3.4 来源、事实、计划、幂等和事件模型。"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

revision: str = "20260713_0002"
down_revision: Union[str, None] = "20260713_0001"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    inspector = sa.inspect(op.get_bind())
    existing_tables = set(inspector.get_table_names())
    authority_columns = {column["name"] for column in inspector.get_columns("legal_authorities")}
    for name, column in [
        ("provider", sa.Column("provider", sa.String(), nullable=False, server_default="legacy")),
        ("external_id", sa.Column("external_id", sa.String())),
        ("canonical_url", sa.Column("canonical_url", sa.Text())),
        ("trust_level", sa.Column("trust_level", sa.String(), nullable=False, server_default="untrusted")),
        ("version", sa.Column("version", sa.String(), nullable=False, server_default="1")),
        ("supersedes_id", sa.Column("supersedes_id", sa.String())),
        ("last_verified_at", sa.Column("last_verified_at", sa.DateTime(timezone=True))),
        ("retrieval_status", sa.Column("retrieval_status", sa.String(), nullable=False, server_default="stored")),
    ]:
        if name not in authority_columns:
            op.add_column("legal_authorities", column)
    additions = {"agent_steps": [("plan_id", sa.Column("plan_id", sa.String())), ("plan_version", sa.Column("plan_version", sa.Integer(), nullable=False, server_default="1"))], "labor_dispute_profiles": [("facts_version", sa.Column("facts_version", sa.Integer(), nullable=False, server_default="0")), ("rule_version", sa.Column("rule_version", sa.String(), nullable=False, server_default="labor-rules-1"))], "agent_artifacts": [("input_fingerprint", sa.Column("input_fingerprint", sa.String())), ("version", sa.Column("version", sa.Integer(), nullable=False, server_default="1"))]}
    for table, columns in additions.items():
        known = {column["name"] for column in inspector.get_columns(table)}
        for name, column in columns:
            if name not in known:
                op.add_column(table, column)
    if "matter_fact_assertions" not in existing_tables:
        op.create_table("matter_fact_assertions", sa.Column("id", sa.String(), primary_key=True), sa.Column("matter_id", sa.String(), sa.ForeignKey("matters.id", ondelete="CASCADE"), nullable=False), sa.Column("client_id", sa.String(), nullable=False), sa.Column("fact_key", sa.String(), nullable=False), sa.Column("value_json", sa.JSON(), nullable=False), sa.Column("source_type", sa.String(), nullable=False), sa.Column("document_id", sa.String()), sa.Column("fragment_id", sa.String()), sa.Column("quote", sa.Text()), sa.Column("confirmed_by_user", sa.Boolean(), nullable=False), sa.Column("version", sa.Integer(), nullable=False), sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()), sa.UniqueConstraint("matter_id", "fact_key", "version", name="uq_fact_assertion_version"))
    if "agent_plans" not in existing_tables:
        op.create_table("agent_plans", sa.Column("id", sa.String(), primary_key=True), sa.Column("run_id", sa.String(), sa.ForeignKey("agent_runs.id", ondelete="CASCADE"), nullable=False), sa.Column("version", sa.Integer(), nullable=False), sa.Column("task_type", sa.String(), nullable=False), sa.Column("input_fingerprint", sa.String(), nullable=False), sa.Column("plan_json", sa.JSON(), nullable=False), sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()), sa.UniqueConstraint("run_id", "version", name="uq_agent_plan_version"))
    if "agent_run_actions" not in existing_tables:
        op.create_table("agent_run_actions", sa.Column("id", sa.String(), primary_key=True), sa.Column("run_id", sa.String(), sa.ForeignKey("agent_runs.id", ondelete="CASCADE"), nullable=False), sa.Column("idempotency_key", sa.String(), nullable=False), sa.Column("action", sa.String(), nullable=False), sa.Column("payload_hash", sa.String(), nullable=False), sa.Column("response_json", sa.JSON()), sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()), sa.UniqueConstraint("run_id", "idempotency_key", name="uq_run_action_key"))
    if "agent_event_outbox" not in existing_tables:
        op.create_table("agent_event_outbox", sa.Column("id", sa.String(), primary_key=True), sa.Column("run_id", sa.String(), sa.ForeignKey("agent_runs.id", ondelete="CASCADE"), nullable=False), sa.Column("event_type", sa.String(), nullable=False), sa.Column("payload_json", sa.JSON(), nullable=False), sa.Column("published_at", sa.DateTime(timezone=True)), sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()))


def downgrade() -> None:
    op.drop_table("agent_event_outbox")
    op.drop_table("agent_run_actions")
    op.drop_table("agent_plans")
    op.drop_table("matter_fact_assertions")
    for table, columns in [("agent_artifacts", ["version", "input_fingerprint"]), ("labor_dispute_profiles", ["rule_version", "facts_version"]), ("agent_steps", ["plan_version", "plan_id"]), ("legal_authorities", ["retrieval_status", "last_verified_at", "supersedes_id", "version", "trust_level", "canonical_url", "external_id", "provider"])]:
        for column in columns:
            op.drop_column(table, column)
