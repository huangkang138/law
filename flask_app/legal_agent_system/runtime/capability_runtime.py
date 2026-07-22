"""通用任务用例层；统一解析能力、创建或恢复 Run，并处理继续动作。"""
import logging

from legal_agent_system.capabilities import ResolvedCapability

from .enums import ErrorCode, RunStatus, StepStatus
from .errors import AgentRuntimeError
from .locks import RunExecutionLock
from .schemas import AgentState


class CapabilityRuntime:
    def __init__(self, repository, graph, capability_registry, authority_sync=None) -> None:
        self.repository = repository
        self.graph = graph
        self.capability_registry = capability_registry
        self.authority_sync = authority_sync
        self.execution_lock = RunExecutionLock()

    def start_task(self, matter_id: str, client_id: str, task_type: str, facts=None):
        """启动通用任务；一次解析能力，并复用同案件的活动 Run。"""
        logging.info("启动 Agent 任务: matter=%s client=%s task=%s", matter_id, client_id, task_type)
        resolved = self.capability_registry.resolve(task_type)#1找到属于哪个领域、使用哪个模板
        adapter = self.capability_registry.get_adapter(resolved.domain.domain_id)
        updated = adapter.prepare_start(matter_id, client_id, facts, task_type)#2保存领域事实
        state = self.repository.find_or_create_active_run(matter_id, client_id, task_type)#3找到或创建任务
        self._bind_capability(state, resolved)
        if state.status == RunStatus.AWAITING_INFORMATION.value and updated:
            state.status = RunStatus.REPLANNING
            state.replan_reason = "用户补充或修正了劳动案件事实"
            state.questions = []
            state.missing_facts = []
            state.error_code = None
            self.repository.save_state(state, "run_resumed", {"action": "provide_information"})
        try:
            with self.execution_lock.acquire(state.run_id):
                self.graph.invoke(state)#4开始执行
        except AgentRuntimeError as exc:
            if exc.code != "RUN_BUSY":
                raise
        return self.repository.snapshot(state.run_id, client_id)

    def start_new_task(self, goal: str, client_id: str, task_type: str, session_id=None):
        """为无需预建 Matter 的兼容入口创建案件并进入同一 Runtime。"""
        goal = goal.strip() if isinstance(goal, str) else ""
        if not goal:
            raise AgentRuntimeError("任务目标不能为空", ErrorCode.INVALID_INPUT.value)
        resolved = self.capability_registry.resolve(task_type)
        state = self.repository.create_run(goal, client_id, session_id, task_type)
        self._bind_capability(state, resolved)
        with self.execution_lock.acquire(state.run_id):
            self.graph.invoke(state)
        return self.repository.snapshot(state.run_id, client_id)

    def start(self, matter_id: str, client_id: str, task_type: str, facts=None):
        """兼容旧调用；新代码使用 start_task。"""
        return self.start_task(matter_id, client_id, task_type, facts)

    def continue_task(self, run_id: str, client_id: str, action: str, payload=None, idempotency_key=None):
        """从持久化状态继续一个通用任务。"""
        with self.execution_lock.acquire(run_id):
            return self._continue_run_locked(run_id, client_id, action, payload, idempotency_key)

    def continue_run(self, run_id: str, client_id: str, action: str, payload=None, idempotency_key=None):
        """兼容旧调用；新代码使用 continue_task。"""
        return self.continue_task(run_id, client_id, action, payload, idempotency_key)

    def _continue_run_locked(self, run_id: str, client_id: str, action: str, payload=None, idempotency_key=None):
        state = self.repository.load_state(run_id, client_id)
        payload = payload or {}
        resolved = self.capability_registry.resolve(state.task_type)
        adapter = self.capability_registry.get_adapter(resolved.domain.domain_id)
        self._bind_capability(state, resolved)
        if idempotency_key:
            cached = self.repository.begin_action(run_id, idempotency_key, action, payload)
            if cached is not None:
                return cached
        if action == "provide_information":
            if state.status != RunStatus.AWAITING_INFORMATION.value:
                raise AgentRuntimeError("任务当前不在等待补充事实状态", ErrorCode.INVALID_STATE.value)
            adapter.provide_information(state, payload)
            state.status = RunStatus.REPLANNING
            state.replan_reason = "用户补充或修正了劳动案件事实"
            state.current_step_index = 0
        elif action == "confirm_jurisdiction":
            if state.status != RunStatus.AWAITING_JURISDICTION.value:
                raise AgentRuntimeError("任务当前不在等待法域状态", ErrorCode.INVALID_STATE.value)
            adapter.confirm_jurisdiction(state, payload)
            state.status = RunStatus.REPLANNING
            state.replan_reason = "用户确认了适用法域"
        elif action == "approve":
            if state.status != RunStatus.AWAITING_APPROVAL.value or not isinstance(payload.get("approved"), bool):
                raise AgentRuntimeError("任务当前不能执行该审批", ErrorCode.INVALID_STATE.value)
            self.repository.decide_approval(state, payload["approved"])
            if not payload["approved"]:
                # 拒绝的是尚未执行的高风险步骤；保留其 pending 状态兼容旧劳动闭环审计语义。
                self.repository.set_step_status(state.run_id, state.current_step_id, StepStatus.PENDING)
                state.status = RunStatus.CANCELLED
                state.error_code = ErrorCode.RUN_CANCELLED.value
                state.approved = False
                self.repository.save_state(state, "run_cancelled", {"reason": "approval_rejected"})
                response = self.repository.snapshot(run_id, client_id)
                if idempotency_key:
                    self.repository.finish_action(run_id, idempotency_key, response)
                return response
            state.approved = True
        elif action == "retry_authority":
            if state.status != RunStatus.BLOCKED_AUTHORITY.value:
                raise AgentRuntimeError("任务当前不需要重试法律来源", ErrorCode.INVALID_STATE.value)
            if self.authority_sync is not None:
                sync_result = self.authority_sync()
                if isinstance(sync_result, dict) and not sync_result.get("ok", True):
                    state.blocked_reason = "官方法源同步失败，请稍后重试或转人工复核"
                    state.error_code = "AUTHORITY_SYNC_FAILED"
                    self.repository.save_state(state, "authority_sync_failed", {"error_code": sync_result.get("error_code")})
                    response = self.repository.snapshot(run_id, client_id)
                    if idempotency_key:
                        self.repository.finish_action(run_id, idempotency_key, response)
                    return response
            self.repository.set_step_status(state.run_id, state.current_step_id, StepStatus.PENDING)
            state.status = RunStatus.RETRYING
            state.blocked_reason = None
        else:
            raise AgentRuntimeError("不支持的继续动作", ErrorCode.UNSUPPORTED_ACTION.value)
        state.error_code = None
        state.questions = []
        self.repository.save_state(state, "run_resumed", {"action": action})
        self.graph.invoke(state)
        response = self.repository.snapshot(run_id, client_id)
        if idempotency_key:
            self.repository.finish_action(run_id, idempotency_key, response)
        return response

    def _bind_capability(self, state: AgentState, resolved: ResolvedCapability) -> None:
        """将解析结果绑定到 Run；Graph 只消费结果，不再重复路由。"""
        default_tool_budget = AgentState.model_fields["max_tool_calls"].default
        if state.max_tool_calls == default_tool_budget:
            state.max_tool_calls = resolved.template.max_tool_calls
        binding = (
            resolved.domain.domain_id,
            resolved.template.template_id,
            resolved.template.version,
        )
        if (state.domain_id, state.template_id, state.template_version) == binding:
            return
        state.domain_id, state.template_id, state.template_version = binding
        self.repository.save_state(state, "task_routed", {
            "domain_id": state.domain_id,
            "task_type": state.task_type,
            "template_id": state.template_id,
            "template_version": state.template_version,
        })
