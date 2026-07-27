from .base import decision


class OvertimePayRule:
    """标准工时制下的加班费受控估算；特殊工时制保持失败关闭。"""

    version = "cn-labor-overtime-1"
    fields = (
        "monthly_salary", "working_hours_system", "overtime_monthly_wage_base",
        "overtime_workday_hours", "overtime_rest_day_hours",
        "overtime_statutory_holiday_hours", "rest_day_compensatory_leave_hours",
        "overtime_paid_amount",
    )

    def evaluate(self, facts: dict, evidence: dict, authorities: list) -> dict:
        system = facts.get("working_hours_system")
        monthly_base = facts.get("overtime_monthly_wage_base") or facts.get("monthly_salary")
        workday_hours = float(facts.get("overtime_workday_hours") or 0)
        rest_day_hours = float(facts.get("overtime_rest_day_hours") or 0)
        holiday_hours = float(facts.get("overtime_statutory_holiday_hours") or 0)
        compensatory_hours = float(facts.get("rest_day_compensatory_leave_hours") or 0)
        paid_amount = float(facts.get("overtime_paid_amount") or 0)
        missing = []
        if not system:
            missing.append("working_hours_system")
        elif system != "standard":
            missing.append("standard_working_hours_system_required")
        if monthly_base is None:
            missing.append("overtime_wage_base")
        if workday_hours + rest_day_hours + holiday_hours <= 0:
            missing.append("overtime_hours_by_type")

        calculations = {}
        assumptions = []
        if monthly_base is not None and not missing:
            hourly_base = round(float(monthly_base) / 21.75 / 8, 2)
            payable_rest_hours = max(rest_day_hours - compensatory_hours, 0)
            workday_pay = round(hourly_base * workday_hours * 1.5, 2)
            rest_day_pay = round(hourly_base * payable_rest_hours * 2, 2)
            holiday_pay = round(hourly_base * holiday_hours * 3, 2)
            total = round(workday_pay + rest_day_pay + holiday_pay, 2)
            calculations = {
                "hourly_wage_base": hourly_base,
                "workday_overtime_pay": workday_pay,
                "rest_day_overtime_pay": rest_day_pay,
                "statutory_holiday_overtime_pay": holiday_pay,
                "estimated_overtime_pay": total,
                "overtime_paid_amount": paid_amount,
                "estimated_unpaid_overtime_pay": round(max(total - paid_amount, 0), 2),
            }
            assumptions.append("小时工资按月工资基数÷21.75天÷8小时折算。")
            if facts.get("overtime_monthly_wage_base") is None:
                assumptions.append("未单独确认加班费基数，暂按用户确认的月工资估算。")
            if compensatory_hours:
                assumptions.append("休息日补休按等小时抵扣；补休有效性与实际安排仍需材料复核。")

        return decision(
            "overtime_pay", self.version,
            "已按标准工时制区分工作日、休息日和法定节假日进行初步核算。",
            {name: facts.get(name) for name in self.fields}, evidence, authorities, missing,
            calculations=calculations,
            assumptions=assumptions,
            warnings=[
                "加班事实、用人单位安排、工时制度审批、工资基数、补休及已付款项必须结合考勤、排班、聊天和工资记录复核。",
                "综合计算工时或不定时工作制不使用本公式，需结合审批文件和当地规则人工核算。",
            ],
        )
