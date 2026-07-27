"""方案 C 能力注册、计划修订和单步审计字段。"""

from typing import Sequence, Union

from alembic import context, op
import sqlalchemy as sa

revision: str = "20260716_0004"
down_revision: Union[str, None] = "20260713_0003"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


PLAN_COLUMNS = (
    ("domain_id", "VARCHAR NOT NULL DEFAULT 'legacy'", sa.Column("domain_id", sa.String(), nullable=False, server_default="legacy")),
    ("template_id", "VARCHAR NOT NULL DEFAULT 'legacy'", sa.Column("template_id", sa.String(), nullable=False, server_default="legacy")),
    ("template_version", "VARCHAR NOT NULL DEFAULT '1.0.0'", sa.Column("template_version", sa.String(), nullable=False, server_default="1.0.0")),
    ("replan_reason", "TEXT", sa.Column("replan_reason", sa.Text())),
    ("triggered_by", "VARCHAR NOT NULL DEFAULT 'runtime'", sa.Column("triggered_by", sa.String(), nullable=False, server_default="runtime")),
    ("parent_plan_id", "VARCHAR", sa.Column("parent_plan_id", sa.String())),
)

STEP_COLUMNS = (
    ("template_step_id", "VARCHAR", sa.Column("template_step_id", sa.String())),
    ("step_type", "VARCHAR", sa.Column("step_type", sa.String())),
    ("requires_approval", "BOOLEAN NOT NULL DEFAULT FALSE", sa.Column("requires_approval", sa.Boolean(), nullable=False, server_default=sa.false())),
    ("verification_policy_ids", "JSON NOT NULL DEFAULT '[]'::json", sa.Column("verification_policy_ids", sa.JSON(), nullable=False, server_default=sa.text("'[]'::json"))),
    ("skip_reason", "TEXT", sa.Column("skip_reason", sa.Text())),
    ("observation_json", "JSON", sa.Column("observation_json", sa.JSON())),
    ("verification_json", "JSON", sa.Column("verification_json", sa.JSON())),
    ("decision_json", "JSON", sa.Column("decision_json", sa.JSON())),
)


def upgrade() -> None:
    if context.is_offline_mode():
        for name, sql_type, _column in PLAN_COLUMNS:
            op.execute(f"ALTER TABLE agent_plans ADD COLUMN IF NOT EXISTS {name} {sql_type}")
        for name, sql_type, _column in STEP_COLUMNS:
            op.execute(f"ALTER TABLE agent_steps ADD COLUMN IF NOT EXISTS {name} {sql_type}")
        op.execute("CREATE INDEX IF NOT EXISTS ix_agent_plans_template_id ON agent_plans (template_id)")
        return

    inspector = sa.inspect(op.get_bind())
    plan_columns = {column["name"] for column in inspector.get_columns("agent_plans")}
    step_columns = {column["name"] for column in inspector.get_columns("agent_steps")}
    for name, _sql_type, column in PLAN_COLUMNS:
        if name not in plan_columns:
            op.add_column("agent_plans", column)
    for name, _sql_type, column in STEP_COLUMNS:
        if name not in step_columns:
            op.add_column("agent_steps", column)
    indexes = {item["name"] for item in inspector.get_indexes("agent_plans")}
    if "ix_agent_plans_template_id" not in indexes:
        op.create_index("ix_agent_plans_template_id", "agent_plans", ["template_id"])


def downgrade() -> None:
    op.drop_index("ix_agent_plans_template_id", table_name="agent_plans")
    for name, _sql_type, _column in reversed(STEP_COLUMNS):
        op.drop_column("agent_steps", name)
    for name, _sql_type, _column in reversed(PLAN_COLUMNS):
        op.drop_column("agent_plans", name)
