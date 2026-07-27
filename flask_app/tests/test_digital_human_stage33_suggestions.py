"""阶段 3.3 材料候选事实与用户确认测试。"""

import unittest
import uuid

from core.database import Base, SessionLocal, engine
from legal_agent_system.facade import LegalAgentFacade
from legal_agent_system.runtime.errors import AgentRuntimeError
from models.db_models import LaborDisputeProfile, Matter


class DigitalHumanStage33SuggestionsIntegrationTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        Base.metadata.create_all(bind=engine)

    def setUp(self):
        self.client_id = f"dhc_stage33_{uuid.uuid4().hex}"
        self.facade = LegalAgentFacade()
        self.matter_id = self.facade.create_matter(self.client_id, "材料自动填写测试")["matter_id"]

    def tearDown(self):
        db = SessionLocal()
        try:
            matter = db.get(Matter, self.matter_id)
            if matter:
                db.delete(matter)
            db.commit()
        finally:
            db.close()

    def test_material_suggestions_keep_provenance_and_require_adoption(self):
        text = (
            "事实：林晓雨于2022年03月01日入职北京星河数字科技有限公司，"
            "实际工作地点为北京市朝阳区。\n"
            "事实：最近十二个月平均月工资为12000元。\n"
            "事实：2026年01月10日，公司向林晓雨发送《解除劳动合同通知书》，通知载明劳动关系于2026年01月15日解除，理由为“组织架构调整”。\n"
            "事实：林晓雨于2026年01月10日收到通知，并在当日知道公司拟解除劳动关系。\n"
            "事实：林晓雨拟通过劳动仲裁主张拖欠工资及违法解除赔偿金。"
        )
        document = self.facade.add_material(self.matter_id, self.client_id, "测试材料.txt", text, "text/plain")
        self.facade.extract_material_facts(self.matter_id, self.client_id, document["document_id"])
        result = self.facade.suggest_labor_dispute_facts(self.matter_id, self.client_id)
        suggested = result["suggested_facts"]
        self.assertEqual(suggested["employee_name"], "林晓雨")
        self.assertEqual(suggested["employer_name"], "北京星河数字科技有限公司")
        self.assertEqual(suggested["employment_start_date"], "2022-03-01")
        self.assertEqual(suggested["termination_date"], "2026-01-15")
        self.assertEqual(suggested["limitation_start_date"], "2026-01-10")
        self.assertEqual(suggested["termination_reason"], "组织架构调整")
        self.assertEqual(suggested["monthly_salary"], 12000.0)
        self.assertEqual(suggested["work_location"], "北京市朝阳区")
        self.assertIn("违法解除", suggested["claim_types"])
        self.assertTrue(all(item["sources"][0]["quote"] for item in result["fields"]))

        # 读取建议不会把候选值自动写成用户确认事实。
        db = SessionLocal()
        try:
            self.assertIsNone(db.get(LaborDisputeProfile, self.matter_id))
        finally:
            db.close()
        adopted = self.facade.update_labor_dispute_facts(self.matter_id, self.client_id, suggested)
        self.assertEqual(adopted["facts"]["employee_name"], "林晓雨")

        with self.assertRaises(AgentRuntimeError) as denied:
            self.facade.suggest_labor_dispute_facts(self.matter_id, f"dhc_other_{uuid.uuid4().hex}")
        self.assertEqual(denied.exception.code, "FORBIDDEN")


if __name__ == "__main__":
    unittest.main()
