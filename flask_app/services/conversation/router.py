"""统一会话Router：只决策，不产生外部动作。"""

import re
from typing import Dict, Optional

from .schemas import ContextEnvelope, RouterDecision


LABOR_TERMS = (
    "劳动", "工资", "薪资", "薪水", "欠薪", "加班", "辞退", "解雇",
    "离职", "入职", "试用期", "实习", "兼职", "社保", "工伤",
    "用人单位", "劳动合同",
)
CASE_ACTION_PATTERNS = (
    r"(我要|我想|请|帮我|替我).{0,8}(申请|提起).{0,4}(劳动)?仲裁",
    r"(帮我处理|帮我维权|我要维权|作为案件|建立案件|开始分析|提交材料)",
)
CONSULTATION_PATTERNS = (
    r"(需要|要|应当|具备).{0,8}(哪些|什么).{0,6}(条件|材料|证据)",
    r"(条件|流程|步骤|期限|时效|费用).{0,6}(是什[么麼]|有哪些|怎么|如何)",
    r"(怎么|如何).{0,6}(申请|提起).{0,4}(劳动)?仲裁",
    r"(能不能|是否|可以吗|是什么|什么意思|多久|找谁)",
)
HIGH_RISK_PATTERNS = (
    r"人身安全|生命危险|正在被打|遭到殴打",
    r"威胁|胁迫|强迫",
    r"未成年|童工",
    r"(集体|群体).{0,8}(欠薪|纠纷|维权)",
)


class ConversationRouter:
    ALLOWED_ROUTES = {
        "normal_chat", "labor_consultation", "labor_triage",
        "matter_interaction", "agent_continue", "workspace_guidance",
        "high_risk_handoff",
    }

    def route(
        self,
        question: str,
        context: ContextEnvelope,
        parsed: Optional[Dict] = None,
    ) -> RouterDecision:
        for pattern in HIGH_RISK_PATTERNS:
            if re.search(pattern, question):
                return RouterDecision("high_risk_handoff", 1.0, "deterministic_high_risk")

        if context.matter_id:
            if context.memory_conflicts:
                return RouterDecision(
                    "workspace_guidance", 1.0, "confirmed_fact_conflict",
                )
            if context.run_status in {"blocked_authority", "human_handoff"}:
                return RouterDecision(
                    "workspace_guidance", 1.0, "protected_agent_state",
                )
            if context.run_status == "awaiting_approval":
                return RouterDecision(
                    "matter_interaction", 1.0, "approval_requires_workspace",
                )
            if re.search(r"继续|下一步|重新分析|再试一次", question):
                return RouterDecision("agent_continue", 0.95, "active_matter_continue")
            if re.search(r"材料|证据|事实|案件|进度|状态|审批|法源", question):
                return RouterDecision("matter_interaction", 0.92, "active_matter_context")

        is_labor = any(term in question for term in LABOR_TERMS)
        if is_labor and self.authorizes_labor_triage(question):
            return RouterDecision(
                "labor_triage",
                0.98,
                "explicit_labor_case_intent",
                side_effect_authorized=True,
            )
        if is_labor:
            return RouterDecision("labor_consultation", 0.9, "deterministic_labor_topic")

        llm_route = parsed.get("conversation_route") if parsed else None
        llm_confidence = float(parsed.get("confidence", 0.0)) if parsed else 0.0
        if llm_route == "labor_triage":
            return RouterDecision(
                "normal_chat",
                max(llm_confidence, 0.7),
                "llm_side_effect_not_authorized",
            )
        if llm_route in self.ALLOWED_ROUTES and llm_confidence >= 0.75:
            return RouterDecision(
                llm_route, llm_confidence, "structured_llm_fallback",
            )
        if parsed and parsed.get("intent") in {"dispute_center", "dispute_organize", "case_analysis"}:
            return RouterDecision("workspace_guidance", 0.75, "legacy_intent_guidance")
        return RouterDecision("normal_chat", 0.7, "default_chat")

    @staticmethod
    def authorizes_labor_triage(question: str) -> bool:
        """仅依据当前用户输入授权建案；LLM、摘要和历史记忆都不参与。"""
        if any(re.search(pattern, question) for pattern in CONSULTATION_PATTERNS):
            return False
        return any(re.search(pattern, question) for pattern in CASE_ACTION_PATTERNS)
