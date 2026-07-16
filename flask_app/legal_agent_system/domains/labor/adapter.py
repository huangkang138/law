"""中国劳动领域运行适配器。"""

from typing import Any, Dict

from legal_agent_system.capabilities import ContextAssessment, RuntimeStep
from legal_agent_system.capabilities.contracts import PlanRevision
from legal_agent_system.runtime.errors import AgentRuntimeError
from legal_agent_system.runtime.schemas import AgentState

from .verifier import LaborResultVerifier


class LaborDomainRuntimeAdapter:
    """把劳动事实、法域和工具参数适配到通用 Runtime 契约。"""

    domain_id = "cn_labor"

    def __init__(self, materials, labor_disputes, jurisdictions) -> None:
        self.materials = materials
        self.labor_disputes = labor_disputes
        self.jurisdictions = jurisdictions
        self.verifier = LaborResultVerifier()

    def prepare_start(self, matter_id: str, client_id: str, facts: Dict[str, Any] | None) -> bool:
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
        if workflow["missing_facts"]:
            return ContextAssessment(
                outcome="awaiting_information",
                missing_facts=list(workflow["missing_facts"]),
                questions=list(workflow["questions"]),
                error_code="INFORMATION_REQUIRED",
            )
        return ContextAssessment(outcome="ready")

    def get_workflow(self, state: AgentState) -> Dict[str, Any]:
        return self.labor_disputes.get_workflow(state.matter_id, state.client_id)

    def customize_plan(self, revision: PlanRevision, workflow: Dict[str, Any]) -> PlanRevision:
        claims = (workflow.get("facts") or {}).get("claim_types", [])
        for step in revision.steps:
            if step.step_id != "evidence_check":
                continue
            if "欠薪" in claims:
                step.name = "核对欠薪期间、金额与工资证据"
            elif "违法解除" in claims:
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
        self.labor_disputes.update_facts(state.matter_id, state.client_id, payload)

    def confirm_jurisdiction(self, state: AgentState, payload: Dict[str, Any]) -> None:
        self.jurisdictions.confirm(state.matter_id, state.client_id, payload)
