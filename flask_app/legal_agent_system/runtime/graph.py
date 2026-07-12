import uuid
from typing import Dict

from langgraph.graph import END, StateGraph

from .enums import ErrorCode, RunStatus, StepStatus
from .schemas import AgentState


class AgentGraph:
    """编排规划、工具执行、审批暂停和完成四个核心阶段。"""

    def __init__(self, repository, registry) -> None:
        self.repository = repository
        self.registry = registry
        # 阶段 1 使用 dict 作为 LangGraph 传输格式，边界处统一由 AgentState 校验。
        graph = StateGraph(dict)
        graph.add_node("dispatch", self._dispatch)
        graph.add_node("plan", self._plan)
        graph.add_node("execute", self._execute)
        graph.add_node("finish", self._finish)
        graph.set_entry_point("dispatch")
        graph.add_conditional_edges("dispatch", self._route, {
            "plan": "plan", "execute": "execute", "finish": "finish", "stop": END,
        })
        graph.add_edge("plan", "execute")
        graph.add_edge("execute", END)
        graph.add_edge("finish", END)
        self.compiled = graph.compile()

    @staticmethod
    def _dispatch(state: Dict) -> Dict:
        """恢复入口：保持原状态，由条件边决定下一节点。"""
        return state

    @staticmethod
    def _route(state: Dict) -> str:
        """根据持久化运行状态选择节点，等待和终态均停止执行。"""
        status = state["status"]
        if status == RunStatus.PLANNING.value:
            return "plan"
        if status in {RunStatus.EXECUTING.value, RunStatus.RETRYING.value}:
            return "execute"
        if status == RunStatus.AWAITING_APPROVAL.value and state.get("approved") is True:
            return "finish"
        return "stop"

    def _plan(self, raw: Dict) -> Dict:
        """创建阶段 1 的单个模拟步骤，并进入执行状态。"""
        state = AgentState.model_validate(raw)
        state.current_step_id = self.repository.create_step(state)
        state.status = RunStatus.EXECUTING
        self.repository.save_state(state, "run_planned")
        return state.model_dump(mode="json")

    def _execute(self, raw: Dict) -> Dict:
        """执行白名单工具，按工具声明限制重试次数。"""
        state = AgentState.model_validate(raw)
        definition, handler = self.registry.get("mock_case_summary")
        self.repository.set_step_status(state.run_id, state.current_step_id, StepStatus.RUNNING)
        arguments = {"goal": state.goal, "fail_first_attempt": True}
        # max_retries 不包含首次调用，所以总尝试次数为 max_retries + 1。
        for attempt in range(1, definition.max_retries + 2):
            call_id = f"tool_{uuid.uuid4().hex}"
            result = handler(call_id, arguments, attempt)
            self.repository.save_tool_call(state, attempt, arguments, result)
            state.tool_result_ids.append(call_id)
            if result.success:
                # 模拟工具声明需要审批：结果先保存，任务停在 awaiting_approval。
                state.final_output = result.data
                state.pending_approval_id = self.repository.create_approval(state)
                state.status = RunStatus.AWAITING_APPROVAL
                self.repository.set_step_status(state.run_id, state.current_step_id, StepStatus.AWAITING_APPROVAL)
                self.repository.save_state(state, "run_paused_for_approval")
                return state.model_dump(mode="json")
            state.retry_count = attempt
            state.status = RunStatus.RETRYING
            self.repository.save_state(state, "tool_retry_scheduled", {"attempt": attempt})
            if not result.retryable:
                break
        state.status = RunStatus.FAILED
        state.error_code = ErrorCode.TOOL_RETRY_EXHAUSTED.value
        self.repository.set_step_status(state.run_id, state.current_step_id, StepStatus.FAILED, state.error_code)
        self.repository.save_state(state, "run_failed")
        return state.model_dump(mode="json")

    def _finish(self, raw: Dict) -> Dict:
        """审批通过后完成当前步骤和整次运行。"""
        state = AgentState.model_validate(raw)
        state.status = RunStatus.COMPLETED
        state.pending_approval_id = None
        self.repository.set_step_status(state.run_id, state.current_step_id, StepStatus.COMPLETED)
        self.repository.save_state(state, "run_completed")
        return state.model_dump(mode="json")

    def invoke(self, state: AgentState) -> AgentState:
        """执行状态图，并把图输出重新校验为正式状态对象。"""
        return AgentState.model_validate(self.compiled.invoke(state.model_dump(mode="json")))
"""阶段 1 最小 LangGraph 状态机。"""
