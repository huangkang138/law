import re

from .common import DATE, MONEY, collect, first, iso_date


class AgreementAdapter:
    def __init__(self, document_type: str, keywords: tuple[str, ...]) -> None:
        self.document_type = document_type
        self.keywords = keywords

    def extract(self, text: str):
        kind = self.document_type
        employee = first(text, "employee_name", r"(?:乙方|劳动者|实习生)[：:\s]*([\u4e00-\u9fa5·]{2,12})", kind)
        employer = first(text, "employer_name", r"(?:甲方|用人单位|实习单位)[：:\s]*([^\n，。；]{2,60}?(?:公司|中心|事务所|单位|组织))", kind)
        start = first(text, "employment_start_date", rf"(?:入职|用工|实习|合同期限[^\n]{{0,20}}自)[^\d]{{0,8}}{DATE}", kind, lambda m: iso_date(m, 1))
        salary = first(text, "monthly_salary", rf"(?:月工资|劳动报酬|实习津贴|薪资)[^\d]{{0,15}}{MONEY}", kind, lambda m: float(m.group(1)))
        term = first(text, "contract_term_months", r"(?:合同期限|期限)[^\d]{0,8}(\d{1,3})\s*个?月", kind, lambda m: int(m.group(1)))
        probation = first(text, "probation_period_months", r"试用期[^\d]{0,8}(\d{1,2})\s*个?月", kind, lambda m: int(m.group(1)))
        probation_salary = first(text, "probation_salary", rf"试用期工资[^\d]{{0,8}}{MONEY}", kind, lambda m: float(m.group(1)))
        regular_salary = first(text, "regular_salary", rf"(?:转正后|正式)工资[^\d]{{0,8}}{MONEY}", kind, lambda m: float(m.group(1)))
        return collect(employee, employer, start, salary, term, probation, probation_salary, regular_salary)


class OfferAdapter(AgreementAdapter):
    def __init__(self) -> None:
        super().__init__("offer", ("offer", "录用通知", "聘用通知", "入职邀请"))

    def extract(self, text: str):
        items = super().extract(text)
        start = first(text, "employment_start_date", rf"(?:报到|入职)日期[：:\s]*{DATE}", self.document_type, lambda m: iso_date(m, 1), 0.94)
        return [item for item in items if item.field != "employment_start_date"] + ([start] if start else [])


def default_agreement_adapters():
    return [
        AgreementAdapter("internship_agreement", ("实习协议", "实习单位", "实习生", "实习津贴")),
        AgreementAdapter("labor_contract", ("劳动合同", "用人单位", "劳动者", "合同期限")),
        OfferAdapter(),
    ]
