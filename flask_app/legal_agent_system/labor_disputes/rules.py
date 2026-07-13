"""中国劳动争议确定性规则；模型不得改写这些结论。"""

from datetime import date, timedelta
from typing import Dict

RULE_VERSION = "cn-labor-rules-2"


class LaborRuleEngine:
    def limitation(self, facts: Dict, authorities: list, fact_refs: list) -> Dict:
        start = date.fromisoformat(facts["limitation_start_date"])
        interruptions = sorted(date.fromisoformat(v) for v in facts.get("limitation_interruption_dates", []))
        suspension_days = int(facts.get("limitation_suspension_days", 0))
        assumptions, warnings = [], []

        if facts.get("employment_active") and "欠薪" in facts.get("claim_types", []):
            deadline = None
            assumptions.append("劳动关系存续期间的拖欠工资争议适用特别规则；终止后再起算一年。")
        else:
            base = interruptions[-1] if interruptions else start
            deadline = base + timedelta(days=365 + suspension_days)
            if interruptions:
                assumptions.append("按用户确认的最后一次时效中断日期重新起算。")
            if suspension_days:
                assumptions.append(f"按用户确认的中止期间顺延 {suspension_days} 天。")
        if not interruptions and not suspension_days:
            warnings.append("尚未提供时效中断或中止事实；当前日期是初步计算结果。")
        return {
            "rule_version": RULE_VERSION,
            "start_date": start.isoformat(),
            "estimated_deadline": deadline.isoformat() if deadline else None,
            "fact_refs": fact_refs,
            "authority_refs": [a["authority_id"] for a in authorities],
            "assumptions": assumptions,
            "warnings": warnings,
            "manual_review_required": bool(interruptions or suspension_days),
        }
