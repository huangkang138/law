"""领域、模板、工具声明和验证策略的统一查询入口。"""
import logging
from typing import Dict, List, NamedTuple, Tuple

from .contracts import DomainPackage, PlanTemplate
from .domain_adapter import DomainRuntimeAdapter


class ResolvedCapability(NamedTuple):
    """任务类型解析结果；既可按字段读取，也兼容原有元组解包。"""

    domain: DomainPackage
    template: PlanTemplate


class CapabilityRegistry:
    def __init__(self, tool_registry) -> None:
        self.tool_registry = tool_registry
        self._domains: Dict[str, DomainPackage] = {}
        self._templates: Dict[str, PlanTemplate] = {}
        self._routes: Dict[str, Tuple[str, str]] = {}
        self._adapters: Dict[str, DomainRuntimeAdapter] = {}

    def register(self, package: DomainPackage, adapter: DomainRuntimeAdapter) -> None:
        if package.domain_id in self._domains:
            raise ValueError(f"领域能力包已注册: {package.domain_id}")
        if not isinstance(adapter, DomainRuntimeAdapter):
            raise TypeError("领域适配器未完整实现 DomainRuntimeAdapter")
        if adapter.domain_id != package.domain_id:
            raise ValueError("领域适配器 domain_id 与能力包不一致")
        declared_tools = set(package.tool_names)
        package_templates: Dict[str, PlanTemplate] = {}
        for template in package.plan_templates:
            if template.domain_id != package.domain_id:
                raise ValueError("模板 domain_id 与能力包不一致")
            if template.template_id in self._templates or template.template_id in package_templates:
                raise ValueError(f"计划模板已注册: {template.template_id}")
            for step in template.steps:
                if step.tool_name not in declared_tools:
                    raise ValueError(f"模板使用了未声明工具: {step.tool_name}")
                self.tool_registry.get(step.tool_name)
            package_templates[template.template_id] = template
        package_routes: Dict[str, Tuple[str, str]] = {}
        for rule in package.routing_rules:
            if rule.template_id not in package_templates:
                raise ValueError(f"路由指向未注册模板: {rule.template_id}")
            for task_type in [rule.task_type, *rule.aliases]:
                if task_type in self._routes or task_type in package_routes:
                    raise ValueError(f"任务路由已注册: {task_type}")
                package_routes[task_type] = (package.domain_id, rule.template_id)

        # 所有声明验证完成后再一次性写入，避免注册失败留下半成品。
        self._templates.update(package_templates)
        self._routes.update(package_routes)
        self._domains[package.domain_id] = package
        self._adapters[package.domain_id] = adapter

    def resolve(self, task_type: str) -> ResolvedCapability:
        """将外部 task_type 解析为唯一领域包和计划模板。"""
        logging.info("解析 Agent 任务类型: %s", task_type)
        try:
            domain_id, template_id = self._routes[task_type]
            return ResolvedCapability(
                domain=self._domains[domain_id],
                template=self._templates[template_id],
            )
        except KeyError as exc:
            raise ValueError(f"未注册的 Agent 任务类型: {task_type}") from exc

    def get_template(self, template_id: str) -> PlanTemplate:
        try:
            return self._templates[template_id]
        except KeyError as exc:
            raise ValueError(f"计划模板不存在: {template_id}") from exc

    def get_adapter(self, domain_id: str) -> DomainRuntimeAdapter:
        try:
            return self._adapters[domain_id]
        except KeyError as exc:
            raise ValueError(f"领域运行适配器不存在: {domain_id}") from exc

    def list_domains(self) -> List[DomainPackage]:
        return list(self._domains.values())

    def list_templates(self, domain_id: str | None = None) -> List[PlanTemplate]:
        templates = list(self._templates.values())
        return [item for item in templates if item.domain_id == domain_id] if domain_id else templates
