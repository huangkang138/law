"""阶段 3.7C 青年就业五类旗舰评测。"""

import json
from collections import Counter
from pathlib import Path
from typing import Callable, Literal

from pydantic import BaseModel, Field

from legal_agent_system.labor_disputes.triage_rules import LaborTriageDecisionEngine
from legal_agent_system.labor_disputes.triage_schemas import LaborTriageFacts


DATASET = Path(__file__).with_name("flagship_cases.jsonl")


class YouthFlagshipCase(BaseModel):
    case_id: str = Field(pattern=r"^youth-\d{3}$")
    category: Literal["normal", "insufficient", "non_labor", "composite", "high_risk"]
    provenance: Literal["synthetic_gold", "official_public_adaptation"]
    source_url: str | None = None
    facts: dict
    expected_triage_type: str
    expected_relationship_status: str
    expected_dispute_tags: list[str] = Field(default_factory=list)
    expected_manual_review: bool


def load_flagship_cases(path: Path | None = None) -> list[YouthFlagshipCase]:
    return [
        YouthFlagshipCase.model_validate(json.loads(line))
        for line in (path or DATASET).read_text(encoding="utf-8").splitlines()
        if line.strip()
    ]


def run_flagship_dataset(
    cases=None,
    *,
    runtime_runner: Callable[[YouthFlagshipCase, dict], dict] | None = None,
) -> dict:
    cases = list(cases or load_flagship_cases())
    if runtime_runner is None:
        raise ValueError("旗舰评测必须提供 runtime_runner，禁止退化为仅分流规则自测")
    engine = LaborTriageDecisionEngine()
    failures = []
    runtime_exercised = 0
    analysis_exercised = 0
    material_types_covered = set()
    expected_runtime_status = {
        "normal": "completed",
        "insufficient": "awaiting_information",
        "non_labor": "human_handoff",
        "composite": "completed",
        "high_risk": "human_handoff",
    }
    for case in cases:
        result = engine.assess(LaborTriageFacts.model_validate(case.facts))
        expected = {
            "triage_type": case.expected_triage_type,
            "relationship_status": case.expected_relationship_status,
            "dispute_tags": case.expected_dispute_tags,
            "manual_review_required": case.expected_manual_review,
        }
        actual = {key: result[key] for key in expected}
        if actual != expected:
            failures.append({"case_id": case.case_id, "expected": expected, "actual": actual})
        runtime_result = runtime_runner(case, result)
        triage_run = runtime_result.get("triage_run") or {}
        runtime_exercised += 1
        runtime_expected = expected_runtime_status[case.category]
        if triage_run.get("status") != runtime_expected:
            failures.append({
                "case_id": case.case_id,
                "stage": "runtime_triage",
                "expected": runtime_expected,
                "actual": triage_run.get("status"),
            })
        material_types_covered.update(runtime_result.get("material_types") or [])
        if case.category == "composite":
            analysis_exercised += 1
            analysis_run = runtime_result.get("analysis_run") or {}
            analysis = (analysis_run.get("final_output") or {}).get("analyze_labor_case") or {}
            decisions = analysis.get("rule_decisions") or []
            traceable = bool(decisions) and all(
                item.get("fact_refs") and item.get("authority_refs")
                and item.get("manual_review_required")
                for item in decisions
            )
            if analysis_run.get("status") != "completed" or not traceable:
                failures.append({
                    "case_id": case.case_id,
                    "stage": "runtime_analysis",
                    "expected": "completed_with_traceable_rules",
                    "actual": analysis_run.get("status"),
                })
    return {
        "total": len(cases),
        "passed": len(cases) - len(failures),
        "failed": len(failures),
        "categories": dict(Counter(case.category for case in cases)),
        "provenance": dict(Counter(case.provenance for case in cases)),
        "runtime_exercised": runtime_exercised,
        "analysis_exercised": analysis_exercised,
        "material_types_covered": sorted(material_types_covered),
        "failures": failures,
    }
