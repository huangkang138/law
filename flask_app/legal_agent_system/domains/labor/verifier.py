"""中国劳动领域的事实、法源和交付物验证。"""

from dataclasses import dataclass, field
from typing import List

from legal_agent_system.runtime.schemas import AgentState, ToolResult


@dataclass
class LaborVerification:
    structure_errors: List[str] = field(default_factory=list)
    fact_errors: List[str] = field(default_factory=list)
    authority_errors: List[str] = field(default_factory=list)
    risk_warnings: List[str] = field(default_factory=list)

    @property
    def valid(self) -> bool:
        """领域校验是否通过；风险警告本身不等于失败。"""
        return not (self.structure_errors or self.fact_errors or self.authority_errors)


class LaborResultVerifier:
    def verify(self, tool_name: str, result: ToolResult, state: AgentState) -> LaborVerification:
        report = LaborVerification()
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
        return report
