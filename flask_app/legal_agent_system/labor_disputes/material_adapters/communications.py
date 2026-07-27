from .common import DATE, MONEY, collect, first, iso_date


class ChatRecordAdapter:
    document_type = "chat_record"
    keywords = ("聊天记录", "微信", "企业微信", "发送时间", "对话")

    def extract(self, text: str):
        termination = first(text, "termination_date", rf"{DATE}[^。\n]{{0,40}}(?:不用来|解除|辞退|终止)", self.document_type, lambda m: iso_date(m, 1), 0.86)
        arrears = first(text, "wage_arrears_amount", rf"(?:欠你的工资|未发工资|拖欠工资)[^\d]{{0,15}}{MONEY}", self.document_type, lambda m: float(m.group(1)), 0.84)
        salary = first(text, "monthly_salary", rf"(?:工资|月薪)[^\d]{{0,10}}{MONEY}", self.document_type, lambda m: float(m.group(1)), 0.8)
        reason = first(text, "termination_reason", r"(?:辞退|解除|不用来上班)[，,:：\s]*(?:因为|原因是)?\s*([^。；\n]{2,80})", self.document_type, confidence=0.8)
        return collect(termination, arrears, salary, reason)
