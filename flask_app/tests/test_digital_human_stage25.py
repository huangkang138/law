"""阶段 2.5 案件收口与真实劳动补偿工具集成测试。"""

import unittest
import uuid

from core.database import Base, SessionLocal, engine
from legal_agent_system.facade import LegalAgentFacade
from models.db_models import LaborCompensation, Matter
from services.labor_compensation_service import get_labor_compensation_service


class DigitalHumanStage25IntegrationTest(unittest.TestCase):
    """验证案件恢复/删除、材料去重及 Agent 与原工具使用同一公式。"""

    @classmethod
    def setUpClass(cls):
        Base.metadata.create_all(bind=engine)

    def setUp(self):
        self.client_id = f"dhc_stage25_{uuid.uuid4().hex}"
        self.facade = LegalAgentFacade()
        self.matter_id = self.facade.create_matter(self.client_id, "劳动补偿工具接入测试")["matter_id"]
        self.facade.confirm_jurisdiction(self.matter_id, self.client_id, {
            "country_code": "CN", "effective_at": "2026-07-12T00:00:00+00:00",
            "confirmed_by_user": True,
        })
        self.record_ids = []

    def tearDown(self):
        db = SessionLocal()
        try:
            if self.record_ids:
                db.query(LaborCompensation).filter(LaborCompensation.id.in_(self.record_ids)).delete(synchronize_session=False)
            matter = db.get(Matter, self.matter_id)
            if matter:
                db.delete(matter)
            db.commit()
        finally:
            db.close()

    def test_matter_recovery_deduplication_and_real_tool(self):
        matters = self.facade.list_matters(self.client_id)
        self.assertEqual([item["matter_id"] for item in matters], [self.matter_id])
        restored = self.facade.get_matter(self.matter_id, self.client_id)
        self.assertTrue(restored["jurisdiction"]["confirmed_by_user"])
        self.assertEqual(restored["jurisdiction"]["country_code"], "CN")

        first = self.facade.add_material(self.matter_id, self.client_id, "工资说明.txt", "事实：月工资为12000元。", "text/plain")
        repeated = self.facade.add_material(self.matter_id, self.client_id, "重复文件.txt", "事实：月工资为12000元。", "text/plain")
        self.assertEqual(first["document_id"], repeated["document_id"])
        self.assertTrue(repeated["deduplicated"])
        first_facts = self.facade.extract_material_facts(self.matter_id, self.client_id, first["document_id"])
        repeated_facts = self.facade.extract_material_facts(self.matter_id, self.client_id, first["document_id"])
        self.assertEqual([item["fact_id"] for item in first_facts], [item["fact_id"] for item in repeated_facts])

        agent_result = self.facade.calculate_labor_compensation(self.matter_id, self.client_id, {
            "monthly_salary": 12000, "years": 3, "months": 6,
        })["data"]
        direct_result = get_labor_compensation_service().calculate(12000, 3, 6)
        self.record_ids.extend([agent_result["record_id"], direct_result["record_id"]])
        self.assertEqual(agent_result["compensation"], direct_result["compensation"])
        self.assertEqual(agent_result["formula"], direct_result["formula"])

        self.facade.delete_matter(self.matter_id, self.client_id)
        self.assertEqual(self.facade.list_matters(self.client_id), [])


if __name__ == "__main__":
    unittest.main()
