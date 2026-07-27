"""阶段 3.7C 材料、证据、实体规则、法源门禁与旗舰评测。"""

import unittest
import uuid
from unittest.mock import patch

from core.database import Base, SessionLocal, engine
from evals.labor_disputes import load_flagship_cases, run_flagship_dataset
from legal_agent_system.facade import LegalAgentFacade
from legal_agent_system.labor_disputes.dispute_tags import normalize_dispute_tags
from legal_agent_system.labor_disputes.labor_rules import CompensationRule, OvertimePayRule, ProbationRule
from legal_agent_system.labor_disputes.material_adapters import LaborMaterialAdapterRegistry
from legal_agent_system.labor_disputes.schemas import describe_missing_facts
from models.db_models import LegalAuthority, Matter


class Stage37CLaborRulesTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        Base.metadata.create_all(bind=engine)

    def setUp(self):
        self.client_id = f"dhc_stage37c_{uuid.uuid4().hex}"
        self.facade = LegalAgentFacade()
        self.matter_ids = []
        self.authority_ids = []

    def tearDown(self):
        db = SessionLocal()
        try:
            if self.authority_ids:
                db.query(LegalAuthority).filter(
                    LegalAuthority.id.in_(self.authority_ids)
                ).delete(synchronize_session=False)
            for matter_id in self.matter_ids:
                matter = db.get(Matter, matter_id)
                if matter:
                    db.delete(matter)
            db.commit()
        finally:
            db.close()

    def _matter(self):
        matter_id = self.facade.create_matter(self.client_id, "3.7C 青年就业复合争议")["matter_id"]
        self.matter_ids.append(matter_id)
        self.facade.confirm_jurisdiction(matter_id, self.client_id, {
            "country_code": "CN",
            "effective_at": "2026-07-22T00:00:00+00:00",
            "confirmed_by_user": True,
        })
        return matter_id

    def _authority(self):
        row = self.facade.register_test_authority({
            "country_code": "CN",
            "authority_type": "statute",
            "title": "3.7C 实体规则测试来源",
            "provision": "测试条款",
            "text": "劳动争议仲裁时效期间为一年。劳动关系、劳动报酬、安排劳动者延长工作时间、加班费、试用期、解除和经济补偿规则仅用于自动化测试。",
            "source_url": f"https://{uuid.uuid4().hex}.invalid/stage37c",
            "issuing_body": "自动化测试机构",
            "status": "effective",
            "effective_from": "2020-01-01T00:00:00+00:00",
        })
        self.authority_ids.append(row["authority_id"])

    @staticmethod
    def _facts():
        return {
            "employee_name": "张某",
            "employer_name": "某科技公司",
            "employment_start_date": "2025-01-01",
            "termination_date": "2026-07-01",
            "limitation_start_date": "2026-07-01",
            "monthly_salary": 10000,
            "work_location": "北京市",
            "claim_types": ["试用期", "欠薪", "违法解除", "赔偿金"],
            "demands": "请求支付欠薪和违法解除赔偿金",
            "contract_term_months": 24,
            "contract_term_type": "fixed",
            "probation_period_months": 3,
            "probation_salary": 7000,
            "regular_salary": 10000,
            "local_minimum_wage": 2500,
            "wage_arrears_amount": 20000,
            "wage_arrears_start_date": "2026-05-01",
            "wage_arrears_end_date": "2026-06-30",
            "termination_reason": "试用期不符合录用条件",
            "termination_initiator": "employer",
            "termination_basis": "劳动合同法第三十九条",
            "compensation_kind": "damages",
            "local_average_monthly_salary": 12000,
        }

    def test_seven_material_types_are_classified_and_extract_domain_facts(self):
        registry = LaborMaterialAdapterRegistry()
        fixtures = {
            "internship_agreement": ("实习协议.txt", "实习协议 甲方：某公司 乙方：张某 实习津贴每月3000元"),
            "labor_contract": ("劳动合同.txt", "劳动合同 甲方：某公司 乙方：张某 合同期限24个月，试用期2个月，月工资8000元"),
            "offer": ("Offer.txt", "录用通知 Offer 报到日期：2026年7月1日，月薪9000元"),
            "termination_notice": ("解除通知.txt", "解除劳动合同通知书：于2026年7月1日解除，解除原因：不符合录用条件。"),
            "attendance_record": ("考勤表.txt", "2026年6月考勤记录，实际出勤22天。"),
            "payroll_record": ("工资条.txt", "工资条：应发工资9000元，欠付工资18000元。"),
            "chat_record": ("微信聊天记录.txt", "微信聊天记录：欠你的工资18000元，2026年7月1日不用来上班。"),
        }
        for expected, (filename, text) in fixtures.items():
            with self.subTest(document_type=expected):
                result = registry.extract(filename, text)
                self.assertEqual(result["document_type"], expected)
                self.assertTrue(result["candidates"])

    def test_rules_apply_probation_limits_and_statutory_compensation_rounding(self):
        evidence = {"fact_refs": ["fact-1"], "evidence_refs": ["frag-1"], "conflicts": []}
        authorities = [{"authority_id": "law-1"}]
        probation = ProbationRule().evaluate(self._facts(), evidence, authorities)
        self.assertTrue(probation["calculations"]["duration_exceeded"])
        self.assertTrue(probation["calculations"]["salary_below_floor"])

        compensation = CompensationRule().evaluate(self._facts(), evidence, authorities)
        self.assertEqual(compensation["calculations"]["n_months"], 2)
        self.assertEqual(compensation["calculations"]["multiplier"], 2)
        self.assertEqual(compensation["calculations"]["damages_or_compensation"], 40000)

    def test_overtime_rule_uses_separate_rates_and_human_readable_missing_facts(self):
        evidence = {"fact_refs": ["fact-1"], "evidence_refs": ["frag-1"], "conflicts": []}
        authorities = [{"authority_id": "law-1"}]
        result = OvertimePayRule().evaluate({
            "monthly_salary": 8700,
            "working_hours_system": "standard",
            "overtime_workday_hours": 10,
            "overtime_rest_day_hours": 8,
            "overtime_statutory_holiday_hours": 4,
            "rest_day_compensatory_leave_hours": 0,
            "overtime_paid_amount": 500,
        }, evidence, authorities)
        self.assertEqual(result["status"], "completed")
        self.assertEqual(result["calculations"]["hourly_wage_base"], 50)
        self.assertEqual(result["calculations"]["estimated_unpaid_overtime_pay"], 1650)
        self.assertEqual(normalize_dispute_tags(["加班费"]), ["overtime_pay"])
        self.assertEqual(
            describe_missing_facts(["wage_arrears_amount_or_salary_and_months", "wage_arrears_period"]),
            "欠薪金额（或月工资和欠薪月数）、欠薪期间",
        )

    def test_compensation_handles_short_service_and_fails_closed_without_salary_cap_fact(self):
        evidence = {"fact_refs": ["fact-1"], "evidence_refs": [], "conflicts": []}
        authorities = [{"authority_id": "law-1"}]
        short_service = CompensationRule().evaluate({
            "employment_start_date": "2026-07-01",
            "termination_date": "2026-07-02",
            "monthly_salary": 10000,
            "local_average_monthly_salary": 12000,
            "compensation_kind": "compensation",
        }, evidence, authorities)
        self.assertEqual(short_service["calculations"]["n_months"], 0.5)
        self.assertEqual(short_service["calculations"]["compensation"], 5000)
        for end_date, expected_months in (
            ("2026-06-30", 0.5),
            ("2026-07-01", 1),
            ("2027-01-01", 1),
            ("2027-01-02", 1.5),
        ):
            with self.subTest(end_date=end_date):
                boundary = CompensationRule().evaluate({
                    "employment_start_date": "2026-01-01",
                    "termination_date": end_date,
                    "monthly_salary": 10000,
                    "local_average_monthly_salary": 12000,
                    "compensation_kind": "compensation",
                }, evidence, authorities)
                self.assertEqual(boundary["calculations"]["n_months"], expected_months)
        for end_date, expected_months in (("2026-09-29", 0.5), ("2026-09-30", 1)):
            with self.subTest(month_end=end_date):
                month_end = CompensationRule().evaluate({
                    "employment_start_date": "2026-03-31",
                    "termination_date": end_date,
                    "monthly_salary": 10000,
                    "local_average_monthly_salary": 12000,
                    "compensation_kind": "compensation",
                }, evidence, authorities)
                self.assertEqual(month_end["calculations"]["n_months"], expected_months)

        missing_cap = CompensationRule().evaluate({
            "employment_start_date": "2010-01-01",
            "termination_date": "2026-07-01",
            "monthly_salary": 50000,
            "compensation_kind": "compensation",
        }, evidence, authorities)
        self.assertEqual(missing_cap["status"], "information_required")
        self.assertIn("local_average_monthly_salary", missing_cap["missing_facts"])

    def test_composite_runtime_returns_traceable_rule_decisions(self):
        self._authority()
        matter_id = self._matter()
        self.facade.add_material(
            matter_id, self.client_id, "劳动合同.txt",
            "劳动合同 甲方：某科技公司 乙方：张某 合同期限24个月，试用期3个月，试用期工资7000元，转正工资10000元。",
            "text/plain",
        )
        run = self.facade.start_task(matter_id, self.client_id, "labor_case_analysis", self._facts())
        self.assertEqual(run["status"], "completed")
        self.assertEqual(len(run["steps"]), 8)
        output = run["final_output"]["analyze_labor_case"]
        self.assertEqual(len(output["rule_decisions"]), 4)
        for result in output["rule_decisions"]:
            self.assertTrue(result["fact_refs"])
            self.assertTrue(result["authority_refs"])
            self.assertTrue(result["manual_review_required"])
            self.assertFalse(result["legal_conclusion"])
        probation = next(item for item in output["rule_decisions"] if item["issue_tag"] == "probation")
        self.assertTrue(probation["evidence_refs"])

    def test_overtime_claim_runs_as_fifth_composable_rule(self):
        self._authority()
        matter_id = self._matter()
        self.facade.add_material(
            matter_id, self.client_id, "考勤表.txt",
            "2026年6月考勤记录：工作日加班10小时，休息日加班8小时，法定节假日加班4小时。",
            "text/plain",
        )
        facts = self._facts()
        facts.update({
            "claim_types": [*facts["claim_types"], "加班费"],
            "working_hours_system": "standard",
            "overtime_monthly_wage_base": 8700,
            "overtime_workday_hours": 10,
            "overtime_rest_day_hours": 8,
            "overtime_statutory_holiday_hours": 4,
            "rest_day_compensatory_leave_hours": 0,
            "overtime_paid_amount": 500,
        })
        run = self.facade.start_task(matter_id, self.client_id, "labor_case_analysis", facts)
        self.assertEqual(run["status"], "completed")
        decisions = run["final_output"]["analyze_labor_case"]["rule_decisions"]
        self.assertEqual(len(decisions), 5)
        overtime = next(item for item in decisions if item["issue_tag"] == "overtime_pay")
        self.assertEqual(overtime["calculations"]["estimated_unpaid_overtime_pay"], 1650)

    def test_composite_frontend_facts_can_continue_through_approval_to_draft(self):
        self._authority()
        matter_id = self._matter()
        self.facade.add_material(
            matter_id, self.client_id, "劳动合同.txt",
            "劳动合同 甲方：某科技公司 乙方：张某，2025年1月1日入职，月工资10000元，试用期3个月。",
            "text/plain",
        )
        run = self.facade.start_task(
            matter_id, self.client_id, "labor_arbitration_application", self._facts(),
        )
        self.assertEqual(run["status"], "awaiting_approval")
        analysis = run["final_output"]["analyze_labor_dispute"]
        self.assertEqual(len(analysis["rule_decisions"]), 4)
        self.assertTrue(all(item["status"] == "completed" for item in analysis["rule_decisions"]))

        completed = self.facade.continue_task(
            run["run_id"], self.client_id, "approve", {"approved": True},
        )
        self.assertEqual(completed["status"], "completed")
        draft = completed["final_output"]["draft_labor_arbitration_application"]
        self.assertEqual(draft["status"], "draft")
        self.assertIn("劳动仲裁申请书", draft["content"])
        self.assertTrue(draft["authority_refs"])

    def test_complete_rule_facts_without_authority_fail_closed(self):
        matter_id = self._matter()
        with patch.object(self.facade.authorities, "search", return_value=[]):
            run = self.facade.start_task(matter_id, self.client_id, "labor_case_analysis", self._facts())
        self.assertEqual(run["status"], "blocked_authority")
        self.assertEqual(run["error_code"], "AUTHORITY_REQUIRED")

    def test_flagship_dataset_has_five_balanced_categories_and_public_provenance(self):
        self._authority()
        cases = load_flagship_cases()

        def runtime_runner(case, _triage_result):
            matter_id = self._matter()
            material_types = []
            material_fixtures = {
                "youth-016": [("实习协议.txt", "实习协议 甲方：某科技公司 乙方：张某 实习津贴每月3000元"), ("劳动合同.txt", "劳动合同 甲方：某科技公司 乙方：张某 月工资10000元")],
                "youth-017": [("Offer.txt", "录用通知 Offer 月薪10000元"), ("解除通知.txt", "解除劳动合同通知书：于2026年7月1日解除")],
                "youth-018": [("考勤表.txt", "2026年6月考勤记录，实际出勤22天")],
                "youth-019": [("工资条.txt", "工资条：应发工资10000元，欠付工资20000元")],
                "youth-020": [("微信聊天记录.txt", "微信聊天记录：欠你的工资20000元，7月1日不用来上班")],
            }
            for filename, text in material_fixtures.get(case.case_id, []):
                self.facade.add_material(
                    matter_id, self.client_id, filename, text, "text/plain",
                )
                material_types.append(
                    LaborMaterialAdapterRegistry().extract(filename, text)["document_type"]
                )
            triage_run = self.facade.start_task(
                matter_id, self.client_id, "labor_relationship_assessment", case.facts,
            )
            analysis_run = None
            if case.category == "composite":
                facts = self._facts()
                facts["claim_types"] = list(case.facts.get("claim_types") or [])
                facts["compensation_kind"] = (
                    "damages" if "赔偿金" in facts["claim_types"] else "compensation"
                )
                analysis_run = self.facade.start_task(
                    matter_id, self.client_id, "labor_case_analysis", facts,
                )
            return {
                "triage_run": triage_run,
                "analysis_run": analysis_run,
                "material_types": material_types,
            }

        report = run_flagship_dataset(cases, runtime_runner=runtime_runner)
        self.assertEqual(report["total"], 25)
        self.assertEqual(report["failed"], 0)
        self.assertEqual(set(report["categories"].values()), {5})
        self.assertGreaterEqual(report["provenance"].get("official_public_adaptation", 0), 5)
        self.assertEqual(report["runtime_exercised"], 25)
        self.assertEqual(report["analysis_exercised"], 5)
        self.assertEqual(len(report["material_types_covered"]), 7)


if __name__ == "__main__":
    unittest.main()
