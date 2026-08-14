"""为会话请求增加可恢复业务动作检查点。"""

from typing import Sequence, Union

from alembic import context, op
import sqlalchemy as sa


revision: str = "20260727_0010"
down_revision: Union[str, None] = "20260727_0009"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    columns = (
        sa.Column("action_type", sa.String()),
        sa.Column("action_resource_json", sa.JSON()),
        sa.Column("checkpoint_json", sa.JSON()),
        sa.Column("lease_token", sa.String()),
        sa.Column("lease_expires_at", sa.DateTime(timezone=True)),
    )
    if context.is_offline_mode():
        for column in columns:
            op.add_column("digital_human_requests", column)
        return

    existing = {
        item["name"]
        for item in sa.inspect(op.get_bind()).get_columns("digital_human_requests")
    }
    for column in columns:
        if column.name not in existing:
            op.add_column("digital_human_requests", column)


def downgrade() -> None:
    op.drop_column("digital_human_requests", "lease_expires_at")
    op.drop_column("digital_human_requests", "lease_token")
    op.drop_column("digital_human_requests", "checkpoint_json")
    op.drop_column("digital_human_requests", "action_resource_json")
    op.drop_column("digital_human_requests", "action_type")
