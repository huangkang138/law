from .base import decision


class WageArrearsRule:
    version = "cn-labor-wage-1"
    fields = (
        "monthly_salary", "wage_arrears_amount", "wage_arrears_months",
        "wage_arrears_start_date", "wage_arrears_end_date", "wages_paid_through",
    )

    def evaluate(self, facts: dict, evidence: dict, authorities: list) -> dict:
        amount = facts.get("wage_arrears_amount")
        months = facts.get("wage_arrears_months")
        salary = facts.get("monthly_salary")
        assumptions = []
        if amount is None and months and salary:
            amount = round(float(salary) * int(months), 2)
            assumptions.append("欠薪金额按月工资乘以用户确认的欠薪月数估算，未计个税、社保、绩效和部分月份差异。")
        missing = []
        if amount is None:
            missing.append("wage_arrears_amount_or_salary_and_months")
        if not facts.get("wage_arrears_start_date") and not facts.get("wages_paid_through"):
            missing.append("wage_arrears_period")
        return decision(
            "wage_arrears", self.version,
            "已形成欠薪金额与期间的受控核算；是否实际欠付仍需以工资、考勤和付款记录交叉确认。",
            {name: facts.get(name) for name in self.fields}, evidence, authorities, missing,
            calculations={"estimated_arrears": amount, "months": months},
            assumptions=assumptions,
            warnings=["工资组成、已付款项、扣款合法性和当地工资支付规则仍需人工复核。"],
        )
