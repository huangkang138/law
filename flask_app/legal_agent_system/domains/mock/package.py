"""阶段 1 模拟任务能力包。"""

from legal_agent_system.capabilities.contracts import (
    DomainPackage,
    PlanTemplate,
    RoutingRule,
    TemplateStep,
)


def build_mock_domain_package() -> DomainPackage:
    template = PlanTemplate(
        template_id="mock_case_summary",
        version="1.0.0",
        domain_id="system_mock",
        task_type="mock_case_summary",
        allowed_step_types=["summary"],
        steps=[TemplateStep(
            step_id="mock_summary",
            name="生成模拟案件摘要",
            step_type="summary",
            tool_name="mock_case_summary",
            requires_approval=True,
            on_failure="retry",
        )],
    )
    return DomainPackage(
        domain_id="system_mock",
        version="1.0.0",
        routing_rules=[RoutingRule(task_type="mock_case_summary", template_id=template.template_id)],
        plan_templates=[template],
        tool_names=["mock_case_summary"],
        verification_policies=[],
    )
