from calendar import monthrange
from datetime import date

from .base import decision


class CompensationRule:
    version = "cn-labor-compensation-1"
    fields = (
        "employment_start_date", "termination_date", "monthly_salary",
        "local_average_monthly_salary", "compensation_kind", "termination_reason",
    )

    @staticmethod
    def _service_months(start: date, end: date) -> int | None:
        if end < start:
            return None
        months = (end.year - start.year) * 12 + end.month - start.month
        if end.day < start.day:
            months -= 1
        return max(months, 0)

    @staticmethod
    def _add_months(value: date, months: int) -> date:
        month_index = value.month - 1 + months
        year = value.year + month_index // 12
        month = month_index % 12 + 1
        return value.replace(day=min(value.day, monthrange(year, month)[1]), year=year, month=month)

    @staticmethod
    def _compensation_months(start: date, end: date) -> float | None:
        """按完整年及剩余期间折算法定补偿月数。"""
        if end < start:
            return None
        years = end.year - start.year
        anniversary = CompensationRule._add_months(start, years * 12)
        if anniversary > end:
            years -= 1
            anniversary = CompensationRule._add_months(start, years * 12)
        if end == anniversary:
            return float(years)
        six_month_mark = CompensationRule._add_months(anniversary, 6)
        return float(years + (1 if end >= six_month_mark else 0.5))

    def evaluate(self, facts: dict, evidence: dict, authorities: list) -> dict:
        kind = facts.get("compensation_kind")
        if kind in (None, "undetermined"):
            claims = set(facts.get("claim_types") or [])
            kind = "damages" if "赔偿金" in claims else "compensation" if "经济补偿" in claims else None
        required = ("employment_start_date", "termination_date", "monthly_salary")
        missing = [name for name in required if facts.get(name) in (None, "")]
        if kind is None:
            missing.append("compensation_kind")
        if facts.get("local_average_monthly_salary") in (None, ""):
            missing.append("local_average_monthly_salary")
        calculations = {}
        assumptions = []
        if not any(name in missing for name in ("employment_start_date", "termination_date", "monthly_salary")):
            start = date.fromisoformat(str(facts["employment_start_date"]))
            end = date.fromisoformat(str(facts["termination_date"]))
            months = self._service_months(start, end)
            if months is None:
                missing.append("valid_employment_period")
            else:
                n_months = self._compensation_months(start, end)
                salary_base = float(facts["monthly_salary"])
                local_average = facts.get("local_average_monthly_salary")
                capped = False
                if local_average and salary_base > float(local_average) * 3:
                    salary_base = float(local_average) * 3
                    n_months = min(n_months, 12)
                    capped = True
                compensation = round(salary_base * n_months, 2)
                multiplier = 2 if kind == "damages" else 1
                calculations = {
                    "service_months": months,
                    "n_months": n_months,
                    "salary_base": salary_base,
                    "high_salary_cap_applied": capped,
                    "compensation": compensation,
                    "damages_or_compensation": round(compensation * multiplier, 2),
                    "multiplier": multiplier,
                }
        return decision(
            "economic_compensation", self.version,
            "已按工作年限折算、工资基数和补偿/赔偿类型生成受控估算；适用前提取决于解除规则复核。",
            {**{name: facts.get(name) for name in self.fields}, "compensation_kind": kind}, evidence, authorities, missing,
            calculations=calculations,
            assumptions=assumptions,
            warnings=["补偿与违法解除赔偿不可在解除性质未确定时自动二选一。"],
        )
