import re

from .common import DATE, MONEY, candidate, collect, first, iso_date


class TerminationNoticeAdapter:
    document_type = "termination_notice"
    keywords = ("解除劳动合同通知", "终止劳动合同通知", "辞退通知", "解除通知")

    def extract(self, text: str):
        date = first(text, "termination_date", rf"(?:劳动关系|劳动合同)?(?:于|自)\s*{DATE}\s*(?:解除|终止)", self.document_type, lambda m: iso_date(m, 1), 0.96)
        if date is None:
            date = first(text, "termination_date", rf"{DATE}\s*(?:解除|终止)(?:劳动关系|劳动合同)?", self.document_type, lambda m: iso_date(m, 1), 0.95)
        notice = first(text, "termination_notice_date", rf"(?:通知日期|落款日期)[：:\s]*{DATE}", self.document_type, lambda m: iso_date(m, 1), 0.95)
        reason = first(text, "termination_reason", r"(?:解除|终止)(?:理由|原因|依据)[：:\s]*([^。；\n]{2,120})", self.document_type, confidence=0.94)
        basis = first(text, "termination_basis", r"依据[《\s]*([^。；\n]{2,120})", self.document_type, confidence=0.9)
        return collect(date, notice, reason, basis)


class AttendanceAdapter:
    document_type = "attendance_record"
    keywords = ("考勤", "打卡", "出勤", "迟到", "排班")

    def extract(self, text: str):
        days = first(text, "attendance_days", r"(?:出勤|实际出勤)[^\d]{0,8}(\d{1,3})\s*天", self.document_type, lambda m: int(m.group(1)), 0.93)
        return collect(days)


class PayrollAdapter:
    document_type = "payroll_record"
    keywords = ("工资条", "工资表", "薪资单", "工资发放", "银行流水")

    def extract(self, text: str):
        salary = first(text, "monthly_salary", rf"(?:应发工资|月工资|基本工资|工资合计)[^\d]{{0,12}}{MONEY}", self.document_type, lambda m: float(m.group(1)), 0.94)
        arrears = first(text, "wage_arrears_amount", rf"(?:欠付|未付|拖欠)[^\d]{{0,12}}{MONEY}", self.document_type, lambda m: float(m.group(1)), 0.93)
        paid_through = first(text, "wages_paid_through", rf"工资已支付至[：:\s]*{DATE}", self.document_type, lambda m: iso_date(m, 1), 0.94)
        pay_day = first(text, "wage_payment_day", r"每月\s*(\d{1,2})\s*日[^。\n]{0,12}(?:支付|发放)工资", self.document_type, lambda m: int(m.group(1)), 0.9)
        return collect(salary, arrears, paid_through, pay_day)


def default_record_adapters():
    return [TerminationNoticeAdapter(), AttendanceAdapter(), PayrollAdapter()]
