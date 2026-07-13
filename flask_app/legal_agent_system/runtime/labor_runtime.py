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


class LaborDisputeRuntime:
    TASK_TYPE = "cn_labor_dispute"

    def __init__(self, repository, graph, labor_disputes, jurisdictions) -> None:
        self.repository = repository
        self.graph = graph
        self.labor_disputes = labor_disputes
        self.jurisdictions = jurisdictions

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
        state = self.repository.find_active_run(matter_id, client_id, self.TASK_TYPE)
    # 如果没有找到活动运行状态，则创建一个新的运行状态
        if state is None:
            state = self.repository.create_run_for_matter(matter_id, client_id, self.TASK_TYPE)
    # 如果状态为等待信息状态且提供了更新的事实信息
        elif state.status == RunStatus.AWAITING_INFORMATION.value and updated is not None:
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
        self.graph.invoke(state)
    # 返回案件处理流程的快照信息
        return self.repository.snapshot(state.run_id, client_id)

    def continue_run(self, run_id: str, client_id: str, action: str, payload=None):
        state = self.repository.load_state(run_id, client_id)
        payload = payload or {}
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
                return self.repository.snapshot(run_id, client_id)
            state.approved = True
        elif action == "retry_authority":
            if state.status != RunStatus.BLOCKED_AUTHORITY.value:
                raise AgentRuntimeError("任务当前不需要重试法律来源", ErrorCode.INVALID_STATE.value)
            state.status = RunStatus.REPLANNING
            state.blocked_reason = None
        else:
            raise AgentRuntimeError("不支持的继续动作", ErrorCode.UNSUPPORTED_ACTION.value)
        state.error_code = None
        state.questions = []
        self.repository.save_state(state, "run_resumed", {"action": action})
        self.graph.invoke(state)
        return self.repository.snapshot(run_id, client_id)
