"""法律 Agent 系统门面。

Flask Router 只依赖本模块，不直接感知 LangGraph 节点、仓储或具体工具，
从而保证后续替换 Runtime 实现时不会影响接口层。
"""

import uuid
from typing import Optional

from .runtime.graph import AgentGraph
from .runtime.persistence import AgentRepository
from .runtime.registry import ToolRegistry
from .runtime.runtime import AgentRuntime
from .tools import register_authority_tools, register_labor_tools, register_material_tools, register_mock_tools
from .matters import MaterialService
from .jurisdictions.authorities import LegalAuthorityService
from .jurisdictions import MatterJurisdictionService, get_jurisdiction_registry


class LegalAgentFacade:
    """组装 Agent Runtime，并向外提供稳定的任务用例。"""

    def __init__(self) -> None:
        # 每个门面实例都使用无状态仓储；运行状态统一从 PostgreSQL 恢复。
        self.repository = AgentRepository()
        self.materials = MaterialService()
        self.authorities = LegalAuthorityService()
        self.jurisdictions = MatterJurisdictionService()
        self.registry = ToolRegistry()
        register_mock_tools(self.registry)
        register_material_tools(self.registry, self.materials)
        register_authority_tools(self.registry, self.authorities)
        register_labor_tools(self.registry)
        self.runtime = AgentRuntime(self.repository, AgentGraph(self.repository, self.registry))

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

    def add_material(self, matter_id: str, client_id: str, filename: str, text: str, media_type: str):
        """向当前客户端所属 Matter 添加授权材料。"""
        return self.materials.ingest_text(matter_id, client_id, filename, text, media_type)

    def create_matter(self, client_id: str, goal: str):
        """创建阶段 2 材料工作区，不执行阶段 1 模拟任务。"""
        return self.materials.create_matter(client_id, goal)

    def extract_material_facts(self, matter_id: str, client_id: str, document_id: str):
        """提取带材料位置引用的候选事实。"""
        return self.materials.extract_facts(matter_id, client_id, document_id)

    def build_matter_timeline(self, matter_id: str, client_id: str):
        """根据已定位事实构建基础时间线。"""
        return self.materials.build_timeline(matter_id, client_id)

    def get_evidence_checklist(self, matter_id: str, client_id: str):
        """生成当前 Matter 的材料/证据概览。"""
        return self.materials.evidence_checklist(matter_id, client_id)

    def register_authority(self, data):
        """登记来源适配器提供的结构化法律来源。"""
        return self.authorities.register(data)

    def verify_authority(self, authority_id: str, effective_at, country_code: str):
        """验证引用在指定法域和日期是否可作为确定依据。"""
        return self.authorities.verify(authority_id, effective_at, country_code)

    @staticmethod
    def list_jurisdictions():
        """返回当前已注册法域的能力声明。"""
        return [package.__dict__ for package in get_jurisdiction_registry().list_packages()]

    def confirm_jurisdiction(self, matter_id: str, client_id: str, data):
        """为 Matter 保存用户明确确认的适用法域上下文。"""
        return self.jurisdictions.confirm(matter_id, client_id, data)

    def list_matters(self, client_id: str):
        """列出当前客户端可恢复的案件工作区。"""
        return self.materials.list_matters(client_id)

    def get_matter(self, matter_id: str, client_id: str):
        """读取案件及其已确认法域。"""
        return self.materials.get_matter(matter_id, client_id)

    def delete_matter(self, matter_id: str, client_id: str):
        """删除 Matter 及其材料、事实和法域数据。"""
        self.materials.delete_matter(matter_id, client_id)
        return {"matter_id": matter_id}

    def calculate_labor_compensation(self, matter_id: str, client_id: str, data):
        """通过统一注册中心调用真实劳动补偿工具。"""
        # 真实法律工具必须在用户确认法域后执行，且当前工具只声明支持 CN。
        jurisdiction = self.materials.get_confirmed_jurisdiction(matter_id, client_id)
        if jurisdiction["country_code"] != "CN":
            raise ValueError("劳动补偿工具当前只支持中国法域")
        _definition, handler = self.registry.get("calculate_labor_compensation")
        result = handler(f"tool_{uuid.uuid4().hex}", data, 1)
        return result.model_dump(mode="json")


_facade = None


def get_legal_agent_facade() -> LegalAgentFacade:
    """获取进程内共享门面；真实任务状态不依赖该单例存活。"""
    global _facade
    if _facade is None:
        _facade = LegalAgentFacade()
    return _facade
