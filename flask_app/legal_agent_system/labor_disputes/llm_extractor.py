"""受控 LLM 候选事实接口：只接受可在授权原文中逐字定位的输出。"""

from typing import Any, Callable, Dict, List
from pydantic import BaseModel, Field


class LLMFactCandidate(BaseModel):
    field: str
    value: Any
    quote: str = Field(min_length=1)
    start_offset: int = Field(ge=0)
    end_offset: int = Field(gt=0)
    confidence: float = Field(ge=0, le=1)


class ControlledLaborFactExtractor:
    ALLOWED_FIELDS = {"employee_name", "employer_name", "employment_start_date", "termination_date", "limitation_start_date", "monthly_salary", "work_location", "claim_types", "demands", "termination_reason"}

    def __init__(self, model: Callable[[str, int], Dict], token_budget: int = 4000) -> None:
        self.model, self.token_budget = model, token_budget

    def extract(self, text: str) -> Dict:
        raw = self.model(text, self.token_budget)
        usage = int(raw.get("token_usage", 0))
        if usage > self.token_budget:
            return {"candidates": [], "warnings": ["模型调用超过 token 预算，结果已拒绝。"], "error_code": "BUDGET_EXCEEDED", "token_usage": usage}
        accepted, warnings = [], []
        for item in raw.get("candidates", []):
            try:
                candidate = LLMFactCandidate.model_validate(item)
            except Exception:
                warnings.append("模型候选不符合结构化契约，已丢弃。")
                continue
            if candidate.field not in self.ALLOWED_FIELDS or text[candidate.start_offset:candidate.end_offset] != candidate.quote:
                warnings.append(f"候选 {candidate.field} 无法在授权原文定位，已丢弃。")
                continue
            accepted.append(candidate.model_dump())
        return {"candidates": accepted, "warnings": warnings, "token_usage": usage}
