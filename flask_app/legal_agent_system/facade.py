"""法律 Agent 系统门面。

Flask Router 只依赖本模块，不直接感知 LangGraph 节点、仓储或具体工具，
从而保证后续替换 Runtime 实现时不会影响接口层。
"""

from typing import Optional

from .runtime.graph import AgentGraph
from .runtime.persistence import AgentRepository
from .runtime.registry import ToolRegistry
from .runtime.runtime import AgentRuntime
from .tools import register_mock_tools


class LegalAgentFacade:
    """组装 Agent Runtime，并向外提供稳定的任务用例。"""

    def __init__(self) -> None:
        # 每个门面实例都使用无状态仓储；运行状态统一从 PostgreSQL 恢复。
        self.repository = AgentRepository()
        registry = ToolRegistry()
        register_mock_tools(registry)
        self.runtime = AgentRuntime(self.repository, AgentGraph(self.repository, registry))

    def start_run(self, goal: str, client_id: str, session_id: Optional[str] = None):
        """创建并执行任务，直到完成、失败或进入等待用户状态。"""
        return self.runtime.start(goal, client_id, session_id)

    def get_run(self, run_id: str, client_id: str):
        """返回指定客户端可见的任务快照。"""
        return self.repository.snapshot(run_id, client_id)

    def resume_run(self, run_id: str, client_id: str, approved: bool):
        """提交审批决定，并从持久化状态恢复任务。"""
        return self.runtime.resume(run_id, client_id, approved)

    def cancel_run(self, run_id: str, client_id: str):
        """取消任务及其当前步骤。"""
        state = self.repository.load_state(run_id, client_id)
        self.repository.cancel(state)
        return self.repository.snapshot(run_id, client_id)

    def get_audit(self, run_id: str, client_id: str):
        """读取面向用户和运维的审计事件，不暴露模型思维链。"""
        return self.repository.audit_events(run_id, client_id)


_facade = None


def get_legal_agent_facade() -> LegalAgentFacade:
    """获取进程内共享门面；真实任务状态不依赖该单例存活。"""
    global _facade
    if _facade is None:
        _facade = LegalAgentFacade()
    return _facade
