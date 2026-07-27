from .base import decision


class TerminationRule:
    version = "cn-labor-termination-1"
    fields = (
        "termination_date", "termination_reason", "termination_initiator",
        "termination_basis", "termination_notice_date", "notice_period_days",
        "union_notified", "protected_statuses",
    )

    def evaluate(self, facts: dict, evidence: dict, authorities: list) -> dict:
        missing = [name for name in ("termination_date", "termination_reason", "termination_initiator") if not facts.get(name)]
        reason = str(facts.get("termination_reason") or "")
        basis = str(facts.get("termination_basis") or "")
        text = f"{reason} {basis}"
        if any(key in text for key in ("严重违反", "严重失职", "欺诈", "不符合录用条件")):
            route = "employer_fault_based_termination_review"
        elif any(key in text for key in ("医疗期满", "不能胜任", "客观情况重大变化")):
            route = "employer_notice_termination_review"
        elif any(key in text for key in ("经济性裁员", "裁员")):
            route = "economic_layoff_review"
        elif facts.get("termination_initiator") == "employee":
            route = "employee_resignation_review"
        elif facts.get("termination_initiator") == "mutual":
            route = "mutual_termination_review"
        else:
            route = "undetermined_termination_route"
        return decision(
            "termination", self.version,
            "已识别解除路径候选，必须继续核对实体理由、通知、工会程序、举证责任和特殊保护状态。",
            {name: facts.get(name) for name in self.fields}, evidence, authorities, missing,
            calculations={"termination_route": route},
            warnings=["当前结果不直接认定解除合法或违法。"],
        )
