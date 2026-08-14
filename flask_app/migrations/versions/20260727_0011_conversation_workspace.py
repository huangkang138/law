"""新增每会话一行的当前案件工作台状态。"""

from typing import Sequence, Union

from alembic import context, op
import sqlalchemy as sa


revision: str = "20260727_0011"
down_revision: Union[str, None] = "20260727_0010"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    table_name = "conversation_workspace_states"
    index_name = "ix_conversation_workspace_states_active_matter_id"
    inspector = None if context.is_offline_mode() else sa.inspect(op.get_bind())
    table_exists = inspector is not None and table_name in inspector.get_table_names()
    if not table_exists:
        op.create_table(
            table_name,
            sa.Column(
                "session_id",
                sa.String(),
                sa.ForeignKey("digital_human_sessions.id", ondelete="CASCADE"),
                primary_key=True,
            ),
            sa.Column(
                "active_matter_id",
                sa.String(),
                sa.ForeignKey("matters.id", ondelete="SET NULL"),
                nullable=True,
            ),
            sa.Column("version", sa.Integer(), nullable=False, server_default="0"),
            sa.Column(
                "created_at",
                sa.DateTime(timezone=True),
                nullable=False,
                server_default=sa.func.now(),
            ),
            sa.Column(
                "updated_at",
                sa.DateTime(timezone=True),
                nullable=False,
                server_default=sa.func.now(),
            ),
        )
    existing_indexes = set() if inspector is None or not table_exists else {
        item["name"] for item in inspector.get_indexes(table_name)
    }
    if index_name not in existing_indexes:
        op.create_index(index_name, table_name, ["active_matter_id"])


def downgrade() -> None:
    op.drop_index(
        "ix_conversation_workspace_states_active_matter_id",
        table_name="conversation_workspace_states",
    )
    op.drop_table("conversation_workspace_states")
