"""阶段 3.6 通用 Runtime、能力注册和计划修订测试。"""

import unittest
import uuid
from unittest.mock import patch

from flask import Flask

from core.database import Base, SessionLocal, engine
from legal_agent_system.capabilities import TemplatePlanBuilder
from legal_agent_system.facade import LegalAgentFacade
from legal_agent_system.models import AgentPlan
from legal_agent_system.runtime.decision_router import DecisionRouter
from legal_agent_system.runtime.errors import AgentRuntimeError
from legal_agent_system.runtime.schemas import ToolResult
from models.db_models import LegalAuthority, Matter
from routers import digital_human_agent


class Stage36CapabilityRuntimeTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        Base.metadata.create_all(bind=engine)

    def setUp(self):
        self.client_id = f"dhc_stage36_{uuid.uuid4().hex}"
        self.facade = LegalAgentFacade()
        self.matter_ids = []
        self.authority_ids = []

    def tearDown(self):
        db = SessionLocal()
        try:
            if self.authority_ids:
                db.query(LegalAuthority).filter(LegalAuthority.id.in_(self.authority_ids)).delete(synchronize_session=False)
            for matter_id in self.matter_ids:
                matter = db.get(Matter, matter_id)
                if matter:
                    db.delete(matter)
            db.commit()
        finally:
            db.close()

    def _matter(self, goal="阶段 3.6 劳动任务"):
        matter_id = self.facade.create_matter(self.client_id, goal)["matter_id"]
        self.matter_ids.append(matter_id)
        self.facade.confirm_jurisdiction(matter_id, self.client_id, {
            "country_code": "CN",
            "effective_at": "2026-07-16T00:00:00+00:00",
            "confirmed_by_user": True,
        })
        return matter_id

    def _authority(self):
        authority = self.facade.register_test_authority({
            "country_code": "CN", "authority_type": "statute",
            "title": "阶段 3.6 劳动争议仲裁时效测试来源", "provision": "测试条款",
            "text": "劳动争议仲裁时效期间为一年。解除规则仅用于自动化测试。",
            "source_url": f"https://{uuid.uuid4().hex}.invalid/stage36",
            "issuing_body": "自动化测试机构", "status": "effective",
            "effective_from": "2020-01-01T00:00:00+00:00",
        })
        self.authority_ids.append(authority["authority_id"])

    @staticmethod
    def _facts(**extra):
        return {
            "employee_name": "测试申请人", "employer_name": "测试公司",
            "employment_start_date": "2022-01-01", "limitation_start_date": "2026-01-10",
            "monthly_salary": 12000, "work_location": "北京市",
            "claim_types": ["违法解除"], "demands": "请求分析劳动争议处理方案",
            "termination_date": "2026-01-15", "termination_reason": "组织架构调整",
            "termination_initiator": "employer",
            **extra,
        }

    def test_registry_and_graph_are_template_agnostic(self):
        capabilities = self.facade.list_agent_capabilities()
        self.assertEqual(capabilities[0]["domain_id"], "cn_labor")
        self.assertEqual({item["template_id"] for item in capabilities[0]["templates"]}, {
            "labor_relationship_assessment", "labor_arbitration_application",
            "labor_consultation", "labor_case_analysis",
        })
        nodes = self.facade.capability_runtime.graph.NODE_NAMES
        self.assertTrue({
            "select_next_step", "execute_step", "observe_step", "verify_step", "decide_step",
        }.issubset(nodes))
        self.assertNotIn("draft_labor_arbitration_application", nodes)
        self.assertNotIn("route_task", nodes)

        resolved = self.facade.capabilities.resolve("cn_labor_dispute")
        self.assertEqual(resolved.domain.domain_id, "cn_labor")
        self.assertEqual(resolved.template.template_id, "labor_arbitration_application")

    def test_capability_endpoint_wraps_list_in_success_envelope(self):
        app = Flask(__name__)
        app.register_blueprint(digital_human_agent.router, url_prefix="/api")
        with patch.object(
            digital_human_agent, "get_legal_agent_facade", return_value=self.facade,
        ):
            response = app.test_client().get(
                "/api/digital-human/agent/capabilities",
            )
        payload = response.get_json()
        self.assertEqual(response.status_code, 200)
        self.assertTrue(payload["success"])
        self.assertEqual(payload["capabilities"][0]["domain_id"], "cn_labor")

    def test_optional_step_records_skip_reason_and_router_is_independent(self):
        template = self.facade.capabilities.get_template("labor_case_analysis")
        facts = self._facts()
        facts.pop("termination_date")
        revision = TemplatePlanBuilder().build(
            template, {"facts": facts}, requested_task_type="labor_case_analysis",
        )
        self.assertEqual(revision.steps[0].status, "skipped")
        self.assertIn("未提供解除日期", revision.steps[0].skip_reason)

        retry = DecisionRouter().decide(
            ToolResult(tool_call_id="tool_retry", success=False, error_code="TEMP", retryable=True),
            {"valid": False, "reports": [{"valid": False, "decision_hint": "retry"}]},
            on_failure="retry", has_next_step=True,
        )
        replan = DecisionRouter().decide(
            ToolResult(tool_call_id="tool_replan", success=True, data={}),
            {"valid": False, "reports": [{"valid": False, "decision_hint": "replan"}]},
            on_failure="replan", has_next_step=True,
        )
        self.assertEqual(retry["action"], "retry_step")
        self.assertEqual(replan["action"], "replan")

    def test_plan_revisions_are_append_only(self):
        matter_id = self._matter("计划修订不可覆盖")
        state = self.facade.repository.create_run_for_matter(matter_id, self.client_id, "labor_consultation")
        template = self.facade.capabilities.get_template("labor_consultation")
        builder = TemplatePlanBuilder()
        first = builder.build(template, {"facts": self._facts()}, requested_task_type="labor_consultation")
        self.facade.repository.persist_plan_revision(state, first)
        first_plan_id = state.plan_id
        second = builder.build(
            template,
            {"facts": self._facts(monthly_salary=15000)},
            requested_task_type="labor_consultation",
            replan_reason="用户修正月工资",
            triggered_by="user",
        )
        self.facade.repository.persist_plan_revision(state, second)
        db = SessionLocal()
        try:
            plans = db.query(AgentPlan).filter(AgentPlan.run_id == state.run_id).order_by(AgentPlan.version).all()
            self.assertEqual([item.version for item in plans], [1, 2])
            self.assertEqual(plans[0].id, first_plan_id)
            self.assertIsNone(plans[0].replan_reason)
            self.assertEqual(plans[1].replan_reason, "用户修正月工资")
            self.assertEqual(plans[1].parent_plan_id, plans[0].id)
        finally:
            db.close()

    def test_continue_request_resolves_capability_once(self):
        matter_id = self._matter("继续任务单次能力解析")
        waiting = self.facade.start_task(matter_id, self.client_id, "labor_consultation")
        self.assertEqual(waiting["status"], "awaiting_information")

        with patch.object(
            self.facade.capabilities, "resolve", wraps=self.facade.capabilities.resolve,
        ) as resolve:
            self.facade.continue_task(
                waiting["run_id"], self.client_id, "provide_information", self._facts(),
            )
            self.assertEqual(resolve.call_count, 1)

    def test_graph_rejects_unbound_run(self):
        matter_id = self._matter("禁止绕过 Runtime 直接调用 Graph")
        state = self.facade.repository.create_run_for_matter(
            matter_id, self.client_id, "labor_consultation",
        )
        with self.assertRaises(AgentRuntimeError) as caught:
            self.facade.capability_runtime.graph.invoke(state)
        self.assertEqual(caught.exception.code, "CAPABILITY_NOT_RESOLVED")

    def test_three_labor_tasks_share_runtime_and_readonly_tasks_finish(self):
        self._authority()
        consultation_matter = self._matter("劳动法律咨询")
        with patch.object(
            self.facade.capabilities, "resolve", wraps=self.facade.capabilities.resolve,
        ) as resolve:
            consultation = self.facade.start_task(
                consultation_matter, self.client_id, "labor_consultation", self._facts(),
            )
            self.assertEqual(resolve.call_count, 1)
        self.assertEqual(consultation["status"], "completed")
        self.assertEqual(consultation["template_id"], "labor_consultation")
        self.assertEqual(len(consultation["steps"]), 2)
        self.assertEqual(consultation["final_artifact_ids"], [])

        analysis_matter = self._matter("劳动案件分析")
        analysis = self.facade.start_task(
            analysis_matter, self.client_id, "labor_case_analysis", self._facts(),
        )
        self.assertEqual(analysis["status"], "completed")
        self.assertEqual(analysis["template_id"], "labor_case_analysis")
        self.assertEqual(analysis["steps"][0]["status"], "completed")
        self.assertTrue(analysis["steps"][-1]["verification"]["reports"])


if __name__ == "__main__":
    unittest.main()
