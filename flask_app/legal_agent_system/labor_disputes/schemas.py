"""劳动纠纷事实契约；字段保持通用，法域由 Matter 单独管理。
定义劳动纠纷事实字段：
"""

from datetime import date
from typing import List, Optional

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
    demands: Optional[str] = None
    termination_reason: Optional[str] = None
    employment_active: Optional[bool] = None
    limitation_interruption_dates: List[date] = Field(default_factory=list)
    limitation_suspension_days: int = Field(default=0, ge=0, le=3650)


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
