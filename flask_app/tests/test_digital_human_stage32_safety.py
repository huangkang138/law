"""阶段 3.2 验证、预算、审批过期和交付物幂等测试。"""

import unittest
import uuid
from datetime import datetime, timedelta, timezone

from core.database import Base, SessionLocal, engine
from legal_agent_system.facade import LegalAgentFacade
from legal_agent_system.runtime.errors import AgentRuntimeError
from legal_agent_system.runtime.schemas import AgentState, ToolResult
from legal_agent_system.domains.labor.verifier import LaborResultVerifier
from models.db_models import AgentArtifact, ApprovalRequest, LegalAuthority, Matter, ToolCall


class DigitalHumanStage32SafetyIntegrationTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        Base.metadata.create_all(bind=engine)

    def setUp(self):
        self.client_id = f"dhc_stage32_{uuid.uuid4().hex}"
        self.facade = LegalAgentFacade()
        self.matter_id = self.facade.create_matter(self.client_id, "阶段3.2安全边界测试")["matter_id"]
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

    def _prepare_complete_matter(self):
        self.facade.confirm_jurisdiction(self.matter_id, self.client_id, {
            "country_code": "CN", "effective_at": "2026-07-13T00:00:00+00:00",
            "confirmed_by_user": True,
        })
        facts = {
            "employee_name": "测试申请人", "employer_name": "测试公司",
            "employment_start_date": "2022-01-01", "limitation_start_date": "2026-01-10",
            "monthly_salary": 12000, "work_location": "北京市",
            "claim_types": ["违法解除"], "demands": "请求支付赔偿金",
            "termination_date": "2026-01-15", "termination_reason": "组织架构调整",
            "termination_initiator": "employer",
        }
        self.facade.update_labor_dispute_facts(self.matter_id, self.client_id, facts)
        authority = self.facade.register_test_authority({
            "country_code": "CN", "authority_type": "statute",
            "title": "劳动争议仲裁时效阶段3.2测试来源", "provision": "测试条款",
            "text": "劳动争议仲裁时效期间为一年。解除规则仅用于自动化测试。",
            "source_url": "https://example.invalid/stage32-authority",
            "issuing_body": "自动化测试机构", "status": "effective",
            "effective_from": "2020-01-01T00:00:00+00:00",
        })
        self.authority_ids.append(authority["authority_id"])
        return facts

    def test_expired_approval_cannot_resume(self):
        facts = self._prepare_complete_matter()
        waiting = self.facade.start_labor_dispute_run(self.matter_id, self.client_id, facts)
        db = SessionLocal()
        try:
            approval = db.get(ApprovalRequest, waiting["approval"]["id"])
            approval.expires_at = datetime.now(timezone.utc) - timedelta(minutes=1)
            db.commit()
        finally:
            db.close()
        with self.assertRaises(AgentRuntimeError) as caught:
            self.facade.continue_labor_dispute_run(
                waiting["run_id"], self.client_id, "approve", {"approved": True},
            )
        self.assertEqual(caught.exception.code, "APPROVAL_EXPIRED")

    def test_tool_budget_stops_run_before_call(self):
        self._prepare_complete_matter()
        state = self.facade.repository.create_run_for_matter(
            self.matter_id, self.client_id, "cn_labor_dispute",
        )
        state.max_tool_calls = 0
        self.facade.repository.save_state(state, "test_budget_configured")
        snapshot = self.facade.start_task(self.matter_id, self.client_id, "cn_labor_dispute")
        self.assertEqual(snapshot["status"], "failed")
        self.assertEqual(snapshot["error_code"], "BUDGET_EXCEEDED")
        db = SessionLocal()
        try:
            self.assertEqual(db.query(ToolCall).filter(ToolCall.run_id == state.run_id).count(), 0)
        finally:
            db.close()

    def test_draft_generation_is_idempotent(self):
        self._prepare_complete_matter()
        first = self.facade.create_labor_dispute_draft(self.matter_id, self.client_id, True)
        second = self.facade.create_labor_dispute_draft(self.matter_id, self.client_id, True)
        self.assertEqual(first["artifact_id"], second["artifact_id"])
        self.assertFalse(first["deduplicated"])
        self.assertTrue(second["deduplicated"])
        db = SessionLocal()
        try:
            count = db.query(AgentArtifact).filter(
                AgentArtifact.matter_id == self.matter_id,
                AgentArtifact.artifact_type == "labor_arbitration_application",
            ).count()
            self.assertEqual(count, 1)
        finally:
            db.close()

    def test_verifier_rejects_untraceable_analysis(self):
        state = AgentState(
            run_id="run_test", matter_id="matter_test", client_id=self.client_id,
            goal="测试", task_type="cn_labor_dispute",
        )
        result = ToolResult(
            tool_call_id="tool_test", success=True,
            data={"status": "awaiting_draft_approval", "deadline": {}},
        )
        report = LaborResultVerifier().verify("analyze_labor_dispute", result, state)
        self.assertFalse(report.valid)
        self.assertTrue(report.fact_errors)
        self.assertTrue(report.authority_errors)


if __name__ == "__main__":
    unittest.main()
