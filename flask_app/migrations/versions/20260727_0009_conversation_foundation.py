"""新增阶段3.7D会话记忆、消息Token与请求幂等关联。"""

from typing import Sequence, Union

from alembic import context, op
import sqlalchemy as sa


revision: str = "20260727_0009"
down_revision: Union[str, None] = "20260721_0008"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def _create_memory_table() -> None:
    op.create_table(
        "conversation_memories",
        sa.Column("session_id", sa.String(), nullable=False),
        sa.Column("schema_version", sa.Integer(), nullable=False, server_default="1"),
        sa.Column("revision", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("structured_json", sa.JSON(), nullable=False),
        sa.Column("summary_text", sa.Text()),
        sa.Column("summary_items", sa.JSON(), nullable=False),
        sa.Column("summary_through_message_id", sa.String()),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.ForeignKeyConstraint(
            ["session_id"], ["digital_human_sessions.id"], ondelete="CASCADE",
        ),
        sa.PrimaryKeyConstraint("session_id"),
    )


def upgrade() -> None:
    if context.is_offline_mode():
        op.add_column("digital_human_messages", sa.Column("request_id", sa.String()))
        op.add_column("digital_human_messages", sa.Column("estimated_tokens", sa.Integer()))
        op.create_index(
            "ix_digital_human_messages_request_id",
            "digital_human_messages",
            ["request_id"],
        )
        op.create_unique_constraint(
            "uq_digital_human_message_request_role",
            "digital_human_messages",
            ["session_id", "request_id", "role"],
        )
        _create_memory_table()
        return

    inspector = sa.inspect(op.get_bind())
    tables = set(inspector.get_table_names())
    message_columns = {
        item["name"] for item in inspector.get_columns("digital_human_messages")
    }
    if "request_id" not in message_columns:
        op.add_column("digital_human_messages", sa.Column("request_id", sa.String()))
        op.create_index(
            "ix_digital_human_messages_request_id",
            "digital_human_messages",
            ["request_id"],
        )
    if "estimated_tokens" not in message_columns:
        op.add_column("digital_human_messages", sa.Column("estimated_tokens", sa.Integer()))
    constraints = {
        item["name"] for item in inspector.get_unique_constraints("digital_human_messages")
    }
    if "uq_digital_human_message_request_role" not in constraints:
        op.create_unique_constraint(
            "uq_digital_human_message_request_role",
            "digital_human_messages",
            ["session_id", "request_id", "role"],
        )
    if "conversation_memories" not in tables:
        _create_memory_table()


def downgrade() -> None:
    op.drop_table("conversation_memories")
    op.drop_constraint(
        "uq_digital_human_message_request_role",
        "digital_human_messages",
        type_="unique",
    )
    op.drop_index(
        "ix_digital_human_messages_request_id",
        table_name="digital_human_messages",
    )
    op.drop_column("digital_human_messages", "estimated_tokens")
    op.drop_column("digital_human_messages", "request_id")
