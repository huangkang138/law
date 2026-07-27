"""跨进程会话编排锁，避免同一Session并发产生重复动作。"""

import hashlib
from contextlib import contextmanager

from sqlalchemy import text

from core.database import engine

from .repository import RequestInProgress


class ConversationSessionLock:
    @staticmethod
    def _key(session_id: str) -> int:
        payload = f"conversation:{session_id}".encode("utf-8")
        return int.from_bytes(
            hashlib.sha256(payload).digest()[:8], "big", signed=True,
        )

    @contextmanager
    def acquire(self, session_id: str):
        connection = engine.connect()
        key = self._key(session_id)
        acquired = False
        try:
            acquired = bool(connection.execute(
                text("SELECT pg_try_advisory_lock(:key)"),
                {"key": key},
            ).scalar())
            if not acquired:
                raise RequestInProgress("该会话正在处理另一条消息，请稍后重试")
            yield
        finally:
            if acquired:
                connection.execute(
                    text("SELECT pg_advisory_unlock(:key)"),
                    {"key": key},
                )
            connection.close()
