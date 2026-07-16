"""Runtime 统一结果验证器。

验证器只输出可审计规则结果，不保存或暴露模型隐藏推理过程。
"""

from dataclasses import dataclass, field
from typing import Dict, List

from .schemas import AgentState, ToolResult


@dataclass
class VerificationReport:
    valid: bool = True
    structure_errors: List[str] = field(default_factory=list)
    fact_errors: List[str] = field(default_factory=list)
    authority_errors: List[str] = field(default_factory=list)
    risk_warnings: List[str] = field(default_factory=list)

    @property
    def errors(self) -> List[str]:
        return self.structure_errors + self.fact_errors + self.authority_errors


class AgentResultVerifier:
    """按工具类型执行结构、事实、来源和风险四类确定性校验。"""

    def verify(self, tool_name: str, result: ToolResult, state: AgentState) -> VerificationReport:
        report = VerificationReport()
        if result.success and not isinstance(result.data, dict):
            report.structure_errors.append("成功工具必须返回结构化 data")
        if result.tool_call_id not in {result.tool_call_id.strip()} or not result.tool_call_id:
            report.structure_errors.append("工具调用 ID 无效")

        if tool_name == "generate_evidence_checklist" and result.success:
            data = result.data or {}
            for key in ("available", "missing", "located_fact_count", "warning"):
                if key not in data:
                    report.structure_errors.append(f"证据清单缺少字段: {key}")

        if tool_name in {"analyze_labor_dispute", "analyze_labor_consultation", "analyze_labor_case"} and result.success:
            data = result.data or {}
            expected_status = "awaiting_draft_approval" if tool_name == "analyze_labor_dispute" else "completed_readonly"
            if data.get("status") != expected_status:
                report.structure_errors.append("劳动分析没有进入模板声明的完成状态")
            deadline = data.get("deadline") or {}
            if not deadline.get("start_date"):
                report.fact_errors.append("期限结果缺少起算日")
            if not deadline.get("estimated_deadline") and deadline.get("deadline_type") != "employment_active_wage_claim":
                report.fact_errors.append("期限结果缺少预计截止日或合法的开放期限类型")
            if deadline.get("deadline_type") == "employment_active_wage_claim" and not deadline.get("manual_review_required"):
                report.fact_errors.append("劳动关系存续欠薪的开放期限必须标记人工复核")
            authorities = data.get("authorities") or []
            authority_ids = {item.get("authority_id") for item in authorities}
            if not authority_ids or None in authority_ids:
                report.authority_errors.append("分析结果缺少已验证法律来源")
            if not authority_ids.issubset(set(result.authority_refs)):
                report.authority_errors.append("工具 authority_refs 与分析来源不一致")
            report.risk_warnings.extend(result.assumptions)

        if tool_name == "draft_labor_arbitration_application" and result.success:
            data = result.data or {}
            content = str(data.get("content", ""))
            if data.get("status") != "draft" or not data.get("artifact_id"):
                report.structure_errors.append("文书工具没有返回持久化草稿")
            if "草稿" not in content or "不代表已向仲裁机构提交" not in content:
                report.risk_warnings.append("草稿缺少明确的非正式提交声明")
                report.structure_errors.append("文书风险声明不完整")
            if not data.get("authority_refs"):
                report.authority_errors.append("草稿没有关联法律来源")

        report.valid = not report.errors
        return report


class LayeredVerifier:
    """Global/Domain/Task 三层只产出报告，不负责状态跳转。"""

    def __init__(self) -> None:
        self.task_verifier = AgentResultVerifier()

    def verify(
        self,
        tool_name: str,
        result: ToolResult,
        state: AgentState,
        policy_ids: List[str],
        on_failure: str,
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

        task_report = self.task_verifier.verify(tool_name, result, state) if result.success else VerificationReport(valid=False)
        domain_errors = task_report.authority_errors + task_report.fact_errors
        if any(policy_id.startswith("labor.") for policy_id in policy_ids):
            reports.append({
                "layer": "domain", "policy_id": "labor.domain", "version": "1.0.0",
                "valid": not domain_errors, "errors": domain_errors,
                "warnings": list(task_report.risk_warnings),
                "decision_hint": on_failure if domain_errors else "pass",
            })
        reports.append({
            "layer": "task", "policy_id": f"task.{tool_name}", "version": "1.0.0",
            "valid": not task_report.structure_errors,
            "errors": list(task_report.structure_errors),
            "warnings": list(task_report.risk_warnings),
            "decision_hint": on_failure if task_report.structure_errors else "pass",
        })
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
