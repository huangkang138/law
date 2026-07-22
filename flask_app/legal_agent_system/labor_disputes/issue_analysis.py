"""3.7C 劳动争议实体规则入口；返回统一可追溯规则结果。"""

from typing import Dict


class LaborIssueAnalysisService:
    def __init__(self, labor_disputes) -> None:
        self.labor_disputes = labor_disputes

    def wage_arrears(self, matter_id: str, client_id: str) -> Dict:
        return self.labor_disputes.evaluate_rule(matter_id, client_id, "wage_arrears")

    def probation(self, matter_id: str, client_id: str) -> Dict:
        return self.labor_disputes.evaluate_rule(matter_id, client_id, "probation")

    def termination(self, matter_id: str, client_id: str) -> Dict:
        return self.labor_disputes.evaluate_rule(matter_id, client_id, "termination")

    def economic_compensation(self, matter_id: str, client_id: str) -> Dict:
        return self.labor_disputes.evaluate_rule(matter_id, client_id, "economic_compensation")
