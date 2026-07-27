"""数字人阶段 2 材料、法域和法律来源 PostgreSQL 集成测试。"""

import unittest
import uuid
from datetime import datetime, timezone

from core.database import Base, SessionLocal, engine
from legal_agent_system.facade import LegalAgentFacade
from legal_agent_system.runtime.errors import AgentRuntimeError
from models.db_models import LegalAuthority, Matter


class DigitalHumanStage2IntegrationTest(unittest.TestCase):
    """验证事实和法律引用均能追溯，且未知来源会明确降级。"""

    @classmethod
    def setUpClass(cls):
        Base.metadata.create_all(bind=engine)

    def setUp(self):
        token = uuid.uuid4().hex
        self.client_id = f"dhc_stage2_{token}"
        self.other_client_id = f"dhc_stage2_other_{token}"
        self.facade = LegalAgentFacade()
        matter = self.facade.create_matter(self.client_id, "阶段 2 材料追溯测试")
        self.matter_id = matter["matter_id"]
        self.authority_id = None

    def tearDown(self):
        db = SessionLocal()
        try:
            if self.authority_id:
                authority = db.get(LegalAuthority, self.authority_id)
                if authority:
                    db.delete(authority)
            matter = db.get(Matter, self.matter_id)
            if matter:
                db.delete(matter)
            db.commit()
        finally:
            db.close()

    def test_material_traceability_access_control_and_authority_degrade(self):
        jurisdiction = self.facade.confirm_jurisdiction(self.matter_id, self.client_id, {
            "country_code": "CN", "effective_at": "2026-07-12T00:00:00+00:00",
            "confirmed_by_user": True, "subdivision_code": "CN-BJ",
        })
        self.assertTrue(jurisdiction["confirmed_by_user"])

        material = self.facade.add_material(
            self.matter_id, self.client_id, "解除通知.txt",
            "事实：2026年6月1日收到解除通知。拖欠工资金额为5000元。",
            "text/plain",
        )
        facts = self.facade.extract_material_facts(self.matter_id, self.client_id, material["document_id"])
        self.assertGreaterEqual(len(facts), 2)
        for fact in facts:
            self.assertEqual(fact["material_ref"]["document_id"], material["document_id"])
            self.assertTrue(fact["material_ref"]["quote"])
            self.assertLess(fact["material_ref"]["start_offset"], fact["material_ref"]["end_offset"])

        timeline = self.facade.build_matter_timeline(self.matter_id, self.client_id)
        self.assertEqual(timeline[0]["date"], "2026-06-01")
        checklist = self.facade.get_evidence_checklist(self.matter_id, self.client_id)
        self.assertEqual(checklist["located_fact_count"], len(facts))

        with self.assertRaises(AgentRuntimeError) as denied:
            self.facade.build_matter_timeline(self.matter_id, self.other_client_id)
        self.assertEqual(denied.exception.code, "FORBIDDEN")

        authority = self.facade.register_test_authority({
            "country_code": "CN",
            "authority_type": "statute",
            "title": "阶段 2 测试来源",
            "text": "仅供自动化测试的来源正文，不代表真实法律内容。",
            "source_url": "https://example.invalid/stage2-test",
            "issuing_body": "测试机构",
            "status": "unknown",
        })
        self.authority_id = authority["authority_id"]
        verified = self.facade.verify_authority(self.authority_id, datetime.now(timezone.utc), "CN")
        self.assertFalse(verified["valid"])
        self.assertTrue(any("不能作为确定依据" in warning for warning in verified["warnings"]))

        jurisdictions = self.facade.list_jurisdictions()
        self.assertEqual(jurisdictions[0]["country_code"], "CN")
        with self.assertRaises(AgentRuntimeError):
            self.facade.register_test_authority({"country_code": "ZZ", "source_url": "https://example.invalid/unsupported"})


if __name__ == "__main__":
    unittest.main()
