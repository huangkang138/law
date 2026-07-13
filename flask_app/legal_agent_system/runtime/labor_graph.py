"""阶段 3.1 中国劳动纠纷 LangGraph 状态机。"""

import uuid
from typing import Dict

from langgraph.graph import END, StateGraph

from .enums import RunStatus, StepStatus
from .errors import AgentRuntimeError
from .schemas import AgentState
from .verifier import AgentResultVerifier


class LaborDisputeGraph:
    """将法域、事实、计划、工具、验证和审批串成可恢复任务。"""

    PLAN = [
        {"name": "核对材料与证据缺口", "tool_name": "generate_evidence_checklist"},
        {"name": "计算期限并验证法律来源", "tool_name": "analyze_labor_dispute"},
        {"name": "生成劳动仲裁申请书草稿", "tool_name": "draft_labor_arbitration_application"},
    ]

    def __init__(self, repository, registry, materials, labor_disputes) -> None:

        """
        初始化方法，用于设置类的实例属性并构建一个状态图(StateGraph)

        参数:
            repository: 仓库对象，用于存储和管理数据
            registry: 注册表对象，用于维护注册信息
            materials: 材料对象，包含所需材料相关信息
            labor_disputes: 劳务纠纷对象，处理劳务相关争议

        返回:
            None
        """
        self.repository = repository  # 初始化仓库属性
        self.registry = registry    # 初始化注册表属性
        self.materials = materials  # 初始化材料属性
        self.labor_disputes = labor_disputes  # 初始化劳务纠纷属性
        self.verifier = AgentResultVerifier()  # 创建结果验证器实例


    # 创建状态图并配置节点和边
        graph = StateGraph(dict)  # 初始化状态图，使用字典作为状态类型
        graph.add_node("dispatch", lambda state: state)  # 添加调度节点，保持状态不变
        graph.add_node("ensure_context", self._ensure_context)  # 添加上下文确认节点
        graph.add_node("execute", self._execute)  # 添加执行节点
        graph.add_node("draft", self._draft)  # 添加起草节点


    # 设置入口点和条件边
        graph.set_entry_point("dispatch")  # 设置调度节点为入口点
        graph.add_conditional_edges("dispatch", self._route, {  # 添加调度节点的条件边
            "ensure_context": "ensure_context", "execute": "execute",
            "draft": "draft", "stop": END,
        })
        graph.add_conditional_edges("ensure_context", self._after_context, {"execute": "execute", "stop": END})
        graph.add_conditional_edges("execute", self._after_execute, {"execute": "execute", "stop": END})
        graph.add_edge("draft", END)
        self.compiled = graph.compile()

    @staticmethod
    def _route(raw: Dict) -> str:
        status = raw["status"]
        if status in {RunStatus.PLANNING.value, RunStatus.REPLANNING.value}:
            return "ensure_context"
        if status == RunStatus.EXECUTING.value:
            return "execute"
        if status == RunStatus.AWAITING_APPROVAL.value and raw.get("approved") is True:
            return "draft"
        return "stop"

    @staticmethod
    def _after_context(raw: Dict) -> str:
        return "execute" if raw["status"] == RunStatus.EXECUTING.value else "stop"

    @staticmethod
    def _after_execute(raw: Dict) -> str:
        return "execute" if raw["status"] == RunStatus.EXECUTING.value else "stop"

    def _ensure_context(self, raw: Dict) -> Dict:
        state = AgentState.model_validate(raw)
        try:
            jurisdiction = self.materials.get_confirmed_jurisdiction(state.matter_id, state.client_id)
        except AgentRuntimeError as exc:
            if exc.code != "JURISDICTION_CONFIRMATION_REQUIRED":
                raise
            state.status = RunStatus.AWAITING_JURISDICTION
            state.questions = ["请明确确认本案件的适用法域和地区。"]
            state.error_code = "JURISDICTION_CONFIRMATION_REQUIRED"
            self.repository.save_state(state, "run_waiting_for_jurisdiction")
            return state.model_dump(mode="json")
        if jurisdiction["country_code"] != "CN":
            state.status = RunStatus.HUMAN_HANDOFF
            state.blocked_reason = "劳动纠纷 Runtime 当前只支持中国法域"
            state.error_code = "UNSUPPORTED_JURISDICTION"
            self.repository.save_state(state, "run_handoff_required")
            return state.model_dump(mode="json")

        workflow = self.labor_disputes.get_workflow(state.matter_id, state.client_id)
        if workflow["missing_facts"]:
            state.status = RunStatus.AWAITING_INFORMATION
            state.missing_facts = workflow["missing_facts"]
            state.questions = workflow["questions"]
            state.error_code = "INFORMATION_REQUIRED"
            self.repository.save_state(state, "run_waiting_for_information", {"missing_facts": state.missing_facts})
            return state.model_dump(mode="json")

        state.plan_version = max(1, state.plan_version)
        if len(self.PLAN) > state.max_steps:
            state.status = RunStatus.FAILED
            state.error_code = "BUDGET_EXCEEDED"
            state.blocked_reason = "动态计划超过最大步骤预算"
            self.repository.save_state(state, "run_budget_exceeded", {"budget": "steps"})
            return state.model_dump(mode="json")
        step_ids = self.repository.create_plan_steps(state, self.PLAN)
        state.current_step_index = 0
        state.current_step_id = step_ids[0]
        state.missing_facts = []
        state.questions = []
        state.error_code = None
        state.status = RunStatus.EXECUTING
        self.repository.save_state(state, "run_planned", {"plan_version": state.plan_version})
        return state.model_dump(mode="json")

    def _execute(self, raw: Dict) -> Dict:
        state = AgentState.model_validate(raw)
        if state.tool_call_count >= state.max_tool_calls:
            state.status = RunStatus.FAILED
            state.error_code = "BUDGET_EXCEEDED"
            state.blocked_reason = "工具调用次数达到预算上限"
            self.repository.save_state(state, "run_budget_exceeded", {"budget": "tool_calls"})
            return state.model_dump(mode="json")
        step = self.repository.get_step(state.run_id, state.current_step_index + 1)
        state.current_step_id = step.id
        self.repository.set_step_status(state.run_id, step.id, StepStatus.RUNNING)
        definition, handler = self.registry.get(step.tool_name)
        arguments = {"matter_id": state.matter_id, "client_id": state.client_id}
        call_id = f"tool_{uuid.uuid4().hex}"
        result = handler(call_id, arguments, 1)
        state.tool_call_count += 1
        result = self._verify_result(state, step.tool_name, result)
        self.repository.save_tool_call(state, 1, arguments, result, step.tool_name)
        state.tool_result_ids.append(call_id)
        if not result.success:
            self.repository.set_step_status(state.run_id, step.id, StepStatus.FAILED, result.error_code)
            state.final_output = result.data
            state.error_code = result.error_code
            state.blocked_reason = result.error_message or (result.warnings[0] if result.warnings else "工具验证失败")
            state.status = RunStatus.BLOCKED_AUTHORITY if result.error_code == "AUTHORITY_REQUIRED" else RunStatus.FAILED
            self.repository.save_state(state, "run_blocked", {"tool_name": step.tool_name, "error_code": result.error_code})
            return state.model_dump(mode="json")

        self.repository.set_step_status(state.run_id, step.id, StepStatus.COMPLETED)
        state.final_output = {**(state.final_output or {}), step.tool_name: result.data}
        state.current_step_index += 1
        if step.tool_name == "analyze_labor_dispute":
            state.pending_approval_id = self.repository.create_approval(
                state, result.data.get("approval_prompt", "是否确认生成劳动仲裁申请书草稿？"),
            )
            state.status = RunStatus.AWAITING_APPROVAL
            self.repository.save_state(state, "run_paused_for_approval")
            return state.model_dump(mode="json")
        next_step = self.repository.get_step(state.run_id, state.current_step_index + 1)
        state.current_step_id = next_step.id
        self.repository.save_state(state, "run_step_advanced", {"next_step_id": next_step.id})
        return state.model_dump(mode="json")

    def _draft(self, raw: Dict) -> Dict:
        state = AgentState.model_validate(raw)
        if state.tool_call_count >= state.max_tool_calls:
            state.status = RunStatus.FAILED
            state.error_code = "BUDGET_EXCEEDED"
            state.blocked_reason = "工具调用次数达到预算上限"
            self.repository.save_state(state, "run_budget_exceeded", {"budget": "tool_calls"})
            return state.model_dump(mode="json")
        step = self.repository.get_step(state.run_id, 3)
        state.current_step_id = step.id
        self.repository.set_step_status(state.run_id, step.id, StepStatus.RUNNING)
        _definition, handler = self.registry.get(step.tool_name)
        arguments = {"matter_id": state.matter_id, "client_id": state.client_id}
        call_id = f"tool_{uuid.uuid4().hex}"
        result = handler(call_id, arguments, 1)
        state.tool_call_count += 1
        result = self._verify_result(state, step.tool_name, result)
        self.repository.save_tool_call(state, 1, arguments, result, step.tool_name)
        state.tool_result_ids.append(call_id)
        if not result.success:
            self.repository.set_step_status(state.run_id, step.id, StepStatus.FAILED, result.error_code)
            state.status = RunStatus.FAILED
            state.error_code = result.error_code
            self.repository.save_state(state, "run_failed")
            return state.model_dump(mode="json")
        self.repository.set_step_status(state.run_id, step.id, StepStatus.COMPLETED)
        state.final_output = {**(state.final_output or {}), step.tool_name: result.data}
        state.final_artifact_ids.append(result.data["artifact_id"])
        state.pending_approval_id = None
        state.status = RunStatus.COMPLETED
        state.error_code = None
        self.repository.save_state(state, "run_completed", {"artifact_id": result.data["artifact_id"]})
        return state.model_dump(mode="json")

    def invoke(self, state: AgentState) -> AgentState:
        return AgentState.model_validate(self.compiled.invoke(state.model_dump(mode="json")))

    def _verify_result(self, state: AgentState, tool_name: str, result):
        """把统一验证报告折叠回 ToolResult，确保失败同样进入 ToolCall 审计。"""
        if not result.success:
            return result
        report = self.verifier.verify(tool_name, result, state)
        result.warnings.extend(report.risk_warnings)
        if report.valid:
            return result
        result.success = False
        result.error_code = "VERIFICATION_FAILED"
        result.error_message = "；".join(report.errors)
        result.retryable = False
        return result
