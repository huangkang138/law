"""阶段 3.7B 主模板、争议标签、白名单步骤和 revision 测试。"""

import unittest
import uuid

from core.database import Base, SessionLocal, engine
from legal_agent_system.capabilities import TemplatePlanBuilder
from legal_agent_system.facade import LegalAgentFacade
from legal_agent_system.models import AgentPlan
from models.db_models import LegalAuthority, Matter


class Stage37BCompositePlanTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        Base.metadata.create_all(bind=engine)

    def setUp(self):
        self.client_id = f"dhc_stage37b_{uuid.uuid4().hex}"
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

    def _matter(self, goal="阶段 3.7B 复合劳动争议"):
        matter_id = self.facade.create_matter(self.client_id, goal)["matter_id"]
        self.matter_ids.append(matter_id)
        self.facade.confirm_jurisdiction(matter_id, self.client_id, {
            "country_code": "CN",
            "effective_at": "2026-07-21T00:00:00+00:00",
            "confirmed_by_user": True,
        })
        return matter_id

    def _authority(self):
        authority = self.facade.register_test_authority({
            "country_code": "CN",
            "authority_type": "statute",
            "title": "阶段 3.7B 劳动争议仲裁时效测试来源",
            "provision": "测试条款",
            "text": "劳动争议仲裁时效期间为一年。劳动报酬、解除、经济补偿与试用期规则均仅用于自动化测试。",
            "source_url": f"https://{uuid.uuid4().hex}.invalid/stage37b",
            "issuing_body": "自动化测试机构",
            "status": "effective",
            "effective_from": "2020-01-01T00:00:00+00:00",
        })
        self.authority_ids.append(authority["authority_id"])

    @staticmethod
    def _facts(**extra):
        return {
            "employee_name": "测试申请人",
            "employer_name": "测试公司",
            "employment_start_date": "2022-01-01",
            "limitation_start_date": "2026-01-10",
            "monthly_salary": 12000,
            "work_location": "北京市",
            "claim_types": ["经济补偿"],
            "demands": "请求分析劳动争议处理方案",
            **extra,
        }

    def test_main_template_composes_and_skips_whitelisted_issue_steps(self):
        template = self.facade.capabilities.get_template("labor_case_analysis")
        builder = TemplatePlanBuilder()
        wage_only = builder.build(
            template,
            {"facts": {}, "dispute_tags": ["wage_arrears"]},
            requested_task_type="labor_case_analysis",
        )
        statuses = {step.step_id: step for step in wage_only.steps}
        self.assertEqual(statuses["wage_arrears_analysis"].status, "pending")
        self.assertEqual(statuses["wage_arrears_analysis"].triggered_by_tags, ["wage_arrears"])
        self.assertEqual(statuses["overtime_pay_analysis"].status, "skipped")
        self.assertEqual(statuses["termination_analysis"].status, "skipped")
        self.assertTrue(statuses["termination_analysis"].skip_reason)
        self.assertEqual(statuses["economic_compensation_analysis"].status, "skipped")

        composite = builder.build(
            template,
            {
                "facts": {"termination_date": "2026-06-01"},
                "dispute_tags": [
                    "wage_arrears", "termination", "economic_compensation",
                ],
            },
            requested_task_type="labor_case_analysis",
        )
        step_ids = [step.step_id for step in composite.steps]
        self.assertEqual(len(step_ids), len(set(step_ids)))
        self.assertEqual(step_ids.count("evidence_check"), 1)
        for step_id in (
            "wage_arrears_analysis", "termination_analysis",
            "economic_compensation_analysis",
        ):
            self.assertEqual(next(s for s in composite.steps if s.step_id == step_id).status, "pending")

    def test_unknown_tag_and_tool_override_fail_closed(self):
        template = self.facade.capabilities.get_template("labor_case_analysis")
        builder = TemplatePlanBuilder()
        with self.assertRaises(ValueError):
            builder.build(
                template,
                {"facts": {}, "dispute_tags": ["unregistered_claim"]},
                requested_task_type="labor_case_analysis",
            )

        revision = builder.build(
            template,
            {"facts": {}, "dispute_tags": ["wage_arrears"]},
            requested_task_type="labor_case_analysis",
        )
        revision.steps[2].tool_name = "draft_labor_arbitration_application"
        with self.assertRaises(ValueError):
            self.facade.capabilities.validate_plan(revision)

    def test_runtime_rejects_unknown_claim_without_executing_steps(self):
        matter_id = self._matter("未知争议标签失败关闭")
        run = self.facade.start_task(
            matter_id,
            self.client_id,
            "labor_case_analysis",
            self._facts(claim_types=["股票争议"]),
        )
        self.assertEqual(run["status"], "failed")
        self.assertEqual(run["error_code"], "INVALID_PLAN_COMPOSITION")
        self.assertEqual(run["steps"], [])

    def test_new_facts_create_revision_and_enable_new_issue_steps(self):
        self._authority()
        matter_id = self._matter()
        first = self.facade.start_task(
            matter_id,
            self.client_id,
            "labor_case_analysis",
            self._facts(),
        )
        self.assertEqual(first["status"], "awaiting_information")
        self.assertEqual(first["plan_revision"], 1)
        self.assertEqual(first["dispute_tags"], ["economic_compensation"])

        second = self.facade.continue_task(
            first["run_id"],
            self.client_id,
            "provide_information",
            {
                "termination_date": "2026-06-01",
                "termination_reason": "用人单位通知解除",
                "wage_arrears_amount": 24000,
                "wage_arrears_start_date": "2026-04-01",
                "wage_arrears_end_date": "2026-05-31",
                "termination_initiator": "employer",
                "claim_types": ["欠薪", "违法解除", "经济补偿"],
                "local_average_monthly_salary": 12000,
            },
        )
        self.assertEqual(second["status"], "completed")
        self.assertEqual(second["plan_revision"], 2)
        self.assertEqual(second["dispute_tags"], [
            "wage_arrears", "termination", "economic_compensation",
        ])
        self.assertEqual(len(second["steps"]), 8)
        self.assertEqual(sum(s["step_type"] == "evidence_analysis" for s in second["steps"]), 1)

        db = SessionLocal()
        try:
            plans = db.query(AgentPlan).filter(
                AgentPlan.run_id == first["run_id"]
            ).order_by(AgentPlan.version).all()
            self.assertEqual([plan.version for plan in plans], [1, 2])
            self.assertEqual(plans[1].parent_plan_id, plans[0].id)
            self.assertTrue(plans[1].replan_reason)
            self.assertEqual(plans[0].plan_json["dispute_tags"], ["economic_compensation"])
            self.assertEqual(plans[1].plan_json["dispute_tags"], [
                "wage_arrears", "termination", "economic_compensation",
            ])
            first_steps = {s["step_id"]: s for s in plans[0].plan_json["steps"]}
            second_steps = {s["step_id"]: s for s in plans[1].plan_json["steps"]}
            self.assertEqual(first_steps["termination_analysis"]["status"], "skipped")
            self.assertEqual(second_steps["termination_analysis"]["status"], "pending")
        finally:
            db.close()

    def test_arbitration_allows_two_information_rounds_without_exhausting_budget(self):
        self._authority()
        matter_id = self._matter("两轮补充事实预算测试")
        started = self.facade.start_task(
            matter_id,
            self.client_id,
            "labor_arbitration_application",
            self._facts(
                claim_types=["欠薪", "违法解除", "经济补偿"],
                termination_date="2026-06-01",
                termination_reason="用人单位通知解除",
                termination_initiator="employer",
            ),
        )
        self.assertEqual(started["status"], "awaiting_information")

        wage_supplied = self.facade.continue_task(
            started["run_id"],
            self.client_id,
            "provide_information",
            {
                "wage_arrears_amount": 24000,
                "wage_arrears_start_date": "2026-04-01",
                "wage_arrears_end_date": "2026-05-31",
            },
        )
        self.assertEqual(wage_supplied["status"], "awaiting_information")

        ready = self.facade.continue_task(
            started["run_id"],
            self.client_id,
            "provide_information",
            {"local_average_monthly_salary": 12000},
        )
        self.assertEqual(ready["status"], "awaiting_approval")
        self.assertGreaterEqual(ready["max_tool_calls"], 16)
        self.assertNotEqual(ready["error_code"], "BUDGET_EXCEEDED")


if __name__ == "__main__":
    unittest.main()
