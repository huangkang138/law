"""把验证报告归一为唯一的 Runtime 路由决策。
   将验证报告转换为下一步、重试、补信息、审批、移交或结束
"""

from typing import Dict

from .schemas import ToolResult


class DecisionRouter:
    ACTIONS = {
        "next_step", "retry_step", "request_context", "replan",
        "require_approval", "reject", "handoff", "finish",
    }

    def decide(
        self,
        result: ToolResult,
        verification: Dict,
        *,
        on_failure: str,
        has_next_step: bool,
    ) -> Dict:
        if result.success and verification.get("valid"):
            action = "next_step" if has_next_step else "finish"
            return {"action": action, "reason": "step_verified"}

        hints = [
            report.get("decision_hint")
            for report in verification.get("reports", [])
            if not report.get("valid")
        ]
        hint = next((item for item in hints if item and item != "pass"), on_failure)
        mapping = {
            "retry": "retry_step",
            "request_context": "request_context",
            "replan": "replan",
            "handoff": "handoff",
            "reject": "reject",
        }
        action = mapping.get(hint, "reject")
        if action == "retry_step" and not result.retryable:
            action = "reject"
        return {
            "action": action,
            "reason": result.error_code or "verification_failed",
        }
