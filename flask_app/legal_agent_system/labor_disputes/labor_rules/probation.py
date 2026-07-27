from .base import decision


class ProbationRule:
    version = "cn-labor-probation-1"
    fields = (
        "contract_term_months", "contract_term_type", "probation_period_months",
        "probation_salary", "regular_salary", "local_minimum_wage",
        "prior_probation_with_same_employer", "termination_reason",
    )

    @staticmethod
    def _maximum_months(facts: dict):
        term_type = facts.get("contract_term_type")
        months = facts.get("contract_term_months")
        if term_type == "open_ended":
            return 6
        if term_type == "task_based" or (months is not None and months < 3):
            return 0
        if months is None:
            return None
        if months < 12:
            return 1
        if months < 36:
            return 2
        return 6

    def evaluate(self, facts: dict, evidence: dict, authorities: list) -> dict:
        probation = facts.get("probation_period_months")
        maximum = self._maximum_months(facts)
        missing = []
        if probation is None:
            missing.append("probation_period_months")
        if maximum is None:
            missing.append("contract_term")
        salary_floor = None
        regular = facts.get("regular_salary") or facts.get("monthly_salary")
        if regular:
            salary_floor = round(float(regular) * 0.8, 2)
        if facts.get("local_minimum_wage"):
            salary_floor = max(salary_floor or 0, float(facts["local_minimum_wage"]))
        duration_exceeded = probation is not None and maximum is not None and probation > maximum
        salary_below_floor = (
            facts.get("probation_salary") is not None
            and salary_floor is not None
            and float(facts["probation_salary"]) < salary_floor
        )
        return decision(
            "probation", self.version,
            "已核对试用期期限、重复约定和工资下限；试用期解除仍须逐项核对法定理由及说明义务。",
            {name: facts.get(name) for name in self.fields}, evidence, authorities, missing,
            calculations={
                "maximum_probation_months": maximum,
                "duration_exceeded": duration_exceeded,
                "salary_floor": salary_floor,
                "salary_below_floor": salary_below_floor,
                "repeat_probation": facts.get("prior_probation_with_same_employer"),
            },
            warnings=["岗位最低档工资、当地最低工资和是否曾约定试用期需以有效材料复核。"],
        )
