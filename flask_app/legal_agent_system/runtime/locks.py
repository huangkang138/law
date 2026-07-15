"""跨进程 Agent Run 执行锁。"""

import hashlib
from contextlib import contextmanager

from sqlalchemy import text

from core.database import engine

from .errors import AgentRuntimeError


class RunExecutionLock:
    """使用 PostgreSQL session advisory lock，覆盖一次完整 Graph 执行。"""

    @staticmethod
    def _key(run_id: str) -> int:
        return int.from_bytes(hashlib.sha256(run_id.encode()).digest()[:8], "big", signed=True)

    @contextmanager
    def acquire(self, run_id: str):
        connection = engine.connect()
        key = self._key(run_id)
        try:
            acquired = connection.execute(text("SELECT pg_try_advisory_lock(:key)"), {"key": key}).scalar()
            if not acquired:
                raise AgentRuntimeError("该任务正在执行，请稍后重试", "RUN_BUSY")
            yield
        finally:
            try:
                connection.execute(text("SELECT pg_advisory_unlock(:key)"), {"key": key})
            finally:
                connection.close()
