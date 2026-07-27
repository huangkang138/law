from typing import Any

from ..schemas import LaborRuleDecision


def decision(
    issue_tag: str,
    version: str,
    assessment: str,
    facts: dict,
    evidence: dict,
    authorities: list,
    missing: list[str] | None = None,
    calculations: dict[str, Any] | None = None,
    assumptions: list[str] | None = None,
    warnings: list[str] | None = None,
) -> dict:
    missing = list(missing or [])
    warnings = list(warnings or [])
    if evidence.get("conflicts"):
        warnings.append(f"材料候选存在冲突: {', '.join(evidence['conflicts'])}")
    if missing:
        status = "information_required"
    elif not authorities:
        status = "authority_required"
        warnings.append("当前规则缺少已验证且处于新鲜期的官方法源")
    else:
        status = "completed"
    return LaborRuleDecision(
        status=status,
        issue_tag=issue_tag,
        rule_version=version,
        assessment=assessment,
        missing_facts=missing,
        facts={name: facts.get(name) for name in facts},
        fact_refs=list(evidence.get("fact_refs") or []),
        evidence_refs=list(evidence.get("evidence_refs") or []),
        authority_refs=[item["authority_id"] for item in authorities],
        calculations=calculations or {},
        assumptions=assumptions or [],
        warnings=warnings,
        manual_review_required=True,
        legal_conclusion=False,
    ).model_dump(mode="json")
