"""接管 2026-07-13 已有数据库结构，不重复操作现存业务表。"""

from typing import Sequence, Union

revision: str = "20260713_0001"
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """现有数据库使用 stamp 接管；后续结构变化从本 revision 向前迁移。"""


def downgrade() -> None:
    """基线不删除历史业务表，避免破坏已有数据。"""
