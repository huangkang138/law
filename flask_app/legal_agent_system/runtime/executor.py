"""工具策略执行器：统一输入、法域、审批、超时和重试边界。"""
import uuid
from concurrent.futures import ThreadPoolExecutor, TimeoutError
from .schemas import ToolResult


class PolicyToolExecutor:
    def execute(self, definition, handler, arguments: dict, jurisdiction: str, approved: bool = False):
        missing = [k for k in definition.input_schema.get("required", []) if k not in arguments]
        if missing:
            return ToolResult(tool_call_id=f"tool_{uuid.uuid4().hex}", success=False, error_code="INVALID_INPUT", error_message=f"缺少字段: {', '.join(missing)}")
        if definition.supported_jurisdictions and jurisdiction not in definition.supported_jurisdictions:
            return ToolResult(tool_call_id=f"tool_{uuid.uuid4().hex}", success=False, error_code="UNSUPPORTED_JURISDICTION")
        if definition.requires_approval and not approved:
            return ToolResult(tool_call_id=f"tool_{uuid.uuid4().hex}", success=False, error_code="APPROVAL_REQUIRED")
        attempts = definition.max_retries + 1
        for attempt in range(1, attempts + 1):
            call_id = f"tool_{uuid.uuid4().hex}"
            pool = ThreadPoolExecutor(max_workers=1)
            try:
                result = pool.submit(handler, call_id, arguments, attempt).result(definition.timeout_seconds)
            except TimeoutError:
                result = ToolResult(tool_call_id=call_id, success=False, error_code="TOOL_TIMEOUT", retryable=True)
                pool.shutdown(wait=False, cancel_futures=True)
            else:
                pool.shutdown(wait=True)
            if result.success or not result.retryable or attempt == attempts:
                return result
