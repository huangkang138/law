"""阶段 3.7A 劳动案件分流与劳动关系初筛测试。"""

import unittest
import uuid

from core.database import Base, SessionLocal, engine
from legal_agent_system.facade import LegalAgentFacade
from legal_agent_system.labor_disputes import LaborTriageDecisionEngine, LaborTriageFacts
from legal_agent_system.runtime.errors import AgentRuntimeError
from models.db_models import DigitalHumanSession, LegalAuthority, Matter


class Stage37ALaborTriageTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        Base.metadata.create_all(bind=engine)

    def setUp(self):
        self.client_id = f"dhc_stage37a_{uuid.uuid4().hex}"
        self.other_client_id = f"dhc_stage37a_other_{uuid.uuid4().hex}"
        self.facade = LegalAgentFacade()
        self.matter_ids = []
        self.session_ids = []
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
            for session_id in self.session_ids:
                session = db.get(DigitalHumanSession, session_id)
                if session:
                    db.delete(session)
            db.commit()
        finally:
            db.close()

    def _matter(self, goal="青年就业劳动关系判断"):
        matter_id = self.facade.create_matter(self.client_id, goal)["matter_id"]
        self.matter_ids.append(matter_id)
        self.facade.confirm_jurisdiction(matter_id, self.client_id, {
            "country_code": "CN",
            "effective_at": "2026-07-21T00:00:00+00:00",
            "confirmed_by_user": True,
        })
        return matter_id

    def _relationship_authority(self):
        authority = self.facade.register_test_authority({
            "country_code": "CN",
            "authority_type": "regulation",
            "title": "劳动关系测试来源",
            "provision": "第一条",
            "text": "劳动关系应核对主体资格、劳动管理、有报酬劳动及单位业务组成部分。",
            "source_url": f"https://{uuid.uuid4().hex}.invalid/stage37c-relationship",
            "issuing_body": "自动化测试机构",
            "status": "effective",
            "effective_from": "2020-01-01T00:00:00+00:00",
        })
        self.authority_ids.append(authority["authority_id"])

    @staticmethod
    def _facts(**extra):
        return {
            "issue_domain": "labor",
            "scenario_type": "part_time",
            "student_status": "not_student",
            "school_arranged": False,
            "employment_intent": True,
            "employer_qualified": True,
            "paid_labor": True,
            "management_control": True,
            "business_integrated": True,
            "regular_schedule": True,
            "agreement_type": "none",
            "claim_types": ["欠薪"],
            **extra,
        }

    def test_school_arranged_internship_does_not_enter_arbitration_directly(self):
        result = LaborTriageDecisionEngine().assess(LaborTriageFacts.model_validate(self._facts(
            scenario_type="school_arranged_internship",
            student_status="current_student",
            school_arranged=True,
            employment_intent=False,
            agreement_type="internship_agreement",
        )))
        self.assertEqual(result["triage_type"], "labor_relationship_assessment")
        self.assertEqual(result["relationship_status"], "likely_not_established")
        self.assertTrue(result["manual_review_required"])
        self.assertFalse(result["legal_conclusion"])

    def test_student_part_time_can_be_likely_labor_relationship(self):
        result = LaborTriageDecisionEngine().assess(LaborTriageFacts.model_validate(self._facts(
            student_status="current_student",
            scenario_type="part_time",
            claim_types=["欠薪", "违法解除"],
        )))
        self.assertEqual(result["triage_type"], "formal_labor_dispute")
        self.assertEqual(result["relationship_status"], "likely_established")
        self.assertEqual(result["recommended_task_type"], "labor_case_analysis")
        self.assertTrue(result["manual_review_required"])

    def test_missing_and_high_risk_cases_fail_safe(self):
        missing = LaborTriageDecisionEngine().assess(LaborTriageFacts())
        self.assertEqual(missing["relationship_status"], "uncertain")
        self.assertIn("scenario_type", missing["missing_facts"])
        ordinary = LaborTriageDecisionEngine().assess(LaborTriageFacts.model_validate({
            "issue_domain": "labor",
            "scenario_type": "regular_employment",
            "student_status": "not_student",
        }))
        self.assertNotIn("school_arranged", ordinary["missing_facts"])
        high_risk = LaborTriageDecisionEngine().assess(LaborTriageFacts.model_validate({
            "urgent_risks": ["personal_safety"],
        }))
        self.assertEqual(high_risk["triage_type"], "high_risk_handoff")
        self.assertEqual(high_risk["risk_level"], "high")

    def test_triage_persists_and_runtime_uses_relationship_template(self):
        self._relationship_authority()
        matter_id = self._matter()
        saved = self.facade.update_labor_case_triage(matter_id, self.client_id, self._facts())
        self.assertEqual(saved["version"], 1)
        restored = self.facade.get_labor_case_triage(matter_id, self.client_id)
        self.assertEqual(restored["result"]["relationship_status"], "likely_established")
        with self.assertRaises(AgentRuntimeError):
            self.facade.get_labor_case_triage(matter_id, self.other_client_id)

        run = self.facade.start_task(
            matter_id, self.client_id, "labor_relationship_assessment",
        )
        self.assertEqual(run["status"], "completed")
        self.assertEqual(run["template_id"], "labor_relationship_assessment")
        self.assertEqual(len(run["steps"]), 1)
        output = run["final_output"]["assess_labor_relationship"]
        self.assertEqual(output["triage_type"], "formal_labor_dispute")
        self.assertFalse(output["legal_conclusion"])
        self.assertTrue(output["fact_refs"])
        self.assertTrue(output["authority_refs"])

    def test_non_labor_case_is_handed_off_before_tool_execution(self):
        matter_id = self._matter("邻里纠纷不进入劳动流程")
        run = self.facade.start_task(matter_id, self.client_id, "labor_relationship_assessment", {
            "issue_domain": "non_labor",
        })
        self.assertEqual(run["status"], "human_handoff")
        self.assertEqual(run["error_code"], "NON_LABOR_DISPUTE")
        self.assertEqual(run["steps"], [])

    def test_chat_session_is_persistently_linked_to_triage_matter(self):
        session_id = f"dhs_stage37a_{uuid.uuid4().hex}"
        self.session_ids.append(session_id)
        db = SessionLocal()
        try:
            db.add(DigitalHumanSession(
                id=session_id, user_id=self.client_id,
                title="劳动分流编排", is_active=True,
            ))
            db.commit()
        finally:
            db.close()

        created = self.facade.create_matter(
            self.client_id, "聊天创建的劳动案件", session_id,
        )
        self.matter_ids.append(created["matter_id"])
        self.assertEqual(created["session_id"], session_id)
        restored = self.facade.get_matter(created["matter_id"], self.client_id)
        self.assertEqual(restored["session_id"], session_id)

        with self.assertRaises(AgentRuntimeError) as caught:
            self.facade.create_matter(
                self.other_client_id, "禁止关联他人会话", session_id,
            )
        self.assertEqual(caught.exception.code, "FORBIDDEN")


if __name__ == "__main__":
    unittest.main()
