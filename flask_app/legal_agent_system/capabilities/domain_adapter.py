"""领域运行适配器契约：隔离通用 Runtime 与具体法律领域服务。"""

from dataclasses import dataclass, field
from typing import Any, Dict, List, Protocol, TYPE_CHECKING, runtime_checkable

from .contracts import PlanRevision

if TYPE_CHECKING:
    from legal_agent_system.runtime.schemas import AgentState, ToolResult


@dataclass(frozen=True)
class ContextAssessment:
    """领域上下文检查结果；Runtime 根据结果更新全局 Run 状态。"""

    outcome: str
    missing_facts: List[str] = field(default_factory=list)
    questions: List[str] = field(default_factory=list)
    error_code: str | None = None
    blocked_reason: str | None = None


class RuntimeStep(Protocol):
    """Adapter 可读取的持久化步骤最小视图。"""

    id: str
    template_step_id: str
    tool_name: str


@runtime_checkable
class DomainRuntimeAdapter(Protocol):
    """每个 Domain Package 必须提供的运行时边界。"""

    domain_id: str

    def prepare_start(self, matter_id: str, client_id: str, facts: Dict[str, Any] | None) -> bool: ...

    def assess_context(self, state: "AgentState") -> ContextAssessment: ...

    def get_workflow(self, state: "AgentState") -> Dict[str, Any]: ...

    def customize_plan(self, revision: PlanRevision, workflow: Dict[str, Any]) -> PlanRevision: ...

    def tool_arguments(self, state: "AgentState", step: RuntimeStep) -> Dict[str, Any]: ...

    def jurisdiction_code(self, state: "AgentState") -> str: ...

    def verification_reports(
        self,
        tool_name: str,
        result: "ToolResult",
        state: "AgentState",
        policy_ids: List[str],
        on_failure: str,
    ) -> List[Dict[str, Any]]: ...

    def provide_information(self, state: "AgentState", payload: Dict[str, Any]) -> None: ...

    def confirm_jurisdiction(self, state: "AgentState", payload: Dict[str, Any]) -> None: ...
