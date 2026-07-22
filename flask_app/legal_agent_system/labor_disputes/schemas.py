"""劳动纠纷事实契约；字段保持通用，法域由 Matter 单独管理。
定义劳动纠纷事实字段：
"""

from datetime import date
from typing import Any, Dict, List, Literal, Optional

from pydantic import BaseModel, Field


class LaborDisputeFacts(BaseModel):
    employee_name: Optional[str] = None
    employer_name: Optional[str] = None
    employment_start_date: Optional[date] = None
    termination_date: Optional[date] = None
    limitation_start_date: Optional[date] = None
    monthly_salary: Optional[float] = Field(default=None, gt=0)
    work_location: Optional[str] = None
    claim_types: List[str] = Field(default_factory=list)
    dispute_tags: List[str] = Field(default_factory=list)
    demands: Optional[str] = None
    termination_reason: Optional[str] = None
    wage_arrears_amount: Optional[float] = Field(default=None, gt=0)
    wage_arrears_months: Optional[int] = Field(default=None, ge=1, le=1200)
    wage_arrears_start_date: Optional[date] = None
    wage_arrears_end_date: Optional[date] = None
    employment_active: Optional[bool] = None
    limitation_interruption_dates: List[date] = Field(default_factory=list)
    limitation_suspension_days: int = Field(default=0, ge=0, le=3650)
    contract_term_months: Optional[int] = Field(default=None, ge=1, le=1200)
    contract_term_type: Optional[Literal["fixed", "open_ended", "task_based"]] = None
    probation_period_months: Optional[int] = Field(default=None, ge=0, le=12)
    probation_salary: Optional[float] = Field(default=None, gt=0)
    regular_salary: Optional[float] = Field(default=None, gt=0)
    local_minimum_wage: Optional[float] = Field(default=None, gt=0)
    wage_payment_day: Optional[int] = Field(default=None, ge=1, le=31)
    wages_paid_through: Optional[date] = None
    termination_initiator: Optional[Literal["employee", "employer", "mutual", "expiry", "unknown"]] = None
    termination_basis: Optional[str] = None
    termination_notice_date: Optional[date] = None
    notice_period_days: Optional[int] = Field(default=None, ge=0, le=365)
    union_notified: Optional[bool] = None
    protected_statuses: List[str] = Field(default_factory=list)
    local_average_monthly_salary: Optional[float] = Field(default=None, gt=0)
    compensation_kind: Optional[Literal["compensation", "damages", "undetermined"]] = None
    prior_probation_with_same_employer: Optional[bool] = None
    attendance_days: Optional[int] = Field(default=None, ge=0, le=366)


class LaborEvidenceItem(BaseModel):
    field: str
    value: Any = None
    status: Literal["supported", "user_confirmed_only", "conflict", "missing"]
    fact_refs: List[str] = Field(default_factory=list)
    evidence_refs: List[str] = Field(default_factory=list)
    material_refs: List[Dict[str, Any]] = Field(default_factory=list)
    conflicting_values: List[Any] = Field(default_factory=list)


class LaborRuleDecision(BaseModel):
    """3.7C 统一规则结果；任何法律判断都必须可追溯且保留人工复核。"""

    status: Literal["completed", "information_required", "authority_required"]
    issue_tag: str
    rule_version: str
    assessment: str
    missing_facts: List[str] = Field(default_factory=list)
    facts: Dict[str, Any] = Field(default_factory=dict)
    fact_refs: List[str] = Field(default_factory=list)
    evidence_refs: List[str] = Field(default_factory=list)
    authority_refs: List[str] = Field(default_factory=list)
    calculations: Dict[str, Any] = Field(default_factory=dict)
    assumptions: List[str] = Field(default_factory=list)
    warnings: List[str] = Field(default_factory=list)
    manual_review_required: bool = True
    legal_conclusion: bool = False


FIELD_QUESTIONS = {
    "employee_name": "申请人姓名是什么？",
    "employer_name": "用人单位的完整名称是什么？",
    "employment_start_date": "劳动关系何时开始？",
    "monthly_salary": "离职前月工资或争议工资基数是多少？",
    "work_location": "实际工作地点在哪里？",
    "claim_types": "争议涉及欠薪、解除、加班费还是其他事项？",
    "demands": "希望通过仲裁解决哪些具体请求？",
    "limitation_start_date": "你从哪一天起知道或应当知道权利受到侵害？",
}
