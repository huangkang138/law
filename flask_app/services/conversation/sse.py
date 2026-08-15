"""SSE增量呈现：事件编码、文本分块与流错误映射。

阶段3.7F第一部分只负责把"服务端已完成解析、路由、安全校验和持久化"的
已验证回复分块下发；事件不暴露原始LLM Token，也不包含服务端取消能力。
"""

import json
from typing import Dict, Iterable

from sqlalchemy.exc import SQLAlchemyError

from .cancel import ConversationCancelled
from .repository import RequestInProgress

DEFAULT_CHUNK_SIZE = 12  # 每个delta事件包含的字符数
DEFAULT_CHUNK_DELAY = 0.02  # 两个delta事件之间的呈现间隔（秒）

EVENT_STATUS = "status"
EVENT_DELTA = "delta"
EVENT_COMPLETED = "completed"
EVENT_ERROR = "error"

STATUS_ACCEPTED = "accepted"
STATUS_THINKING = "thinking"


def encode_event(event: str, data: Dict, request_id: str) -> str:
    """编码单条SSE事件；request_id必带，且不可被事件载荷覆盖。"""
    payload = dict(data)
    payload["request_id"] = request_id
    return f"event: {event}\ndata: {json.dumps(payload, ensure_ascii=False)}\n\n"


def iter_text_chunks(text: str, size: int = DEFAULT_CHUNK_SIZE) -> Iterable[str]:
    """按字符切分已验证回复；所有块按序拼接必须与原文一致。"""
    if size <= 0:
        raise ValueError("分块大小必须为正整数")
    for position in range(0, len(text), size):
        yield text[position:position + size]


def stream_error_data(exc: Exception) -> Dict:
    """把处理异常映射为稳定错误事件载荷：中文错误、错误码、是否可重试。"""
    if isinstance(exc, RequestInProgress):
        return {
            "error": str(exc) or "该请求正在处理中",
            "code": "REQUEST_IN_PROGRESS",
            "retryable": True,
        }
    if isinstance(exc, ConversationCancelled):
        # 服务端已落 cancelled 终态；同 request_id 重试可恢复或重跑。
        return {
            "error": str(exc) or "回复已停止",
            "code": "CANCELLED",
            "retryable": True,
        }
    if isinstance(exc, PermissionError):
        return {"error": str(exc), "code": "FORBIDDEN", "retryable": False}
    if isinstance(exc, LookupError):
        return {"error": str(exc), "code": "NOT_FOUND", "retryable": False}
    if isinstance(exc, ValueError):
        return {"error": str(exc), "code": "INVALID_INPUT", "retryable": False}
    if isinstance(exc, SQLAlchemyError):
        return {
            "error": "数字人数据服务暂时不可用，请稍后重试",
            "code": "DATABASE_UNAVAILABLE",
            "retryable": True,
        }
    return {
        "error": "数字人暂时无法回答，请稍后重试",
        "code": "INTERNAL_ERROR",
        "retryable": True,
    }
