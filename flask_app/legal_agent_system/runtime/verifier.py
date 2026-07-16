"""Runtime 统一结果验证器。

验证器只输出可审计规则结果，不保存或暴露模型隐藏推理过程。
"""

from typing import Dict, List
from .schemas import AgentState, ToolResult


class LayeredVerifier:
    """Global/Domain/Task 三层只产出报告，不负责状态跳转。"""

    def verify(
        self,
        tool_name: str,
        result: ToolResult,
        state: AgentState,
        policy_ids: List[str],
        on_failure: str,
        domain_adapter,
    ) -> Dict:
        global_errors: List[str] = []
        if not result.success:
            global_errors.append(result.error_message or result.error_code or "工具执行失败")
        if result.success and not isinstance(result.data, dict):
            global_errors.append("成功工具必须返回结构化 data")
        reports = [{
            "layer": "global", "policy_id": "global.tool_result", "version": "1.0.0",
            "valid": not global_errors, "errors": global_errors,
            "warnings": list(result.warnings),
            "decision_hint": self._failure_hint(result, on_failure) if global_errors else "pass",
        }]

        if result.success:
            reports.extend(domain_adapter.verification_reports(
                tool_name, result, state, policy_ids, on_failure,
            ))
        return {
            "valid": all(item["valid"] for item in reports),
            "reports": reports,
        }

    @staticmethod
    def _failure_hint(result: ToolResult, on_failure: str) -> str:
        if result.error_code == "AUTHORITY_REQUIRED":
            return "reject"
        if result.retryable:
            return "retry"
        return on_failure
