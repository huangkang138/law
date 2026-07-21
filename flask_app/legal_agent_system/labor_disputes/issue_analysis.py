"""3.7B 劳动争议问题步骤；只输出可审计的初步分析，不替代最终法源校验。"""

from datetime import date
from typing import Dict, List

from services.labor_compensation_service import get_labor_compensation_service


class LaborIssueAnalysisService:
    """复用劳动事实档案，为主 PlanTemplate 的白名单步骤提供结果。"""

    def __init__(self, labor_disputes) -> None:
        self.labor_disputes = labor_disputes

    def wage_arrears(self, matter_id: str, client_id: str) -> Dict:
        facts = self._facts(matter_id, client_id)
        amount = facts.get("wage_arrears_amount")
        months = facts.get("wage_arrears_months")
        if amount is None and months and facts.get("monthly_salary"):
            amount = round(float(facts["monthly_salary"]) * int(months), 2)
        missing = [] if amount is not None else ["wage_arrears_amount_or_months"]
        return self._result(
            "wage_arrears",
            missing,
            {
                "arrears_amount": amount,
                "arrears_months": months,
                "period_start": facts.get("wage_arrears_start_date"),
                "period_end": facts.get("wage_arrears_end_date"),
            },
            "欠薪金额和期间仍需结合工资记录、考勤及付款流水复核。",
        )

    def termination(self, matter_id: str, client_id: str) -> Dict:
        facts = self._facts(matter_id, client_id)
        missing = [
            name for name in ("termination_date", "termination_reason")
            if not facts.get(name)
        ]
        return self._result(
            "termination",
            missing,
            {
                "termination_date": facts.get("termination_date"),
                "termination_reason": facts.get("termination_reason"),
            },
            "解除合法性仍需核对解除依据、通知、程序和举证责任。",
        )

    def economic_compensation(self, matter_id: str, client_id: str) -> Dict:
        facts = self._facts(matter_id, client_id)
        required = ("employment_start_date", "termination_date", "monthly_salary")
        missing = [name for name in required if not facts.get(name)]
        calculation = None
        warnings: List[str] = []
        if not missing:
            years, months = self._service_period(
                date.fromisoformat(facts["employment_start_date"]),
                date.fromisoformat(facts["termination_date"]),
            )
            if years is None:
                missing.append("valid_employment_period")
            else:
                calculation = get_labor_compensation_service().calculate(
                    facts["monthly_salary"], years, months, save_record=False,
                )
                warnings.append(calculation["warning"])
        result = self._result(
            "economic_compensation",
            missing,
            {"calculation": calculation},
            "补偿与赔偿适用条件取决于解除原因和程序，当前仅作估算。",
        )
        result["warnings"].extend(warnings)
        return result

    def _facts(self, matter_id: str, client_id: str) -> Dict:
        return dict(self.labor_disputes.get_workflow(matter_id, client_id).get("facts") or {})

    @staticmethod
    def _service_period(start: date, end: date) -> tuple[int | None, int]:
        if end < start:
            return None, 0
        total_months = (end.year - start.year) * 12 + end.month - start.month
        if end.day < start.day:
            total_months -= 1
        total_months = max(total_months, 0)
        return total_months // 12, total_months % 12

    @staticmethod
    def _result(tag: str, missing: List[str], data: Dict, warning: str) -> Dict:
        return {
            "status": "preliminary",
            "issue_tag": tag,
            "missing_facts": missing,
            "manual_review_required": True,
            "legal_conclusion": False,
            "data": data,
            "warnings": [warning],
        }
