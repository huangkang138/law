"""统一法源快照约束：每个同步批次保存自己的原始响应。"""

from typing import Sequence, Union

from alembic import op

revision: str = "20260716_0006"
down_revision: Union[str, None] = "20260716_0005"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # 历史实库曾额外增加跨批次内容唯一约束，与“每次同步都保留原始响应”冲突。
    # 批次内重复仍由 uq_authority_snapshot_run_source 阻止。
    op.execute(
        "ALTER TABLE authority_source_snapshots "
        "DROP CONSTRAINT IF EXISTS uq_authority_snapshot_content"
    )


def downgrade() -> None:
    # 不恢复跨批次唯一约束，避免删除或合并已经形成的审计快照。
    pass
