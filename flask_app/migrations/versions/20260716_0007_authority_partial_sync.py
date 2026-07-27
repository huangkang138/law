"""记录逐来源同步失败数量。"""

from typing import Sequence, Union

from alembic import context, op
import sqlalchemy as sa

revision: str = "20260716_0007"
down_revision: Union[str, None] = "20260716_0006"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    if context.is_offline_mode():
        op.execute(
            "ALTER TABLE authority_sync_runs "
            "ADD COLUMN IF NOT EXISTS failed_count INTEGER NOT NULL DEFAULT 0"
        )
        return
    inspector = sa.inspect(op.get_bind())
    columns = {column["name"] for column in inspector.get_columns("authority_sync_runs")}
    if "failed_count" not in columns:
        op.add_column(
            "authority_sync_runs",
            sa.Column("failed_count", sa.Integer(), nullable=False, server_default="0"),
        )


def downgrade() -> None:
    op.drop_column("authority_sync_runs", "failed_count")
