"""劳动纠纷 Runtime 用例层，统一处理启动和多种用户继续动作。
    负责：
    启动劳动纠纷Run
    复用未完成Run
    补充事实后恢复
    确认法域后恢复
    法律来源重试
    审批通过或拒绝

    用户操作”和“状态机”之间的协调层
"""

from .enums import ErrorCode, RunStatus
from .errors import AgentRuntimeError
from .locks import RunExecutionLock


class LaborDisputeRuntime:
    TASK_TYPE = "cn_labor_dispute"

    def __init__(self, repository, graph, labor_disputes, jurisdictions, authority_sync=None) -> None:
        self.repository = repository
        self.graph = graph
        self.labor_disputes = labor_disputes
        self.jurisdictions = jurisdictions
        self.authority_sync = authority_sync
        self.execution_lock = RunExecutionLock()

    def start(self, matter_id: str, client_id: str, facts=None):
        """
        启动一个案件处理流程
        参数:
            matter_id (str): 案件ID
            client_id (str): 客户ID
            facts (dict, optional): 案件事实信息，默认为None
        返回:
            dict: 案件处理流程的快照信息
        """
    # 如果提供了facts信息，则更新案件事实
        updated = self.labor_disputes.update_facts(matter_id, client_id, facts) if facts else None
    # 查找当前案件的活动运行状态
        state = self.repository.find_or_create_active_run(matter_id, client_id, self.TASK_TYPE)
    # 如果状态为等待信息状态且提供了更新的事实信息
        if state.status == RunStatus.AWAITING_INFORMATION.value and updated is not None:
        # 将状态更新为重新规划状态
            state.status = RunStatus.REPLANNING
        # 清空问题和缺失事实列表
            state.questions = []
            state.missing_facts = []
        # 清空错误代码
            state.error_code = None
        # 保存状态变更，记录为"run_resumed"操作
            self.repository.save_state(state, "run_resumed", {"action": "provide_information"})
    # 如果状态为权限阻塞状态
        elif state.status == RunStatus.BLOCKED_AUTHORITY.value:
        # 将状态更新为重新规划状态
            state.status = RunStatus.REPLANNING
        # 清空阻塞原因
            state.blocked_reason = None
        # 清空错误代码
            state.error_code = None
        # 保存状态变更，记录为"run_retry_requested"操作
            self.repository.save_state(state, "run_retry_requested")
    # 调用图处理流程
        try:
            with self.execution_lock.acquire(state.run_id):
                self.graph.invoke(state)
        except AgentRuntimeError as exc:
            if exc.code != "RUN_BUSY":
                raise
    # 返回案件处理流程的快照信息
        return self.repository.snapshot(state.run_id, client_id)

    def continue_run(self, run_id: str, client_id: str, action: str, payload=None, idempotency_key=None):
        with self.execution_lock.acquire(run_id):
            return self._continue_run_locked(run_id, client_id, action, payload, idempotency_key)

    def _continue_run_locked(self, run_id: str, client_id: str, action: str, payload=None, idempotency_key=None):
        state = self.repository.load_state(run_id, client_id)
        payload = payload or {}
        if idempotency_key:
            cached = self.repository.begin_action(run_id, idempotency_key, action, payload)
            if cached is not None:
                return cached
        if state.task_type != self.TASK_TYPE:
            raise AgentRuntimeError("该接口只处理劳动纠纷任务", ErrorCode.INVALID_STATE.value)
        if action == "provide_information":
            if state.status != RunStatus.AWAITING_INFORMATION.value:
                raise AgentRuntimeError("任务当前不在等待补充事实状态", ErrorCode.INVALID_STATE.value)
            self.labor_disputes.update_facts(state.matter_id, client_id, payload)
            state.status = RunStatus.REPLANNING
        elif action == "confirm_jurisdiction":
            if state.status != RunStatus.AWAITING_JURISDICTION.value:
                raise AgentRuntimeError("任务当前不在等待法域状态", ErrorCode.INVALID_STATE.value)
            self.jurisdictions.confirm(state.matter_id, client_id, payload)
            state.status = RunStatus.REPLANNING
        elif action == "approve":
            if state.status != RunStatus.AWAITING_APPROVAL.value or not isinstance(payload.get("approved"), bool):
                raise AgentRuntimeError("任务当前不能执行该审批", ErrorCode.INVALID_STATE.value)
            self.repository.decide_approval(state, payload["approved"])
            if not payload["approved"]:
                self.repository.cancel(state)
                response = self.repository.snapshot(run_id, client_id)
                if idempotency_key:
                    self.repository.finish_action(run_id, idempotency_key, response)
                return response
            state.approved = True
        elif action == "retry_authority":
            if state.status != RunStatus.BLOCKED_AUTHORITY.value:
                raise AgentRuntimeError("任务当前不需要重试法律来源", ErrorCode.INVALID_STATE.value)
            # “重新验证”必须先刷新可信来源，不能只把同一失败计划再跑一次。
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
            state.status = RunStatus.REPLANNING
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
