"""中国劳动领域能力包：主模板通过争议标签组合白名单步骤。"""

from legal_agent_system.capabilities.contracts import (
    DomainPackage,
    PlanTemplate,
    RoutingRule,
    TemplateStep,
    VerificationPolicy,
)
from legal_agent_system.labor_disputes.dispute_tags import (
    ALLOWED_DISPUTE_TAGS,
    ECONOMIC_COMPENSATION,
    PROBATION,
    TERMINATION,
    WAGE_ARREARS,
)


COMMON_STEP_TYPES = [
    "relationship_assessment", "evidence_analysis", "timeline_analysis",
    "wage_analysis", "termination_analysis", "compensation_analysis",
    "legal_analysis", "document_drafting",
]
COMMON_TOOLS = [
    "assess_labor_relationship",
    "generate_evidence_checklist",
    "build_case_timeline",
    "analyze_wage_arrears",
    "analyze_labor_termination",
    "analyze_economic_compensation",
    "analyze_probation",
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



def _issue_steps() -> list[TemplateStep]:
    # 欠薪分析
    # 解除分析
    # 经济补偿分析
    return [
        TemplateStep(
            step_id="probation_analysis",
            name="分析试用期约定、工资与解除条件",
            step_type="legal_analysis",
            tool_name="analyze_probation",
            depends_on=["evidence_check"],
            optional=True,
            condition={"dispute_tag_any": [PROBATION]},
            skip_reason="争议标签不包含试用期，本次不执行试用期分析",
            verification_policy_ids=["global.tool_result", "labor.issue"],
            on_failure="request_context",
        ),
        TemplateStep(
            step_id="wage_arrears_analysis",
            name="分析欠薪期间与金额",
            step_type="wage_analysis",
            tool_name="analyze_wage_arrears",
            depends_on=["evidence_check"],
            optional=True,
            condition={"dispute_tag_any": [WAGE_ARREARS]},
            skip_reason="争议标签不包含欠薪，本次不执行欠薪分析",
            verification_policy_ids=["global.tool_result", "labor.issue"],
            on_failure="request_context",
        ),
        TemplateStep(
            step_id="termination_analysis",
            name="分析解除事实、依据与程序",
            step_type="termination_analysis",
            tool_name="analyze_labor_termination",
            depends_on=["evidence_check"],
            optional=True,
            condition={"dispute_tag_any": [TERMINATION]},
            skip_reason="争议标签不包含解除，本次不执行解除分析",
            verification_policy_ids=["global.tool_result", "labor.issue"],
            on_failure="request_context",
        ),
        TemplateStep(
            step_id="economic_compensation_analysis",
            name="估算经济补偿或赔偿",
            step_type="compensation_analysis",
            tool_name="analyze_economic_compensation",
            depends_on=["evidence_check"],
            optional=True,
            condition={"dispute_tag_any": [ECONOMIC_COMPENSATION]},
            skip_reason="争议标签不包含经济补偿，本次不执行补偿估算",
            verification_policy_ids=["global.tool_result", "labor.issue"],
            on_failure="request_context",
        ),
    ]


def _analysis_step(depends_on: list[str], tool_name: str) -> TemplateStep:
    return TemplateStep(
        step_id="labor_analysis",
        name="统一计算期限并验证法律来源",
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

    arbitration_issues = _issue_steps()
    arbitration = PlanTemplate(
        template_id="labor_arbitration_application",
        version="3.0.0",
        domain_id="cn_labor",
        task_type="labor_arbitration_application",
        allowed_step_types=COMMON_STEP_TYPES,
        allowed_dispute_tags=list(ALLOWED_DISPUTE_TAGS),
        steps=[
            _evidence_step(),
            *arbitration_issues,
            _analysis_step(
                [step.step_id for step in arbitration_issues],
                "analyze_labor_dispute",
            ),
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
        version="1.1.0",
        domain_id="cn_labor",
        task_type="labor_consultation",
        allowed_step_types=COMMON_STEP_TYPES,
        allowed_dispute_tags=list(ALLOWED_DISPUTE_TAGS),
        steps=[
            _evidence_step(),
            _analysis_step(["evidence_check"], "analyze_labor_consultation"),
        ],
    )

    case_issues = _issue_steps()
    case_analysis = PlanTemplate(
        template_id="labor_case_analysis",
        version="3.0.0",
        domain_id="cn_labor",
        task_type="labor_case_analysis",
        allowed_step_types=COMMON_STEP_TYPES,
        allowed_dispute_tags=list(ALLOWED_DISPUTE_TAGS),
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
            *case_issues,
            _analysis_step([step.step_id for step in case_issues], "analyze_labor_case"),
        ],
    )

    return DomainPackage(
        domain_id="cn_labor",
        version="1.2.0",
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
            VerificationPolicy(policy_id="labor.issue", layer="task"),
            VerificationPolicy(policy_id="labor.authority", layer="domain"),
            VerificationPolicy(policy_id="labor.analysis", layer="task"),
            VerificationPolicy(policy_id="labor.draft", layer="task"),
            VerificationPolicy(policy_id="labor.relationship", layer="domain"),
        ],
    )
