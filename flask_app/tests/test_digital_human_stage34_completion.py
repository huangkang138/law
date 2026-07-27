"""阶段 3.4B-E 的确定性、可信来源、计划和受控模型边界。"""
import unittest
import uuid
from datetime import datetime, timezone

from legal_agent_system.facade import LegalAgentFacade
from legal_agent_system.labor_disputes.llm_extractor import ControlledLaborFactExtractor
from legal_agent_system.labor_disputes.rules import LaborRuleEngine, RULE_VERSION
from legal_agent_system.capabilities.plans import TemplatePlanBuilder
from legal_agent_system.jurisdictions.authority_provider import OfficialCnLaborProvider, RetrievedSource
from core.database import SessionLocal
from models.db_models import Matter


class Stage34SourceClient:
    def get(self, url, _trusted_domains):
        spec = next(item for item in OfficialCnLaborProvider.sources if item.canonical_url == url)
        if spec.external_id.startswith("npc-"):
            text = "中华人民共和国劳动争议调解仲裁法 第二十六条前条内容。第二十七条劳动争议申请仲裁的时效期间为一年，欠薪适用特别规则。第二十八条后条内容。"
        elif spec.external_id.startswith("mohrss-"):
            text = "劳动人事争议仲裁办案规则 第二十五条前条内容。第二十六条申请仲裁的时效期间为一年。第二十七条主张权利导致时效中断并重新计算。第二十八条因不可抗力不能申请时仲裁时效中止。第二十九条后条内容。"
        else:
            articles = "".join(
                f"第{number}条劳动关系、劳动报酬、试用期、解除和经济补偿规则测试正文。"
                for number in spec.article_numbers
            )
            text = f"{spec.title}{articles}第一百条测试结束条款。"
        # retrieved_at 表示本次同步时间，不能固定为历史日期，否则七天新鲜度
        # 门禁会让该长期回归测试随日历自然失效。
        return RetrievedSource(text.encode(), "text/html", url, datetime.now(timezone.utc), '"stage34"', None)


class Stage34AuthorityProvider(OfficialCnLaborProvider):
    # 每次测试进程使用独立 Provider，避免本地历史法源版本污染幂等性断言。
    name = f"official_cn_labor_stage37c_fixture_{uuid.uuid4().hex}"

    def __init__(self):
        super().__init__(Stage34SourceClient())


class DigitalHumanStage34CompletionTest(unittest.TestCase):
    def test_production_facade_syncs_official_sources_and_reaches_approval(self):
        client_id = "dhc_stage34_production_sync"
        facade = LegalAgentFacade(auto_sync_authorities=True, authority_provider=Stage34AuthorityProvider())
        matter_id = facade.create_matter(client_id, "官方法源自动同步测试")["matter_id"]
        try:
            facade.confirm_jurisdiction(matter_id, client_id, {
                "country_code": "CN", "effective_at": "2026-07-13T00:00:00+00:00",
                "confirmed_by_user": True,
            })
            result = facade.start_labor_dispute_run(matter_id, client_id, {
                "employee_name": "测试申请人", "employer_name": "测试公司",
                "employment_start_date": "2022-03-01", "limitation_start_date": "2026-01-10",
                "monthly_salary": 12000, "work_location": "北京市朝阳区",
                "claim_types": ["欠薪", "违法解除"], "demands": "请求支付欠薪及解除赔偿",
                "wage_arrears_amount": 24000,
                "wage_arrears_start_date": "2026-05-01",
                "wage_arrears_end_date": "2026-06-30",
                "termination_date": "2026-07-01",
                "termination_reason": "用人单位通知解除",
                "termination_initiator": "employer",
            })
            self.assertEqual(result["status"], "awaiting_approval")
            analysis = result["final_output"]["analyze_labor_dispute"]
            self.assertGreaterEqual(len(analysis["authorities"]), 1)
            self.assertTrue(all(item["trust_level"] == "trusted" for item in analysis["authorities"]))
        finally:
            db = SessionLocal()
            try:
                matter = db.get(Matter, matter_id)
                if matter:
                    db.delete(matter)
                db.commit()
            finally:
                db.close()

    def test_official_provider_is_idempotent_and_searchable(self):
        facade = LegalAgentFacade(authority_provider=Stage34AuthorityProvider())
        first = facade.import_official_labor_authorities()
        second = facade.import_official_labor_authorities()
        self.assertEqual([x["authority_id"] for x in first], [x["authority_id"] for x in second])
        rows = facade.authorities.search("CN", datetime.now(timezone.utc), ["仲裁时效", "一年"])
        self.assertTrue(rows)
        self.assertTrue(all(x["trust_level"] == "trusted" for x in rows))
        catalog = LegalAgentFacade(auto_sync_authorities=True, authority_provider=Stage34AuthorityProvider()).get_labor_authority_catalog()
        self.assertEqual(catalog["status"], "ready")
        self.assertGreaterEqual(catalog["count"], 2)

    def test_limitation_rule_exposes_assumptions_and_refs(self):
        result = LaborRuleEngine().limitation({"limitation_start_date": "2026-01-01", "limitation_interruption_dates": ["2026-03-01"], "limitation_suspension_days": 10, "claim_types": ["欠薪"]}, [{"authority_id": "a1"}], ["f1"])
        self.assertEqual(result["rule_version"], RULE_VERSION)
        self.assertEqual(result["estimated_deadline"], "2027-03-11")
        self.assertEqual(result["fact_refs"], ["f1"])
        self.assertTrue(result["manual_review_required"])

    def test_limitation_rule_uses_calendar_year_and_marks_active_wage_claim(self):
        engine = LaborRuleEngine()
        leap = engine.limitation({"limitation_start_date": "2024-02-29", "claim_types": ["违法解除"]}, [{"authority_id": "a1"}], ["f1"])
        self.assertEqual(leap["estimated_deadline"], "2025-02-28")
        active = engine.limitation({"limitation_start_date": "2026-01-01", "claim_types": ["欠薪"], "employment_active": True}, [{"authority_id": "a1"}], ["f1"])
        self.assertIsNone(active["estimated_deadline"])
        self.assertEqual(active["deadline_type"], "employment_active_wage_claim")
        self.assertTrue(active["manual_review_required"])

    def test_plan_changes_with_claim_and_has_fingerprint(self):
        facade = LegalAgentFacade()
        template = facade.capabilities.get_template("labor_arbitration_application")
        workflow = {
            "facts": {"claim_types": ["违法解除"]},
            "dispute_tags": ["termination"],
        }
        revision = TemplatePlanBuilder().build(
            template, workflow, requested_task_type="labor_arbitration_application",
        )
        revision = facade.capabilities.get_adapter("cn_labor").customize_plan(revision, workflow)
        self.assertIn("解除", revision.steps[0].name)
        self.assertEqual(len(revision.input_fingerprint), 64)

    def test_llm_candidate_must_match_authorized_quote_and_budget(self):
        text = "申请人张三于2025年入职。"
        valid = ControlledLaborFactExtractor(lambda _text, _budget: {"token_usage": 10, "candidates": [{"field": "employee_name", "value": "张三", "quote": "张三", "start_offset": 3, "end_offset": 5, "confidence": 0.9}]}).extract(text)
        self.assertEqual(valid["candidates"][0]["value"], "张三")
        invalid = ControlledLaborFactExtractor(lambda _text, _budget: {"token_usage": 10, "candidates": [{"field": "employee_name", "value": "李四", "quote": "李四", "start_offset": 3, "end_offset": 5, "confidence": 0.9}]}).extract(text)
        self.assertFalse(invalid["candidates"])
        exceeded = ControlledLaborFactExtractor(lambda _text, _budget: {"token_usage": 11, "candidates": []}, token_budget=10).extract(text)
        self.assertEqual(exceeded["error_code"], "BUDGET_EXCEEDED")


if __name__ == "__main__":
    unittest.main()
