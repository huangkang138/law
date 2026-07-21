"""青年就业劳动分流的数据契约。
    TRIAGE_QUESTIONS定义实习、兼职、学生身份、用工要素、风险等结构化输入和追问
"""

from typing import List, Literal, Optional

from pydantic import BaseModel, Field


class LaborTriageFacts(BaseModel):
    """分流所需的最小结构化事实；未知信息必须显式追问。"""

    issue_domain: Literal["labor", "non_labor", "unknown"] = "unknown"
    scenario_type: Literal[
        "school_arranged_internship", "independent_internship", "work_study",
        "part_time", "graduate_employment", "regular_employment", "other", "unknown",
    ] = "unknown"
    student_status: Literal[
        "current_student", "graduating", "graduated", "not_student", "unknown"
    ] = "unknown"
    school_arranged: Optional[bool] = None
    employment_intent: Optional[bool] = None
    employer_qualified: Optional[bool] = None
    paid_labor: Optional[bool] = None
    management_control: Optional[bool] = None
    business_integrated: Optional[bool] = None
    regular_schedule: Optional[bool] = None
    agreement_type: Literal[
        "labor_contract", "internship_agreement", "service_agreement", "none", "unknown"
    ] = "unknown"
    claim_types: List[str] = Field(default_factory=list)
    urgent_risks: List[Literal[
        "imminent_limitation_deadline", "work_injury", "personal_safety",
        "coercion_or_threat", "minor_worker", "mass_dispute",
    ]] = Field(default_factory=list)


TRIAGE_QUESTIONS = {
    "issue_domain": "问题是否发生在求职、实习、兼职、入职、工资或辞退过程中？",
    "scenario_type": "这次经历属于学校安排实习、自主实习、勤工助学、兼职还是正式就业？",
    "student_status": "事情发生时，你是在校、临近毕业、已经毕业，还是已不再具有学生身份？",
    "school_arranged": "该实习或工作是否由学校统一组织、纳入教学或学分安排？",
    "employment_intent": "你和单位当时是否以建立正式、持续用工关系为目的？",
    "employer_qualified": "对方是否为公司、个体经济组织或其他依法用工的组织？",
    "paid_labor": "你是否实际提供劳动，并由对方支付工资、报酬或固定津贴？",
    "management_control": "对方是否安排岗位、考勤、工作时间并实施奖惩或日常管理？",
    "business_integrated": "你完成的工作是否属于该单位日常业务的一部分？",
}
