"""无需访问真实案件数据的劳动纠纷离线评测 Runner。"""

import json
from pathlib import Path
from typing import Iterable, List, Optional

from legal_agent_system.labor_disputes.schemas import FIELD_QUESTIONS, LaborDisputeFacts

from .schema import LaborEvalCase, LaborEvalReport, LaborEvalResult


DEFAULT_DATASET = Path(__file__).with_name("cases.jsonl")


def load_cases(path: Optional[Path] = None) -> List[LaborEvalCase]:
    dataset = path or DEFAULT_DATASET
    return [LaborEvalCase.model_validate(json.loads(line)) for line in dataset.read_text(encoding="utf-8").splitlines() if line.strip()]


def evaluate_case(case: LaborEvalCase) -> LaborEvalResult:
    facts = LaborDisputeFacts.model_validate(case.facts).model_dump(mode="json", exclude_none=True)
    missing = [name for name in FIELD_QUESTIONS if not facts.get(name)]
    status = "awaiting_information" if missing else "blocked_authority"
    errors = []
    if missing != case.expected_missing_facts:
        errors.append("缺失事实集合或顺序不符合预期")
    if status != case.expected_status_without_authority:
        errors.append("无可信来源时的安全状态不符合预期")
    return LaborEvalResult(
        case_id=case.case_id,
        passed=not errors,
        actual_missing_facts=missing,
        actual_status_without_authority=status,
        errors=errors,
    )


def run_dataset(cases: Optional[Iterable[LaborEvalCase]] = None) -> LaborEvalReport:
    results = [evaluate_case(case) for case in (cases or load_cases())]
    passed = sum(result.passed for result in results)
    return LaborEvalReport(total=len(results), passed=passed, failed=len(results) - passed, results=results)


if __name__ == "__main__":
    print(run_dataset().model_dump_json(indent=2))
