"""通用 Runtime 用例层；旧劳动入口通过 task_type 别名兼容接入。
    通用任务用例层；创建/恢复 Run，处理用户继续动作。
"""
import logging

from .enums import ErrorCode, RunStatus, StepStatus
from .errors import AgentRuntimeError
from .locks import RunExecutionLock


class CapabilityRuntime:
    def __init__(self, repository, graph, labor_disputes, jurisdictions, capability_registry, authority_sync=None) -> None:
        self.repository = repository
        self.graph = graph
        self.labor_disputes = labor_disputes
        self.jurisdictions = jurisdictions
        self.capability_registry = capability_registry
        self.authority_sync = authority_sync
        self.execution_lock = RunExecutionLock()

    def start(self, matter_id: str, client_id: str, task_type: str, facts=None):
        logging.info("start() run for matter_id: %s, client_id: %s, task_type: %s", matter_id, client_id, task_type)
        self.capability_registry.resolve(task_type)
        updated = self.labor_disputes.update_facts(matter_id, client_id, facts) if facts else None
        logging.info("find_or_create_active_run查找或创建 Run")
        state = self.repository.find_or_create_active_run(matter_id, client_id, task_type)
        if state.status == RunStatus.AWAITING_INFORMATION.value and updated is not None:
            state.status = RunStatus.REPLANNING
            state.replan_reason = "用户补充或修正了劳动案件事实"
            state.questions = []
            state.missing_facts = []
            state.error_code = None
            self.repository.save_state(state, "run_resumed", {"action": "provide_information"})
        try:
            with self.execution_lock.acquire(state.run_id):
                self.graph.invoke(state)
        except AgentRuntimeError as exc:
            if exc.code != "RUN_BUSY":
                raise
        return self.repository.snapshot(state.run_id, client_id)

    def continue_run(self, run_id: str, client_id: str, action: str, payload=None, idempotency_key=None):
        with self.execution_lock.acquire(run_id):
            return self._continue_run_locked(run_id, client_id, action, payload, idempotency_key)

    def _continue_run_locked(self, run_id: str, client_id: str, action: str, payload=None, idempotency_key=None):
        state = self.repository.load_state(run_id, client_id)
        payload = payload or {}
        self.capability_registry.resolve(state.task_type)
        if idempotency_key:
            cached = self.repository.begin_action(run_id, idempotency_key, action, payload)
            if cached is not None:
                return cached
        if action == "provide_information":
            if state.status != RunStatus.AWAITING_INFORMATION.value:
                raise AgentRuntimeError("任务当前不在等待补充事实状态", ErrorCode.INVALID_STATE.value)
            self.labor_disputes.update_facts(state.matter_id, client_id, payload)
            state.status = RunStatus.REPLANNING
            state.replan_reason = "用户补充或修正了劳动案件事实"
            state.current_step_index = 0
        elif action == "confirm_jurisdiction":
            if state.status != RunStatus.AWAITING_JURISDICTION.value:
                raise AgentRuntimeError("任务当前不在等待法域状态", ErrorCode.INVALID_STATE.value)
            self.jurisdictions.confirm(state.matter_id, client_id, payload)
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
