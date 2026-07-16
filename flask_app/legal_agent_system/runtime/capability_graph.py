"""方案 C 唯一通用 Runtime Graph；只负责上下文、计划和单 Step 执行循环。

task_type 路由由 CapabilityRuntime 在进入 Graph 前完成。
"""

from datetime import datetime, timezone
from typing import Dict

from langgraph.graph import END, StateGraph

from legal_agent_system.capabilities import TemplatePlanBuilder

from .decision_router import DecisionRouter
from .enums import RunStatus, StepStatus
from .errors import AgentRuntimeError
from .executor import PolicyToolExecutor
from .schemas import AgentState, ToolResult
from .verifier import LayeredVerifier


class CapabilityRuntimeGraph:
    NODE_NAMES = {
        "dispatch", "ensure_context", "build_plan", "select_next_step",
        "execute_step", "observe_step", "verify_step", "decide_step",
    }

    def __init__(self, repository, tool_registry, capability_registry) -> None:
        self.repository = repository
        self.tool_registry = tool_registry
        self.capability_registry = capability_registry
        self.plan_builder = TemplatePlanBuilder()
        self.executor = PolicyToolExecutor()
        self.verifier = LayeredVerifier()
        self.decision_router = DecisionRouter()

        graph = StateGraph(dict)
        graph.add_node("dispatch", lambda state: state)
        graph.add_node("ensure_context", self._ensure_context)
        graph.add_node("build_plan", self._build_plan)
        graph.add_node("select_next_step", self._select_next_step)
        graph.add_node("execute_step", self._execute_step)
        graph.add_node("observe_step", self._observe_step)
        graph.add_node("verify_step", self._verify_step)
        graph.add_node("decide_step", self._decide_step)
        graph.set_entry_point("dispatch")
        graph.add_conditional_edges("dispatch", self._dispatch_route, {
            "ensure_context": "ensure_context",
            "select_next_step": "select_next_step",
            "execute_step": "execute_step",
            "observe_step": "observe_step",
            "verify_step": "verify_step",
            "decide_step": "decide_step",
            "stop": END,
        })
        graph.add_conditional_edges("ensure_context", self._after_context, {"build_plan": "build_plan", "stop": END})
        graph.add_conditional_edges("build_plan", self._after_plan, {"select_next_step": "select_next_step", "stop": END})
        graph.add_conditional_edges("select_next_step", self._after_select, {
            "select_next_step": "select_next_step", "execute_step": "execute_step", "stop": END,
        })
        graph.add_conditional_edges("execute_step", self._after_execute, {"observe_step": "observe_step", "stop": END})
        graph.add_edge("observe_step", "verify_step")
        graph.add_edge("verify_step", "decide_step")
        graph.add_conditional_edges("decide_step", self._after_decision, {
            "select_next_step": "select_next_step", "execute_step": "execute_step", "stop": END,
        })
        self.compiled = graph.compile()

    @staticmethod
    def _dispatch_route(raw: Dict) -> str:

        """
        根据运行状态字典返回相应的路由指令

        参数:
            raw (Dict): 包含状态和可能包含批准状态的字典

        返回:
            str: 根据状态返回相应的路由指令字符串
        """
        status = raw["status"]  # 获取状态值
        # 根据不同的状态值返回相应的路由指令
        if status in {RunStatus.PLANNING.value, RunStatus.REPLANNING.value}:
            return "ensure_context"  # 规划或重新规划状态下返回ensure_context
        if status == RunStatus.EXECUTING.value:
            return "select_next_step"  # 执行状态下返回select_next_step
        if status == RunStatus.RETRYING.value:
            return "execute_step"  # 重试状态下返回execute_step
        if status == RunStatus.OBSERVING.value:
            return "observe_step"  # 观察状态下返回observe_step
        if status == RunStatus.VERIFYING.value:
            return "verify_step"  # 验证状态下返回verify_step
        if status == RunStatus.DECIDING.value:
            return "decide_step"  # 决策状态下返回decide_step
        if status == RunStatus.AWAITING_APPROVAL.value and raw.get("approved") is True:
            return "select_next_step"  # 等待批准且已批准状态下返回select_next_step
        return "stop"  # 其他情况返回stop

    @staticmethod
    def _after_context(raw: Dict) -> str:
        return "build_plan" if raw["status"] == RunStatus.PLANNING.value else "stop"

    @staticmethod
    def _after_plan(raw: Dict) -> str:
        return "select_next_step" if raw["status"] == RunStatus.EXECUTING.value else "stop"

    @staticmethod
    def _after_select(raw: Dict) -> str:
        action = (raw.get("last_decision") or {}).get("action")
        if action == "skip_step":
            return "select_next_step"
        if action == "execute_step":
            return "execute_step"
        return "stop"

    @staticmethod
    def _after_execute(raw: Dict) -> str:
        return "observe_step" if raw["status"] == RunStatus.OBSERVING.value else "stop"

    @staticmethod
    def _after_decision(raw: Dict) -> str:
        action = (raw.get("last_decision") or {}).get("action")
        if action == "next_step":
            return "select_next_step"
        if action == "retry_step":
            return "execute_step"
        return "stop"

    def _ensure_context(self, raw: Dict) -> Dict:
        state = AgentState.model_validate(raw)
        assessment = self._adapter(state).assess_context(state)
        if assessment.outcome == "awaiting_jurisdiction":
            state.status = RunStatus.AWAITING_JURISDICTION
            state.questions = assessment.questions
            state.error_code = assessment.error_code
            self.repository.save_state(state, "run_waiting_for_jurisdiction")
            return state.model_dump(mode="json")
        if assessment.outcome == "human_handoff":
            state.status = RunStatus.HUMAN_HANDOFF
            state.blocked_reason = assessment.blocked_reason
            state.error_code = assessment.error_code
            self.repository.save_state(state, "run_handoff_required")
            return state.model_dump(mode="json")
        if assessment.outcome == "awaiting_information":
            state.status = RunStatus.AWAITING_INFORMATION
            state.missing_facts = assessment.missing_facts
            state.questions = assessment.questions
            state.error_code = assessment.error_code
            self.repository.save_state(state, "run_waiting_for_information", {"missing_facts": state.missing_facts})
            return state.model_dump(mode="json")
        if assessment.outcome != "ready":
            raise AgentRuntimeError(f"未知领域上下文结果: {assessment.outcome}", "INVALID_DOMAIN_CONTEXT")
        state.status = RunStatus.PLANNING
        state.missing_facts = []
        state.questions = []
        state.error_code = None
        return state.model_dump(mode="json")

    def _build_plan(self, raw: Dict) -> Dict:
        state = AgentState.model_validate(raw)
        adapter = self._adapter(state)
        template = self.capability_registry.get_template(state.template_id)
        workflow = adapter.get_workflow(state)
        revision = self.plan_builder.build(
            template,
            workflow,
            requested_task_type=state.task_type,
            replan_reason=state.replan_reason,
            triggered_by="runtime",
        )
        revision = adapter.customize_plan(revision, workflow)
        if len(revision.steps) > state.max_steps:
            state.status = RunStatus.FAILED
            state.error_code = "BUDGET_EXCEEDED"
            state.blocked_reason = "动态计划超过最大步骤预算"
            self.repository.save_state(state, "run_budget_exceeded", {"budget": "steps"})
            return state.model_dump(mode="json")
        step_ids = self.repository.persist_plan_revision(state, revision)
        state.current_step_index = 0
        state.current_step_id = step_ids[0] if step_ids else None
        state.status = RunStatus.EXECUTING
        state.last_decision = None
        state.last_tool_result = None
        state.last_observation = None
        state.last_verification = None
        self.repository.save_state(state, "run_planned", {
            "plan_id": state.plan_id,
            "plan_revision": state.plan_revision,
            "template_id": state.template_id,
        })
        return state.model_dump(mode="json")

    def _select_next_step(self, raw: Dict) -> Dict:
        state = AgentState.model_validate(raw)
        try:
            step = self.repository.get_step(state.run_id, state.current_step_index + 1, state.plan_revision)
        except AgentRuntimeError:
            state.status = RunStatus.COMPLETED
            state.current_step_id = None
            state.last_decision = {"action": "finish", "reason": "plan_exhausted"}
            self.repository.save_state(state, "run_completed")
            return state.model_dump(mode="json")
        state.current_step_id = step.id
        if step.status == StepStatus.SKIPPED.value:
            state.current_step_index += 1
            state.last_decision = {"action": "skip_step", "reason": step.skip_reason}
            self.repository.save_step_runtime(state.run_id, step.id, decision=state.last_decision)
            self.repository.save_state(state, "run_step_skipped", {"step_id": step.id, "skip_reason": step.skip_reason})
            return state.model_dump(mode="json")
        if step.requires_approval and state.approved is not True:
            if not state.pending_approval_id:
                state.pending_approval_id = self.repository.create_approval(
                    state, f"是否确认执行高风险步骤：{step.name}？",
                )
            self.repository.set_step_status(state.run_id, step.id, StepStatus.AWAITING_APPROVAL)
            state.status = RunStatus.AWAITING_APPROVAL
            state.last_decision = {"action": "require_approval", "reason": "step_requires_approval"}
            self.repository.save_step_runtime(state.run_id, step.id, decision=state.last_decision)
            self.repository.save_state(state, "run_paused_for_approval")
            return state.model_dump(mode="json")
        state.last_decision = {"action": "execute_step", "reason": "step_selected"}
        state.status = RunStatus.EXECUTING
        return state.model_dump(mode="json")

    def _execute_step(self, raw: Dict) -> Dict:
        state = AgentState.model_validate(raw)
        if self._over_budget(state) or state.tool_call_count >= state.max_tool_calls:
            state.status = RunStatus.FAILED
            state.error_code = "BUDGET_EXCEEDED"
            state.blocked_reason = "工具调用次数达到预算上限"
            self.repository.save_state(state, "run_budget_exceeded", {"budget": "tool_calls"})
            return state.model_dump(mode="json")
        step = self.repository.get_step(state.run_id, state.current_step_index + 1, state.plan_revision)
        self.repository.set_step_status(state.run_id, step.id, StepStatus.RUNNING)
        definition, handler = self.tool_registry.get(step.tool_name)
        adapter = self._adapter(state)
        arguments = adapter.tool_arguments(state, step)
        result = self.executor.execute(
            definition, handler, arguments, adapter.jurisdiction_code(state), state.approved is True,
        )
        state.tool_call_count += 1
        self._record_usage(state, result)
        state.tool_result_ids.append(result.tool_call_id)
        state.last_tool_result = result.model_dump(mode="json")
        self.repository.save_tool_call(state, state.retry_count + 1, arguments, result, step.tool_name)
        state.status = RunStatus.OBSERVING
        self.repository.save_state(state, "step_executed", {"step_id": step.id, "tool_call_id": result.tool_call_id})
        return state.model_dump(mode="json")

    def _observe_step(self, raw: Dict) -> Dict:
        state = AgentState.model_validate(raw)
        result = ToolResult.model_validate(state.last_tool_result)
        observation = {
            "tool_call_id": result.tool_call_id,
            "success": result.success,
            "data": result.data,
            "evidence_refs": result.evidence_refs,
            "authority_refs": result.authority_refs,
            "assumptions": result.assumptions,
            "warnings": result.warnings,
            "error_code": result.error_code,
            "retryable": result.retryable,
        }
        state.last_observation = observation
        state.status = RunStatus.VERIFYING
        self.repository.save_step_runtime(state.run_id, state.current_step_id, observation=observation)
        self.repository.save_state(state, "step_observed", {"step_id": state.current_step_id})
        return state.model_dump(mode="json")

    def _verify_step(self, raw: Dict) -> Dict:
        state = AgentState.model_validate(raw)
        step = self.repository.get_step(state.run_id, state.current_step_index + 1, state.plan_revision)
        result = ToolResult.model_validate(state.last_tool_result)
        verification = self.verifier.verify(
            step.tool_name,
            result,
            state,
            list(step.verification_policy_ids or []),
            self._step_on_failure(state, step.template_step_id),
            self._adapter(state),
        )
        state.last_verification = verification
        state.status = RunStatus.DECIDING
        self.repository.save_step_runtime(state.run_id, step.id, verification=verification)
        self.repository.save_state(state, "step_verified", {"step_id": step.id, "valid": verification["valid"]})
        return state.model_dump(mode="json")

    def _decide_step(self, raw: Dict) -> Dict:
        state = AgentState.model_validate(raw)
        step = self.repository.get_step(state.run_id, state.current_step_index + 1, state.plan_revision)
        result = ToolResult.model_validate(state.last_tool_result)
        on_failure = self._step_on_failure(state, step.template_step_id)
        template = self.capability_registry.get_template(state.template_id)
        decision = self.decision_router.decide(
            result,
            state.last_verification or {},
            on_failure=on_failure,
            has_next_step=state.current_step_index + 1 < len(template.steps),
        )
        if decision["action"] == "retry_step" and state.retry_count >= 1:
            decision = {"action": "handoff", "reason": "consecutive_retry_exhausted"}
        state.last_decision = decision
        self.repository.save_step_runtime(state.run_id, step.id, decision=decision)
        action = decision["action"]
        if action in {"next_step", "finish"}:
            self.repository.set_step_status(state.run_id, step.id, StepStatus.COMPLETED)
            state.final_output = {**(state.final_output or {}), step.tool_name: result.data}
            artifact_id = (result.data or {}).get("artifact_id")
            if artifact_id and artifact_id not in state.final_artifact_ids:
                state.final_artifact_ids.append(artifact_id)
            state.current_step_index += 1
            state.retry_count = 0
            state.approved = None
            state.pending_approval_id = None
            state.status = RunStatus.EXECUTING if action == "next_step" else RunStatus.COMPLETED
            self.repository.save_state(state, "run_step_advanced" if action == "next_step" else "run_completed", {
                "step_id": step.id,
                "decision": action,
                "artifact_id": artifact_id,
            })
        elif action == "retry_step":
            state.retry_count += 1
            state.status = RunStatus.RETRYING
            self.repository.save_state(state, "run_step_retrying", {"step_id": step.id, "retry_count": state.retry_count})
        elif action == "request_context":
            self.repository.set_step_status(state.run_id, step.id, StepStatus.FAILED, result.error_code)
            state.status = RunStatus.AWAITING_INFORMATION
            state.questions = [result.error_message or "请补充完成当前步骤所需的信息。"]
            state.error_code = result.error_code or "INFORMATION_REQUIRED"
            self.repository.save_state(state, "run_waiting_for_information", {"step_id": step.id})
        elif action == "replan":
            self.repository.set_step_status(state.run_id, step.id, StepStatus.FAILED, result.error_code)
            state.status = RunStatus.REPLANNING
            state.replan_reason = decision["reason"]
            self.repository.save_state(state, "run_replan_requested", {"step_id": step.id, "reason": state.replan_reason})
        elif action == "handoff":
            self.repository.set_step_status(state.run_id, step.id, StepStatus.FAILED, result.error_code)
            state.status = RunStatus.HUMAN_HANDOFF
            state.error_code = result.error_code
            state.blocked_reason = result.error_message or "当前步骤需要人工接管"
            self.repository.save_state(state, "run_handoff_required", {"step_id": step.id})
        else:
            self.repository.set_step_status(state.run_id, step.id, StepStatus.FAILED, result.error_code)
            state.status = RunStatus.BLOCKED_AUTHORITY if result.error_code == "AUTHORITY_REQUIRED" else RunStatus.FAILED
            state.error_code = result.error_code or "VERIFICATION_FAILED"
            state.blocked_reason = result.error_message or (result.warnings[0] if result.warnings else "工具或验证失败")
            self.repository.save_state(state, "run_blocked", {"step_id": step.id, "error_code": state.error_code})
        return state.model_dump(mode="json")

    def _step_on_failure(self, state: AgentState, template_step_id: str) -> str:
        template = self.capability_registry.get_template(state.template_id)
        return next(item.on_failure for item in template.steps if item.step_id == template_step_id)

    def _adapter(self, state: AgentState):
        return self.capability_registry.get_adapter(state.domain_id)

    def invoke(self, state: AgentState) -> AgentState:
        if not state.domain_id or not state.template_id or not state.template_version:
            raise AgentRuntimeError(
                "Run 尚未绑定领域和计划模板，请通过 CapabilityRuntime 调用 Graph",
                "CAPABILITY_NOT_RESOLVED",
            )
        return AgentState.model_validate(self.compiled.invoke(state.model_dump(mode="json")))

    @staticmethod
    def _record_usage(state: AgentState, result: ToolResult) -> None:
        usage = (result.data or {}).get("_usage", {}) if result.data else {}
        state.token_usage += int(usage.get("tokens", 0))
        state.cost_cents += int(usage.get("cost_cents", 0))

    @staticmethod
    def _over_budget(state: AgentState) -> bool:
        started = state.started_at if state.started_at.tzinfo else state.started_at.replace(tzinfo=timezone.utc)
        elapsed = (datetime.now(timezone.utc) - started).total_seconds()
        return (
            elapsed >= state.budget_wallclock_seconds
            or state.token_usage >= state.budget_tokens
            or state.cost_cents >= state.budget_cost_cents
        )
