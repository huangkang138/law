"""劳动纠纷评测数据契约。"""

from typing import Any, Dict, List, Literal

from pydantic import BaseModel, Field


class LaborEvalCase(BaseModel):
    case_id: str = Field(pattern=r"^labor-\d{3}$")
    title: str
    facts: Dict[str, Any]
    expected_missing_facts: List[str]
    expected_status_without_authority: Literal["awaiting_information", "blocked_authority"]


class LaborEvalResult(BaseModel):
    case_id: str
    passed: bool
    actual_missing_facts: List[str]
    actual_status_without_authority: str
    errors: List[str] = Field(default_factory=list)


class LaborEvalReport(BaseModel):
    total: int
    passed: int
    failed: int
    results: List[LaborEvalResult]
