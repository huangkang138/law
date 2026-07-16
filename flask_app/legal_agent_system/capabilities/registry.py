"""领域、模板、工具声明和验证策略的统一查询入口。"""
import logging
from typing import Dict, List, Tuple

from .contracts import DomainPackage, PlanTemplate


class CapabilityRegistry:
    def __init__(self, tool_registry) -> None:
        self.tool_registry = tool_registry
        self._domains: Dict[str, DomainPackage] = {}
        self._templates: Dict[str, PlanTemplate] = {}
        self._routes: Dict[str, Tuple[str, str]] = {}

    def register(self, package: DomainPackage) -> None:
        if package.domain_id in self._domains:
            raise ValueError(f"领域能力包已注册: {package.domain_id}")
        declared_tools = set(package.tool_names)
        for template in package.plan_templates:
            if template.domain_id != package.domain_id:
                raise ValueError("模板 domain_id 与能力包不一致")
            if template.template_id in self._templates:
                raise ValueError(f"计划模板已注册: {template.template_id}")
            for step in template.steps:
                if step.tool_name not in declared_tools:
                    raise ValueError(f"模板使用了未声明工具: {step.tool_name}")
                self.tool_registry.get(step.tool_name)
            self._templates[template.template_id] = template
        template_ids = {item.template_id for item in package.plan_templates}
        for rule in package.routing_rules:
            if rule.template_id not in template_ids:
                raise ValueError(f"路由指向未注册模板: {rule.template_id}")
            for task_type in [rule.task_type, *rule.aliases]:
                if task_type in self._routes:
                    raise ValueError(f"任务路由已注册: {task_type}")
                self._routes[task_type] = (package.domain_id, rule.template_id)
        self._domains[package.domain_id] = package

    def resolve(self, task_type: str) -> Tuple[DomainPackage, PlanTemplate]:
        logging.info(f"resolve解析任务类型: {task_type}")
        try:
            domain_id, template_id = self._routes[task_type]
            return self._domains[domain_id], self._templates[template_id]
        except KeyError as exc:
            raise ValueError(f"未注册的 Agent 任务类型: {task_type}") from exc

    def get_template(self, template_id: str) -> PlanTemplate:
        try:
            return self._templates[template_id]
        except KeyError as exc:
            raise ValueError(f"计划模板不存在: {template_id}") from exc

    def list_domains(self) -> List[DomainPackage]:
        return list(self._domains.values())

    def list_templates(self, domain_id: str | None = None) -> List[PlanTemplate]:
        templates = list(self._templates.values())
        return [item for item in templates if item.domain_id == domain_id] if domain_id else templates

