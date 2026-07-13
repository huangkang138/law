from .enums import ErrorCode, RunStatus
from .errors import AgentRuntimeError


class AgentRuntime:
    """协调持久化仓储与 LangGraph，不包含具体法律业务。"""
    def __init__(self, repository, graph) -> None:
        self.repository = repository
        self.graph = graph

    def start(self, goal: str, client_id: str, session_id=None):
        """创建运行并推进状态图，返回数据库中的最新快照。"""
        goal = goal.strip() if isinstance(goal, str) else ""
        if not goal:
            raise AgentRuntimeError("任务目标不能为空", ErrorCode.INVALID_INPUT.value)
        state = self.repository.create_run(goal, client_id, session_id)
        # 图执行结果会在每个关键节点写回数据库，因此这里只需读取最终快照。
        self.graph.invoke(state)#
        return self.repository.snapshot(state.run_id, client_id)

    def resume(self, run_id: str, client_id: str, approved: bool):
        """处理用户审批；确认后继续执行，拒绝后安全取消。"""
        state = self.repository.load_state(run_id, client_id)
        if state.status != RunStatus.AWAITING_APPROVAL.value:
            raise AgentRuntimeError("当前任务不在等待审批状态", ErrorCode.INVALID_STATE.value)
        # 先持久化审批决定，避免任务完成但审批记录仍为 pending。
        self.repository.decide_approval(state, approved)
        if not approved:
            return self.repository.cancel(state) and self.repository.snapshot(run_id, client_id)
        state.approved = True
        self.repository.save_state(state, "run_resumed")
        self.graph.invoke(state)
        return self.repository.snapshot(run_id, client_id)
"""Agent Runtime 用例层，负责启动、暂停后的恢复和输入校验。"""
