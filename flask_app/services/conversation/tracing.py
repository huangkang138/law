"""最小全链路 Trace：trace_id(=request_id) 串联 会话 → 路由 → 记忆 → 案件 → Agent。

正常运行时也会产出：每个事件以 JSONL 写入 logs/trace.jsonl（结构化、可 grep），
同时以 [trace] 前缀镜像到 app.log，按 trace_id 即可串起一次会话的完整链路。
Agent 步骤级明细仍以 DB 中 AgentRun.steps 为准，本模块通过
run_id ↔ trace_id 映射把会话与 Agent 运行关联起来（关联而非复制）。

Trace 写入失败绝不抛异常（不拖垮聊天主链路）。
"""

import json
import threading
from datetime import datetime, timezone
from typing import Optional

from core.logger import app_logger

DEFAULT_TRACE_FILE = "logs/trace.jsonl"

_lock = threading.Lock()
_trace_file: str = DEFAULT_TRACE_FILE
# run_id → trace_id：把 Agent 运行关联回发起它的会话请求。
_run_trace_map: dict = {}


def set_trace_file(path: str) -> None:
    """重定向 trace 文件（测试用）。"""
    global _trace_file
    _trace_file = path


def trace(event: str, trace_id: str, **fields) -> None:
    """写一条 trace 事件；任何异常都吞掉，不影响业务。"""
    payload = {
        "ts": datetime.now(timezone.utc).isoformat(),
        "trace_id": trace_id,
        "event": event,
        **fields,
    }
    message = f"[trace] {trace_id} {event} " + json.dumps(
        fields, ensure_ascii=False, default=str,
    )
    try:
        with _lock:
            with open(_trace_file, "a", encoding="utf-8") as file:
                file.write(json.dumps(payload, ensure_ascii=False, default=str) + "\n")
        app_logger.info(message)
    except Exception:
        # trace 失败绝不拖垮聊天主链路。
        pass


def link_run(run_id: Optional[str], trace_id: str) -> None:
    """登记 run_id ↔ trace_id 关联（Agent 步骤回溯用）。"""
    if run_id:
        _run_trace_map[run_id] = trace_id


def trace_for_run(run_id: str) -> Optional[str]:
    """查询 Agent 运行对应的会话 trace_id。"""
    return _run_trace_map.get(run_id)


def unlink_run(run_id: Optional[str]) -> None:
    """Agent 运行结束时解除映射（进程内存，避免无限增长）。"""
    if run_id:
        _run_trace_map.pop(run_id, None)
