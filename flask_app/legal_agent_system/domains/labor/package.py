"""中国劳动领域的首个方案 C 能力包。"""

from legal_agent_system.capabilities.contracts import (
    DomainPackage,
    PlanTemplate,
    RoutingRule,
    TemplateStep,
    VerificationPolicy,
)


COMMON_STEP_TYPES = [
    "relationship_assessment", "evidence_analysis", "timeline_analysis",
    "legal_analysis", "document_drafting",
]
COMMON_TOOLS = [
    "assess_labor_relationship",
    "generate_evidence_checklist",
    "build_case_timeline",
    "analyze_labor_dispute",
    "analyze_labor_consultation",
    "analyze_labor_case",
    "draft_labor_arbitration_application",
]


def _evidence_step() -> TemplateStep:
    return TemplateStep(
        step_id="evidence_check",
        name="核对材料与证据缺口",
        step_type="evidence_analysis",
        tool_name="generate_evidence_checklist",
        verification_policy_ids=["global.tool_result", "labor.evidence"],
        on_failure="request_context",
    )


def _analysis_step(depends_on: list[str], tool_name: str = "analyze_labor_dispute") -> TemplateStep:
    return TemplateStep(
        step_id="labor_analysis",
        name="计算期限并验证法律来源",
        step_type="legal_analysis",
        tool_name=tool_name,
        depends_on=depends_on,
        verification_policy_ids=["global.tool_result", "labor.authority", "labor.analysis"],
        on_failure="reject",
    )


def build_labor_domain_package() -> DomainPackage:
    relationship = PlanTemplate(
        template_id="labor_relationship_assessment",
        version="1.0.0",
        domain_id="cn_labor",
        task_type="labor_relationship_assessment",
        allowed_step_types=COMMON_STEP_TYPES,
        steps=[TemplateStep(
            step_id="relationship_assessment",
            name="判断实习、兼职或就业场景中的法律关系",
            step_type="relationship_assessment",
            tool_name="assess_labor_relationship",
            verification_policy_ids=["global.tool_result", "labor.relationship"],
            on_failure="handoff",
        )],
    )
    arbitration = PlanTemplate(
        template_id="labor_arbitration_application",
        version="1.0.0",
        domain_id="cn_labor",
        task_type="labor_arbitration_application",
        allowed_step_types=COMMON_STEP_TYPES,
        steps=[
            _evidence_step(),
            _analysis_step(["evidence_check"]),
            TemplateStep(
                step_id="arbitration_draft",
                name="经审批生成劳动仲裁申请书草稿",
                step_type="document_drafting",
                tool_name="draft_labor_arbitration_application",
                depends_on=["labor_analysis"],
                requires_approval=True,
                verification_policy_ids=["global.tool_result", "labor.draft"],
                on_failure="handoff",
            ),
        ],
    )
    consultation = PlanTemplate(
        template_id="labor_consultation",
        version="1.0.0",
        domain_id="cn_labor",
        task_type="labor_consultation",
        allowed_step_types=COMMON_STEP_TYPES,
        steps=[_evidence_step(), _analysis_step(["evidence_check"], "analyze_labor_consultation")],
    )
    case_analysis = PlanTemplate(
        template_id="labor_case_analysis",
        version="1.0.0",
        domain_id="cn_labor",
        task_type="labor_case_analysis",
        allowed_step_types=COMMON_STEP_TYPES,
        steps=[
            TemplateStep(
                step_id="case_timeline",
                name="建立解除与争议事件时间线",
                step_type="timeline_analysis",
                tool_name="build_case_timeline",
                optional=True,
                condition={"fact_present": "termination_date"},
                skip_reason="未提供解除日期，本次不执行解除事件时间线步骤",
                verification_policy_ids=["global.tool_result"],
                on_failure="request_context",
            ),
            _evidence_step(),
            _analysis_step(["evidence_check"], "analyze_labor_case"),
        ],
    )
    return DomainPackage(
        domain_id="cn_labor",
        version="1.0.0",
        routing_rules=[
            RoutingRule(
                task_type="labor_arbitration_application",
                template_id=arbitration.template_id,
                aliases=["cn_labor_dispute"],
            ),
            RoutingRule(task_type="labor_consultation", template_id=consultation.template_id),
            RoutingRule(task_type="labor_case_analysis", template_id=case_analysis.template_id),
            RoutingRule(
                task_type="labor_relationship_assessment",
                template_id=relationship.template_id,
            ),
        ],
        plan_templates=[relationship, arbitration, consultation, case_analysis],
        tool_names=COMMON_TOOLS,
        verification_policies=[
            VerificationPolicy(policy_id="labor.evidence", layer="task"),
            VerificationPolicy(policy_id="labor.authority", layer="domain"),
            VerificationPolicy(policy_id="labor.analysis", layer="task"),
            VerificationPolicy(policy_id="labor.draft", layer="task"),
            VerificationPolicy(policy_id="labor.relationship", layer="domain"),
        ],
    )
