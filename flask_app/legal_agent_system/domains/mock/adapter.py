"""阶段 1 模拟任务适配器；用于保留旧 HTTP 契约而不保留旧 Runtime。"""

from typing import Any, Dict

from legal_agent_system.capabilities import ContextAssessment, RuntimeStep
from legal_agent_system.capabilities.contracts import PlanRevision
from legal_agent_system.runtime.errors import AgentRuntimeError
from legal_agent_system.runtime.schemas import AgentState


class MockDomainRuntimeAdapter:
    domain_id = "system_mock"

    def prepare_start(
        self, matter_id: str, client_id: str, facts: Dict[str, Any] | None,
        task_type: str | None = None,
    ) -> bool:
        return False

    def assess_context(self, state: AgentState) -> ContextAssessment:
        return ContextAssessment(outcome="ready")

    def get_workflow(self, state: AgentState) -> Dict[str, Any]:
        return {"facts": {}}

    def customize_plan(self, revision: PlanRevision, workflow: Dict[str, Any]) -> PlanRevision:
        return revision

    def tool_arguments(self, state: AgentState, step: RuntimeStep) -> Dict[str, Any]:
        return {"goal": state.goal, "fail_first_attempt": True}

    def jurisdiction_code(self, state: AgentState) -> str:
        return ""

    def verification_reports(self, tool_name, result, state, policy_ids, on_failure):
        errors = [] if isinstance(result.data.get("summary"), str) else ["模拟摘要缺少 summary"]
        return [{
            "layer": "task", "policy_id": f"task.{tool_name}", "version": "1.0.0",
            "valid": not errors, "errors": errors, "warnings": list(result.warnings),
            "decision_hint": on_failure if errors else "pass",
        }]

    def provide_information(self, state: AgentState, payload: Dict[str, Any]) -> None:
        raise AgentRuntimeError("模拟任务不接受补充事实动作", "INVALID_STATE")

    def confirm_jurisdiction(self, state: AgentState, payload: Dict[str, Any]) -> None:
        raise AgentRuntimeError("模拟任务不需要确认法域", "INVALID_STATE")
