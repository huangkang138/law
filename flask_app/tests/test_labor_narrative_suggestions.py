"""叙述式劳动争议摘要只生成带出处的表单候选。"""

import unittest
from types import SimpleNamespace
from unittest.mock import MagicMock, patch

from legal_agent_system.labor_disputes.material_adapters.narrative import NarrativeSummaryAdapter
from legal_agent_system.labor_disputes.suggestions import LaborFactSuggestionService


CASE_TEXT = (
    "【虚构测试案例，非真实案件】\n"
    "申请人林知远于2023年3月1日入职云衡信息技术（测试）有限公司，担任软件测试工程师，"
    "实际工作地点为杭州市滨江区。劳动合同约定税前月工资9800元，每月10日发放上月工资，实行标准工时制。\n"
    "公司已支付工资至2026年4月30日。2026年5月工资9800元、6月1日至15日工资4900元尚未支付，合计14700元。\n"
    "2026年3月至5月项目上线期间，项目负责人安排林知远工作日加班20小时、休息日加班16小时、"
    "法定节假日加班8小时。公司未安排补休，也未支付加班费。\n"
    "2026年6月15日，公司以“严重违反考勤制度”为由，当日通知林知远解除劳动合同。"
    "劳动关系现已解除。\n"
    "林知远拟请求：支付欠薪14700元、核算并支付加班费、支付违法解除劳动合同赔偿金。\n"
    "原始劳动合同、银行流水、考勤记录及公司规章制度尚未提供，需标记为待核实，"
    "不应直接认定违法解除或确定最终金额。"
)


class NarrativeSummaryAdapterTest(unittest.TestCase):
    def test_explicit_case_facts_become_locatable_candidates(self):
        candidates = NarrativeSummaryAdapter().extract(CASE_TEXT)
        values = {item.field: item.value for item in candidates}
        self.assertEqual(values["employee_name"], "林知远")
        self.assertEqual(values["termination_date"], "2026-06-15")
        self.assertEqual(values["wage_arrears_amount"], 14700)
        self.assertEqual(values["wage_arrears_start_date"], "2026-05-01")
        self.assertEqual(values["wages_paid_through"], "2026-04-30")
        self.assertEqual(values["wage_payment_day"], 10)
        self.assertEqual(values["working_hours_system"], "standard")
        self.assertEqual(values["overtime_workday_hours"], 20)
        self.assertEqual(values["overtime_rest_day_hours"], 16)
        self.assertEqual(values["overtime_statutory_holiday_hours"], 8)
        self.assertEqual(values["rest_day_compensatory_leave_hours"], 0)
        self.assertEqual(values["overtime_paid_amount"], 0)
        self.assertEqual(values["employment_active"], "false")
        self.assertEqual(values["termination_initiator"], "employer")
        self.assertEqual(values["termination_reason"], "严重违反考勤制度")
        self.assertEqual(values["compensation_kind"], "damages")
        self.assertIn("支付欠薪14700元", values["demands"])
        self.assertNotIn("local_average_monthly_salary", values)
        self.assertTrue(all(CASE_TEXT[item.start_offset:item.end_offset] == item.quote for item in candidates))

    def test_missing_evidence_and_legal_caveat_do_not_become_case_conclusions(self):
        text = "原始合同和银行流水尚未提供，不应直接认定违法解除或确定最终金额。"
        self.assertEqual(NarrativeSummaryAdapter().extract(text), [])
        self.assertEqual(LaborFactSuggestionService._claim_types(text), [])
        mixed_pay = "2026年5月工资已支付，2026年6月工资尚未支付。"
        values = {item.field: item.value for item in NarrativeSummaryAdapter().extract(mixed_pay)}
        self.assertEqual(values["wage_arrears_start_date"], "2026-06-01")

    def test_service_exposes_candidates_without_confirming_facts(self):
        document = SimpleNamespace(id="doc-1", filename="虚构摘要.txt", content=CASE_TEXT)
        db = MagicMock()
        documents_query = MagicMock()
        documents_query.filter.return_value = documents_query
        documents_query.order_by.return_value = documents_query
        documents_query.all.return_value = [document]
        facts_query = MagicMock()
        facts_query.filter.return_value = facts_query
        facts_query.order_by.return_value = facts_query
        facts_query.all.return_value = []
        db.query.side_effect = [documents_query, facts_query]
        materials = MagicMock()
        service = LaborFactSuggestionService(materials)
        service.adapters.extract = lambda _filename, _content: {"document_type": "unknown", "candidates": []}

        with patch("legal_agent_system.labor_disputes.suggestions.SessionLocal", return_value=db):
            result = service.suggest("matter-1", "client-1")

        self.assertEqual(result["suggested_facts"]["working_hours_system"], "standard")
        self.assertEqual(result["suggested_facts"]["overtime_workday_hours"], 20)
        self.assertEqual(result["suggested_facts"]["employment_active"], "false")
        self.assertNotIn("local_average_monthly_salary", result["suggested_facts"])
        self.assertTrue(all(item["sources"][0]["document_id"] == "doc-1" for item in result["fields"]))
        materials.get_matter.assert_called_once_with("matter-1", "client-1")
        db.close.assert_called_once()


if __name__ == "__main__":
    unittest.main()
