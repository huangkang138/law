"""阶段 3.1 劳动纠纷 LangGraph 融合测试。"""

import unittest
import uuid
from unittest.mock import patch

from core.database import Base, SessionLocal, engine
from legal_agent_system.facade import LegalAgentFacade
from models.db_models import AgentRun, AgentStep, LegalAuthority, Matter, ToolCall


class DigitalHumanStage31RuntimeIntegrationTest(unittest.TestCase):
    """验证法域/事实暂停、真实工具、来源阻断、审批恢复和审计。"""

    @classmethod
    def setUpClass(cls):
        Base.metadata.create_all(bind=engine)

    def setUp(self):
        self.client_id = f"dhc_stage31_{uuid.uuid4().hex}"
        self.facade = LegalAgentFacade()
        self.matter_id = self.facade.create_matter(self.client_id, "劳动纠纷 Runtime 融合测试")["matter_id"]
        self.run_id = None
        self.authority_ids = []

    def tearDown(self):
        db = SessionLocal()
        try:
            if self.authority_ids:
                db.query(LegalAuthority).filter(LegalAuthority.id.in_(self.authority_ids)).delete(synchronize_session=False)
            matter = db.get(Matter, self.matter_id)
            if matter:
                db.delete(matter)
            db.commit()
        finally:
            db.close()

    def test_labor_runtime_pause_block_retry_approve_and_complete(self):
        started = self.facade.start_labor_dispute_run(self.matter_id, self.client_id, {
            "employee_name": "测试申请人", "employer_name": "测试公司",
        })
        self.run_id = started["run_id"]
        self.assertEqual(started["task_type"], "cn_labor_dispute")
        self.assertEqual(started["status"], "awaiting_jurisdiction")

        waiting = self.facade.continue_labor_dispute_run(
            self.run_id, self.client_id, "confirm_jurisdiction", {
                "country_code": "CN", "effective_at": "2026-07-13T00:00:00+00:00",
                "confirmed_by_user": True,
            },
        )
        self.assertEqual(waiting["status"], "awaiting_information")
        self.assertIn("monthly_salary", waiting["missing_facts"])

        # 显式模拟来源服务不可用，不依赖共享数据库是否已安装生产法源。
        with patch.object(self.facade.labor_disputes, "_verified_authorities", return_value=[]):
            blocked = self.facade.continue_labor_dispute_run(
                self.run_id, self.client_id, "provide_information", {
                    "employment_start_date": "2022-01-01", "limitation_start_date": "2026-01-10",
                    "monthly_salary": 12000, "work_location": "北京市",
                    "claim_types": ["违法解除"], "demands": "请求支付解除劳动合同赔偿金",
                    "termination_date": "2026-01-15", "termination_reason": "组织架构调整",
                    "termination_initiator": "employer",
                },
            )
        self.assertEqual(blocked["status"], "blocked_authority")
        self.assertEqual([step["tool_name"] for step in blocked["steps"]], [
            "generate_evidence_checklist", "analyze_probation", "analyze_wage_arrears",
            "analyze_overtime_pay",
            "analyze_labor_termination", "analyze_economic_compensation",
            "analyze_labor_dispute",
            "draft_labor_arbitration_application",
        ])

        authority = self.facade.register_test_authority({
            "country_code": "CN", "authority_type": "statute",
            "title": "劳动争议仲裁时效 Runtime 测试来源", "provision": "测试条款",
            "text": "劳动争议仲裁时效期间为一年。解除规则仅用于自动化测试。",
            "source_url": "https://example.invalid/stage31-authority",
            "issuing_body": "自动化测试机构", "status": "effective",
            "effective_from": "2020-01-01T00:00:00+00:00",
        })
        self.authority_ids.append(authority["authority_id"])
        approval = self.facade.continue_labor_dispute_run(
            self.run_id, self.client_id, "retry_authority",
        )
        self.assertEqual(approval["status"], "awaiting_approval")
        self.assertIsNotNone(approval["approval"])
        analysis_step = next(
            step for step in approval["steps"]
            if step["tool_name"] == "analyze_labor_dispute"
        )
        self.assertEqual(analysis_step["status"], "completed")

        # 新 Facade 模拟服务重启，确认运行只依赖 PostgreSQL 状态。
        completed = LegalAgentFacade().continue_labor_dispute_run(
            self.run_id, self.client_id, "approve", {"approved": True},
        )
        self.assertEqual(completed["status"], "completed")
        draft_step = next(
            step for step in completed["steps"]
            if step["tool_name"] == "draft_labor_arbitration_application"
        )
        self.assertEqual(draft_step["status"], "completed")
        self.assertEqual(len(completed["final_artifact_ids"]), 1)

        db = SessionLocal()
        try:
            tool_names = [row.tool_name for row in db.query(ToolCall).filter(ToolCall.run_id == self.run_id).all()]
            self.assertIn("generate_evidence_checklist", tool_names)
            self.assertIn("analyze_labor_dispute", tool_names)
            self.assertIn("draft_labor_arbitration_application", tool_names)
            self.assertEqual(db.query(AgentStep).filter(AgentStep.run_id == self.run_id).count(), 8)
            self.assertEqual(db.get(AgentRun, self.run_id).status, "completed")
        finally:
            db.close()

        events = self.facade.get_audit(self.run_id, self.client_id)
        event_types = [item["type"] for item in events]
        self.assertIn("run_waiting_for_jurisdiction", event_types)
        self.assertIn("run_waiting_for_information", event_types)
        self.assertIn("run_blocked", event_types)
        self.assertIn("run_paused_for_approval", event_types)
        self.assertIn("run_completed", event_types)

    def test_rejecting_draft_keeps_completed_analysis_step(self):
        self.facade.confirm_jurisdiction(self.matter_id, self.client_id, {
            "country_code": "CN", "effective_at": "2026-07-13T00:00:00+00:00",
            "confirmed_by_user": True,
        })
        authority = self.facade.register_test_authority({
            "country_code": "CN", "authority_type": "statute",
            "title": "劳动争议仲裁时效拒绝测试来源", "provision": "测试条款",
            "text": "劳动争议仲裁时效期间为一年。解除规则仅用于自动化测试。",
            "source_url": "https://example.invalid/stage31-reject", "issuing_body": "自动化测试机构",
            "status": "effective", "effective_from": "2020-01-01T00:00:00+00:00",
        })
        self.authority_ids.append(authority["authority_id"])
        waiting = self.facade.start_labor_dispute_run(self.matter_id, self.client_id, {
            "employee_name": "测试申请人", "employer_name": "测试公司",
            "employment_start_date": "2022-01-01", "limitation_start_date": "2026-01-10",
            "monthly_salary": 12000, "work_location": "北京市",
            "claim_types": ["违法解除"], "demands": "请求支付赔偿金",
            "termination_date": "2026-01-15", "termination_reason": "组织架构调整",
            "termination_initiator": "employer",
        })
        self.run_id = waiting["run_id"]
        self.assertEqual(waiting["status"], "awaiting_approval")
        cancelled = self.facade.continue_labor_dispute_run(
            self.run_id, self.client_id, "approve", {"approved": False},
        )
        self.assertEqual(cancelled["status"], "cancelled")
        analysis_step = next(
            step for step in cancelled["steps"]
            if step["tool_name"] == "analyze_labor_dispute"
        )
        draft_step = next(
            step for step in cancelled["steps"]
            if step["tool_name"] == "draft_labor_arbitration_application"
        )
        self.assertEqual(analysis_step["status"], "completed")
        self.assertEqual(draft_step["status"], "pending")


if __name__ == "__main__":
    unittest.main()
