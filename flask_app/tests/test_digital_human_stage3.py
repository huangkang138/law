"""阶段 3 中国劳动纠纷闭环端到端集成测试。"""

import unittest
import uuid
from unittest.mock import patch

from core.database import Base, SessionLocal, engine
from legal_agent_system.facade import LegalAgentFacade
from models.db_models import AgentArtifact, LegalAuthority, Matter


class DigitalHumanStage3IntegrationTest(unittest.TestCase):
    """覆盖动态追问、来源拦截、期限验证、审批和草稿交付。"""

    @classmethod
    def setUpClass(cls):
        Base.metadata.create_all(bind=engine)

    def setUp(self):
        self.client_id = f"dhc_stage3_{uuid.uuid4().hex}"
        self.facade = LegalAgentFacade()
        self.matter_id = self.facade.create_matter(self.client_id, "处理解除劳动合同仲裁") ["matter_id"]
        self.facade.confirm_jurisdiction(self.matter_id, self.client_id, {
            "country_code": "CN", "effective_at": "2026-07-12T00:00:00+00:00",
            "confirmed_by_user": True,
        })
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

    def test_full_labor_dispute_workflow(self):
        partial = self.facade.update_labor_dispute_facts(self.matter_id, self.client_id, {
            "employee_name": "测试申请人", "employer_name": "测试公司",
        })
        self.assertEqual(partial["status"], "awaiting_information")
        self.assertIn("monthly_salary", partial["missing_facts"])
        self.assertTrue(partial["questions"])

        ready = self.facade.update_labor_dispute_facts(self.matter_id, self.client_id, {
            "employment_start_date": "2022-01-01", "limitation_start_date": "2026-01-10",
            "monthly_salary": 12000, "work_location": "北京市",
            "claim_types": ["违法解除"], "demands": "请求支付解除劳动合同赔偿金",
            "termination_date": "2026-01-15", "termination_reason": "组织架构调整",
            "termination_initiator": "employer",
        })
        self.assertEqual(ready["status"], "ready")
        self.assertEqual(ready["missing_facts"], [])

        # 显式模拟来源服务不可用，不依赖共享数据库是否已安装生产法源。
        with patch.object(self.facade.labor_disputes, "_verified_authorities", return_value=[]):
            blocked = self.facade.analyze_labor_dispute(self.matter_id, self.client_id)
        self.assertEqual(blocked["status"], "blocked_authority")

        authority = self.facade.register_test_authority({
            "country_code": "CN", "authority_type": "statute",
            "title": "劳动争议仲裁时效测试来源", "provision": "测试条款",
            "text": "劳动争议仲裁时效期间为一年。解除规则仅用于自动化测试。",
            "source_url": "https://example.invalid/stage3-authority",
            "issuing_body": "自动化测试机构", "status": "effective",
            "effective_from": "2020-01-01T00:00:00+00:00",
        })
        self.authority_ids.append(authority["authority_id"])

        analysis = self.facade.analyze_labor_dispute(self.matter_id, self.client_id)
        self.assertEqual(analysis["status"], "awaiting_draft_approval")
        self.assertEqual(analysis["deadline"]["estimated_deadline"], "2027-01-10")
        with self.assertRaises(Exception):
            self.facade.create_labor_dispute_draft(self.matter_id, self.client_id, False)

        draft = self.facade.create_labor_dispute_draft(self.matter_id, self.client_id, True)
        self.assertEqual(draft["status"], "draft")
        self.assertIn("劳动仲裁申请书（草稿）", draft["content"])
        self.assertIn(authority["authority_id"], draft["authority_refs"])
        db = SessionLocal()
        try:
            self.assertIsNotNone(db.get(AgentArtifact, draft["artifact_id"]))
        finally:
            db.close()


if __name__ == "__main__":
    unittest.main()
