"""方案 C 的能力包、模板和运行时计划契约。"""

from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field, model_validator


class RoutingRule(BaseModel):
    task_type: str
    template_id: str
    aliases: List[str] = Field(default_factory=list)


class VerificationPolicy(BaseModel):
    policy_id: str
    version: str = "1.0.0"
    layer: str = Field(pattern=r"^(domain|task)$")


class TemplateStep(BaseModel):
    step_id: str
    name: str
    step_type: str
    tool_name: str
    depends_on: List[str] = Field(default_factory=list)
    optional: bool = False
    condition: Optional[Dict[str, Any]] = None
    skip_reason: Optional[str] = None
    requires_approval: bool = False
    verification_policy_ids: List[str] = Field(default_factory=list)
    on_failure: str = Field(default="reject", pattern=r"^(retry|request_context|replan|reject|handoff)$")
    arguments: Dict[str, Any] = Field(default_factory=dict)

    @model_validator(mode="after")
    def validate_optional_condition(self):
        if self.optional and not self.skip_reason:
            raise ValueError("可选步骤必须声明 skip_reason")
        return self


class PlanTemplate(BaseModel):
    template_id: str
    version: str
    domain_id: str
    task_type: str
    allowed_step_types: List[str]
    steps: List[TemplateStep]

    @model_validator(mode="after")
    def validate_steps(self):
        known: set[str] = set()
        for step in self.steps:
            if step.step_id in known:
                raise ValueError(f"模板步骤重复: {step.step_id}")
            if step.step_type not in self.allowed_step_types:
                raise ValueError(f"模板不允许步骤类型: {step.step_type}")
            unknown_dependencies = set(step.depends_on) - known
            if unknown_dependencies:
                raise ValueError(f"步骤依赖必须指向前序步骤: {sorted(unknown_dependencies)}")
            known.add(step.step_id)
        return self


class DomainPackage(BaseModel):
    domain_id: str
    version: str
    routing_rules: List[RoutingRule]
    plan_templates: List[PlanTemplate]
    tool_names: List[str]
    verification_policies: List[VerificationPolicy]
    optional_subgraphs: Dict[str, str] = Field(default_factory=dict)


class PlanStep(BaseModel):
    step_id: str
    name: str
    step_type: str
    tool_name: str
    depends_on: List[str] = Field(default_factory=list)
    status: str = "pending"
    skip_reason: Optional[str] = None
    requires_approval: bool = False
    verification_policy_ids: List[str] = Field(default_factory=list)
    on_failure: str = "reject"
    arguments: Dict[str, Any] = Field(default_factory=dict)


class PlanRevision(BaseModel):
    plan_id: Optional[str] = None
    domain_id: str
    task_type: str
    template_id: str
    template_version: str
    plan_revision: int = 0
    input_fingerprint: str
    replan_reason: Optional[str] = None
    triggered_by: str = "runtime"
    parent_plan_id: Optional[str] = None
    steps: List[PlanStep]

