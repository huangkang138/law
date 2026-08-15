"""服务端取消：进程内取消标志与数据库取消状态的统一查询入口。

取消通过双通道生效：
- 进程级标志：同进程（Flask 单进程/线程模型）即时唤醒在途 LLM 分块循环；
- 数据库状态：digital_human_requests.status 为 cancelling/cancelled 时，
  跨进程（多 worker）由分块循环按节流间隔轮询发现并置位本地标志。
"""

import threading
import time
from typing import Dict, Optional

from core.database import SessionLocal
from core.logger import app_logger
from models.db_models import DigitalHumanRequest

CANCELLING = "cancelling"
CANCELLED = "cancelled"
CANCELLED_STATUSES = {CANCELLING, CANCELLED}

REGISTRY_TTL_SECONDS = 15 * 60  # 与请求租约时长对齐
DB_POLL_INTERVAL_SECONDS = 0.5


class ConversationCancelled(Exception):
    """请求已被用户停止；code 稳定为 CANCELLED。

    注意：不能继承 RuntimeError，否则 /chat 路由的
    `except RuntimeError -> 409 REQUEST_IN_PROGRESS` 会先截获。
    """

    code = "CANCELLED"

    def __init__(self, message: str = "回复已停止"):
        super().__init__(message)


class _CancelEntry:
    __slots__ = ("event", "created_at", "last_db_poll")

    def __init__(self) -> None:
        self.event = threading.Event()
        self.created_at = time.monotonic()
        self.last_db_poll = 0.0


_REGISTRY: Dict[str, _CancelEntry] = {}
_REGISTRY_LOCK = threading.Lock()


def _prune_locked(now: float) -> None:
    stale = [
        request_id for request_id, entry in _REGISTRY.items()
        if now - entry.created_at > REGISTRY_TTL_SECONDS
    ]
    for request_id in stale:
        del _REGISTRY[request_id]


def arm(request_id: str) -> None:
    """登记请求；若入口已存在则保持原样（绝不重置已置位的取消标志）。"""
    with _REGISTRY_LOCK:
        _prune_locked(time.monotonic())
        _REGISTRY.setdefault(request_id, _CancelEntry())


def disarm(request_id: str) -> None:
    """请求结束（含异常与客户端断连）时移除入口。"""
    with _REGISTRY_LOCK:
        _REGISTRY.pop(request_id, None)


def set_cancelled(request_id: str) -> None:
    """取消端点调用：get-or-create 入口并置位；请求行尚未创建时也先生效。"""
    with _REGISTRY_LOCK:
        _prune_locked(time.monotonic())
        entry = _REGISTRY.get(request_id)
        if entry is None:
            entry = _CancelEntry()
            _REGISTRY[request_id] = entry
        entry.event.set()


def is_cancelled(request_id: str, poll_db: bool = False) -> bool:
    """先查进程内标志；未置位且 poll_db=True 时按节流间隔读库。

    库中 status 为 cancelling/cancelled 时置位本地标志并返回 True。
    DB 异常吞掉并返回 False（绝不因一次 DB 抖动打断正常分块循环）。
    """
    entry = _entry(request_id)
    if entry is not None and entry.event.is_set():
        return True
    if not poll_db:
        return False

    with _REGISTRY_LOCK:
        entry = _REGISTRY.get(request_id)
        if entry is None:
            return False
        now = time.monotonic()
        if now - entry.last_db_poll < DB_POLL_INTERVAL_SECONDS:
            return False
        entry.last_db_poll = now

    db = SessionLocal()
    try:
        record = db.get(DigitalHumanRequest, request_id)
        if record is not None and record.status in CANCELLED_STATUSES:
            set_cancelled(request_id)
            return True
        return False
    except Exception:
        app_logger.warning(f"数字人取消状态轮询数据库异常 [request={request_id}]")
        return False
    finally:
        db.close()


def _entry(request_id: str) -> Optional[_CancelEntry]:
    with _REGISTRY_LOCK:
        _prune_locked(time.monotonic())
        return _REGISTRY.get(request_id)
