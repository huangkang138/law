"""新增阶段 3.7A 劳动案件分流结果表。"""

from typing import Sequence, Union

from alembic import context, op
import sqlalchemy as sa

revision: str = "20260721_0008"
down_revision: Union[str, None] = "20260716_0007"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    if context.is_offline_mode():
        op.create_table(
            "labor_case_triages",
            sa.Column("matter_id", sa.String(), nullable=False),
            sa.Column("client_id", sa.String(), nullable=False),
            sa.Column("facts_json", sa.JSON(), nullable=False),
            sa.Column("result_json", sa.JSON(), nullable=False),
            sa.Column("version", sa.Integer(), nullable=False, server_default="0"),
            sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
            sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
            sa.ForeignKeyConstraint(["matter_id"], ["matters.id"], ondelete="CASCADE"),
            sa.PrimaryKeyConstraint("matter_id"),
        )
        op.create_index("ix_labor_case_triages_client_id", "labor_case_triages", ["client_id"])
        return
    inspector = sa.inspect(op.get_bind())
    if "labor_case_triages" not in inspector.get_table_names():
        op.create_table(
            "labor_case_triages",
            sa.Column("matter_id", sa.String(), nullable=False),
            sa.Column("client_id", sa.String(), nullable=False),
            sa.Column("facts_json", sa.JSON(), nullable=False),
            sa.Column("result_json", sa.JSON(), nullable=False),
            sa.Column("version", sa.Integer(), nullable=False, server_default="0"),
            sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
            sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
            sa.ForeignKeyConstraint(["matter_id"], ["matters.id"], ondelete="CASCADE"),
            sa.PrimaryKeyConstraint("matter_id"),
        )
        op.create_index("ix_labor_case_triages_client_id", "labor_case_triages", ["client_id"])


def downgrade() -> None:
    op.drop_index("ix_labor_case_triages_client_id", table_name="labor_case_triages")
    op.drop_table("labor_case_triages")
