"""法律 Agent 系统门面。

Flask Router 只依赖本模块，不直接感知 LangGraph 节点、仓储或具体工具，
从而保证后续替换 Runtime 实现时不会影响接口层。
"""
import logging
import uuid
from datetime import datetime, timezone
from typing import Optional

from .runtime.persistence import AgentRepository
from .runtime.registry import ToolRegistry
from .runtime.capability_graph import CapabilityRuntimeGraph
from .runtime.capability_runtime import CapabilityRuntime
from .capabilities import CapabilityRegistry
from .domains.labor import LaborDomainRuntimeAdapter, build_labor_domain_package
from .domains.mock import MockDomainRuntimeAdapter, build_mock_domain_package
from .tools import (
    register_authority_verification_tools, register_labor_dispute_tools, register_labor_tools,
    register_labor_triage_tools, register_material_tools, register_mock_tools,
)
from .matters import MaterialService
from .jurisdictions.authorities import LegalAuthorityService
from .jurisdictions.authority_importer import TrustedAuthorityImporter
from .jurisdictions.authority_provider import OfficialCnLaborProvider
from .jurisdictions.authority_governance import AuthorityGovernanceService
from .jurisdictions import MatterJurisdictionService, get_jurisdiction_registry
from .labor_disputes import LaborCaseTriageService, LaborDisputeService, LaborFactSuggestionService
from . import models as _agent_models  # noqa: F401，注册新增 Agent 表元数据


class LegalAgentFacade:
    """组装 Agent Runtime，并向外提供稳定的任务用例。"""

    def __init__(self, llm_fact_extractor=None, auto_sync_authorities: bool = False, authority_provider=None) -> None:
        # 每个门面实例都使用无状态仓储；运行状态统一从 PostgreSQL 恢复。
        self.repository = AgentRepository()
        self.materials = MaterialService()
        self.authorities = LegalAuthorityService()
        self.authority_importer = TrustedAuthorityImporter(self.authorities)
        self.authority_provider = authority_provider or OfficialCnLaborProvider()
        self.authority_governance = AuthorityGovernanceService()
        # 生产门面开启自动同步；测试可显式关闭，继续验证“无来源必须阻断”的安全边界。
        self.auto_sync_authorities = auto_sync_authorities
        self.jurisdictions = MatterJurisdictionService()
        self.labor_disputes = LaborDisputeService(self.materials, self.authorities)
        self.labor_triage = LaborCaseTriageService(self.materials)
        self.labor_suggestions = LaborFactSuggestionService(self.materials, llm_fact_extractor)
        self.registry = ToolRegistry()
        register_mock_tools(self.registry)
        register_material_tools(self.registry, self.materials)
        register_authority_verification_tools(self.registry, self.authorities)
        register_labor_tools(self.registry)
        register_labor_dispute_tools(self.registry, self.labor_disputes)
        register_labor_triage_tools(self.registry, self.labor_triage)
        self.capabilities = CapabilityRegistry(self.registry)
        self.capabilities.register(
            build_labor_domain_package(),
            LaborDomainRuntimeAdapter(
                self.materials, self.labor_disputes, self.labor_triage, self.jurisdictions,
            ),
        )
        self.capabilities.register(build_mock_domain_package(), MockDomainRuntimeAdapter())
        self.capability_runtime = CapabilityRuntime(
            self.repository,
            CapabilityRuntimeGraph(self.repository, self.registry, self.capabilities),
            self.capabilities,
            (lambda: self._try_sync_authorities(
                force=True,
                trigger="task_retry",
                requested_by="runtime",
            )) if auto_sync_authorities else None,
        )

    def start_run(self, goal: str, client_id: str, session_id: Optional[str] = None):
        """兼容阶段 1 HTTP；内部已统一进入 CapabilityRuntime。"""
        return self.capability_runtime.start_new_task(
            goal, client_id, "mock_case_summary", session_id,
        )

    def get_run(self, run_id: str, client_id: str):
        """返回指定客户端可见的任务快照。"""
        return self.repository.snapshot(run_id, client_id)

    def resume_run(self, run_id: str, client_id: str, approved: bool):
        """兼容阶段 1审批 HTTP；内部已统一为结构化 continue action。"""
        return self.continue_task(run_id, client_id, "approve", {"approved": approved})

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

    def create_matter(self, client_id: str, goal: str, session_id: str | None = None):
        """创建阶段 2 材料工作区，不执行阶段 1 模拟任务。"""
        return self.materials.create_matter(client_id, goal, session_id)

    def extract_material_facts(self, matter_id: str, client_id: str, document_id: str):
        """提取带材料位置引用的候选事实。"""
        return self.materials.extract_facts(matter_id, client_id, document_id)

    def build_matter_timeline(self, matter_id: str, client_id: str):
        """根据已定位事实构建基础时间线。"""
        return self.materials.build_timeline(matter_id, client_id)

    def get_evidence_checklist(self, matter_id: str, client_id: str):
        """生成当前 Matter 的材料/证据概览。"""
        return self.materials.evidence_checklist(matter_id, client_id)

    def register_test_authority(self, data):
        """为集成测试注入保留域名来源；不暴露为 HTTP 或 Agent 工具。"""
        return self.authorities.register_test(data)

    def verify_authority(self, authority_id: str, effective_at, country_code: str):
        """验证引用在指定法域和日期是否可作为确定依据。"""
        return self.authorities.verify(authority_id, effective_at, country_code)

    def import_official_labor_authorities(
        self,
        trigger: str = "manual",
        requested_by: str | None = None,
    ):
        """由内部可信 Provider 同步官方法源；不提供公开写入接口。"""
        return self.authority_importer.import_all(
            self.authority_provider,
            trigger=trigger,
            requested_by=requested_by,
        )

    def _try_sync_authorities(
        self,
        force: bool = False,
        trigger: str = "request",
        requested_by: str | None = None,
    ):
        """运行入口的安全同步：失败留痕并交给来源验证状态阻断，不返回 500。"""
        external_ids = [item.external_id for item in getattr(self.authority_provider, "sources", ())]
        if not force and self.authorities.has_fresh_sources(self.authority_provider.name, external_ids):
            return {"ok": True, "skipped": True, "reason": "fresh_cache"}
        try:
            authorities = self.import_official_labor_authorities(
                trigger=trigger,
                requested_by=requested_by,
            )
            health = self.get_authority_health()
            return {
                "ok": health["status"] == "ready",
                "authorities": authorities,
                "health": health,
                "error_code": None if health["status"] == "ready" else "AUTHORITY_COVERAGE_INCOMPLETE",
            }
        except Exception as exc:
            return {"ok": False, "error_code": type(exc).__name__}

    def get_labor_authority_catalog(self):
        """返回劳动纠纷当前可用的官方来源，让用户在运行前也能看到依据。"""
        sync = self._try_sync_authorities(
            trigger="catalog",
            requested_by="http_catalog",
        ) if self.auto_sync_authorities else {"ok": True}
        authorities = self.authorities.search("CN", datetime.now(timezone.utc), [])
        health = self.get_authority_health()
        return {
            "status": health["status"],
            "count": len(authorities),
            "authorities": authorities,
            "sync": sync,
            "governance": health,
        }

    def get_authority_health(self):
        """返回法源覆盖、新鲜度、待复核和最近同步状态。"""
        external_ids = [item.external_id for item in getattr(self.authority_provider, "sources", ())]
        return self.authority_governance.health(self.authority_provider.name, external_ids)

    def list_pending_authority_reviews(self):
        """内部运维读取待复核版本，不暴露原始响应正文。"""
        return self.authority_governance.pending_reviews(self.authority_provider.name)

    def review_authority_version(
        self,
        authority_id: str,
        decision: str,
        reviewer_id: str,
        notes: str | None = None,
    ):
        """内部运维复核入口；每次批准或驳回都写入独立审计记录。"""
        return self.authority_governance.review(
            authority_id,
            decision,
            reviewer_id,
            notes,
        )

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

    def update_labor_dispute_facts(self, matter_id: str, client_id: str, data):
        """保存劳动纠纷事实并返回动态计划与追问。"""
        return self.labor_disputes.update_facts(matter_id, client_id, data)

    def get_labor_dispute_workflow(self, matter_id: str, client_id: str):
        """恢复劳动纠纷闭环状态。"""
        return self.labor_disputes.get_workflow(matter_id, client_id)

    def update_labor_case_triage(self, matter_id: str, client_id: str, data):
        """保存青年就业分流事实并返回劳动关系初筛结果。"""
        return self.labor_triage.update(matter_id, client_id, data)

    def get_labor_case_triage(self, matter_id: str, client_id: str):
        """恢复指定 Matter 的劳动案件分流结果。"""
        return self.labor_triage.get(matter_id, client_id)

    def analyze_labor_dispute(self, matter_id: str, client_id: str):
        """校验事实、期限、证据和法律来源。"""
        return self.labor_disputes.analyze(matter_id, client_id)

    def create_labor_dispute_draft(self, matter_id: str, client_id: str, approved: bool):
        """经用户确认生成劳动仲裁申请书草稿。"""
        return self.labor_disputes.create_draft(matter_id, client_id, approved)

    def start_labor_dispute_run(self, matter_id: str, client_id: str, facts=None, task_type: str = "cn_labor_dispute"):
        """兼容入口；默认映射到 labor_arbitration_application 模板。"""
        return self.start_task(matter_id, client_id, task_type, facts)

    def start_task(self, matter_id: str, client_id: str, task_type: str, facts=None):
        """启动任一已注册任务；Router 新代码统一调用此入口。"""
        logging.info("启动 Agent 任务：%s/%s/%s", matter_id, client_id, task_type)
        if self.auto_sync_authorities:
            self._try_sync_authorities(trigger="task_start", requested_by="runtime")
        return self.capability_runtime.start_task(matter_id, client_id, task_type, facts)

    def start_labor_task(self, matter_id: str, client_id: str, task_type: str, facts=None):
        """兼容旧劳动命名；新代码使用 start_task。"""
        return self.start_task(matter_id, client_id, task_type, facts)

    def list_agent_capabilities(self):
        """返回可查询的领域与模板元数据，不暴露内部处理器。"""
        return [{
            "domain_id": package.domain_id,
            "version": package.version,
            "task_types": [rule.task_type for rule in package.routing_rules],
            "templates": [{
                "template_id": item.template_id,
                "version": item.version,
                "task_type": item.task_type,
            } for item in package.plan_templates],
        } for package in self.capabilities.list_domains()]

    def suggest_labor_dispute_facts(self, matter_id: str, client_id: str):
        """从已授权材料生成带出处候选值，不自动确认或写入案件事实。"""
        self.suggest = self.labor_suggestions.suggest(matter_id, client_id)
        return self.suggest

    def continue_labor_dispute_run(self, run_id: str, client_id: str, action: str, payload=None, idempotency_key=None):
        """兼容旧劳动命名；新代码使用 continue_task。"""
        return self.continue_task(run_id, client_id, action, payload, idempotency_key)

    def continue_task(self, run_id: str, client_id: str, action: str, payload=None, idempotency_key=None):
        """以结构化动作继续任一已注册任务。"""
        return self.capability_runtime.continue_task(run_id, client_id, action, payload, idempotency_key)


_facade = None


def get_legal_agent_facade() -> LegalAgentFacade:
    """获取进程内共享门面；真实任务状态不依赖该单例存活。"""
    global _facade
    if _facade is None:
        # HTTP 生产入口默认准备可信官方法源；重复调用按 provider/external_id/version 幂等复用。
        _facade = LegalAgentFacade(auto_sync_authorities=True)
    return _facade
