"""中国劳动领域运行适配器。
    把分流结果接进 Agent Runtime，决定继续、追问还是人工处理
"""

from typing import Any, Dict

from legal_agent_system.capabilities import ContextAssessment, RuntimeStep
from legal_agent_system.capabilities.contracts import PlanRevision
from legal_agent_system.runtime.errors import AgentRuntimeError
from legal_agent_system.runtime.schemas import AgentState
from legal_agent_system.labor_disputes.dispute_tags import (
    TERMINATION,
    WAGE_ARREARS,
    dispute_tags_from_facts,
)

from .verifier import LaborResultVerifier


class LaborDomainRuntimeAdapter:
    """把劳动事实、法域和工具参数适配到通用 Runtime 契约。"""

    domain_id = "cn_labor"

    def __init__(self, materials, labor_disputes, labor_triage, jurisdictions) -> None:
        self.materials = materials
        self.labor_disputes = labor_disputes
        self.labor_triage = labor_triage
        self.jurisdictions = jurisdictions
        self.verifier = LaborResultVerifier()

    def prepare_start(
        self, matter_id: str, client_id: str, facts: Dict[str, Any] | None,
        task_type: str | None = None,
    ) -> bool:
        if task_type == "labor_relationship_assessment":
            return self.labor_triage.update(matter_id, client_id, facts) is not None if facts else False
        return self.labor_disputes.update_facts(matter_id, client_id, facts) is not None if facts else False

    def assess_context(self, state: AgentState) -> ContextAssessment:
        try:
            jurisdiction = self.materials.get_confirmed_jurisdiction(state.matter_id, state.client_id)
        except AgentRuntimeError as exc:
            if exc.code != "JURISDICTION_CONFIRMATION_REQUIRED":
                raise
            return ContextAssessment(
                outcome="awaiting_jurisdiction",
                questions=["请明确确认本案件的适用法域和地区。"],
                error_code="JURISDICTION_CONFIRMATION_REQUIRED",
            )
        if jurisdiction["country_code"] != "CN":
            return ContextAssessment(
                outcome="human_handoff",
                error_code="UNSUPPORTED_JURISDICTION",
                blocked_reason="中国劳动领域能力包当前只支持中国法域",
            )
        workflow = self.get_workflow(state)
        missing = self._missing_facts(state, workflow)
        if missing:
            return ContextAssessment(
                outcome="awaiting_information",
                missing_facts=missing,
                questions=self._questions(state, workflow),
                error_code="INFORMATION_REQUIRED",
            )
        if state.task_type == "labor_relationship_assessment":
            result = workflow["result"]
            if result["triage_type"] == "high_risk_handoff":
                return ContextAssessment(
                    outcome="human_handoff",
                    error_code="HIGH_RISK_HANDOFF",
                    blocked_reason=result["recommended_next_step"],
                )
            if result["triage_type"] == "non_labor_dispute":
                return ContextAssessment(
                    outcome="human_handoff",
                    error_code="NON_LABOR_DISPUTE",
                    blocked_reason=result["recommended_next_step"],
                )
        return ContextAssessment(outcome="ready")

    def get_workflow(self, state: AgentState) -> Dict[str, Any]:
        if state.task_type == "labor_relationship_assessment":
            return self.labor_triage.get(state.matter_id, state.client_id)
        workflow = self.labor_disputes.get_workflow(state.matter_id, state.client_id)
        return {
            **workflow,
            "dispute_tags": dispute_tags_from_facts(workflow.get("facts") or {}),
        }

    def customize_plan(self, revision: PlanRevision, workflow: Dict[str, Any]) -> PlanRevision:
        dispute_tags = set(workflow.get("dispute_tags") or [])
        for step in revision.steps:
            if step.step_id != "evidence_check":
                continue
            if WAGE_ARREARS in dispute_tags:
                step.name = "核对欠薪期间、金额与工资证据"
            elif TERMINATION in dispute_tags:
                step.name = "核对解除原因、程序与通知证据"
        return revision

    def tool_arguments(self, state: AgentState, step: RuntimeStep) -> Dict[str, Any]:
        return {"matter_id": state.matter_id, "client_id": state.client_id}

    def jurisdiction_code(self, state: AgentState) -> str:
        return self.materials.get_confirmed_jurisdiction(state.matter_id, state.client_id)["country_code"]

    def verification_reports(self, tool_name, result, state, policy_ids, on_failure):
        report = self.verifier.verify(tool_name, result, state)
        domain_errors = report.authority_errors + report.fact_errors
        reports = []
        if any(policy_id.startswith("labor.") for policy_id in policy_ids):
            reports.append({
                "layer": "domain", "policy_id": "labor.domain", "version": "1.0.0",
                "valid": not domain_errors, "errors": domain_errors,
                "warnings": list(report.risk_warnings),
                "decision_hint": on_failure if domain_errors else "pass",
            })
        reports.append({
            "layer": "task", "policy_id": f"task.{tool_name}", "version": "1.0.0",
            "valid": not report.structure_errors, "errors": list(report.structure_errors),
            "warnings": list(report.risk_warnings),
            "decision_hint": on_failure if report.structure_errors else "pass",
        })
        return reports

    def provide_information(self, state: AgentState, payload: Dict[str, Any]) -> None:
        if state.task_type == "labor_relationship_assessment":
            self.labor_triage.update(state.matter_id, state.client_id, payload)
            return
        self.labor_disputes.update_facts(state.matter_id, state.client_id, payload)

    def confirm_jurisdiction(self, state: AgentState, payload: Dict[str, Any]) -> None:
        self.jurisdictions.confirm(state.matter_id, state.client_id, payload)

    @staticmethod
    def _missing_facts(state: AgentState, workflow: Dict[str, Any]) -> list[str]:
        if state.task_type == "labor_relationship_assessment":
            return list((workflow.get("result") or {}).get("missing_facts", []))
        return list(workflow.get("missing_facts", []))

    @staticmethod
    def _questions(state: AgentState, workflow: Dict[str, Any]) -> list[str]:
        if state.task_type == "labor_relationship_assessment":
            return list((workflow.get("result") or {}).get("questions", []))
        return list(workflow.get("questions", []))
