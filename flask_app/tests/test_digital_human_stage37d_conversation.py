"""阶段3.7D会话基础设施专项测试。"""

import json
import threading
import unittest
import uuid
from unittest.mock import patch

from sqlalchemy import text

from core.database import SessionLocal, engine
from models.db_models import (
    AgentRun,
    DigitalHumanMessage,
    DigitalHumanRequest,
    DigitalHumanSession,
    Matter,
)
from services.digital_human_service import DigitalHumanService
from services.conversation.context_builder import ConversationContextBuilder
from services.conversation.locks import ConversationSessionLock
from services.conversation.memory import ConversationMemoryManager
from services.conversation.repository import RequestInProgress
from services.conversation.router import ConversationRouter
from services.conversation.schemas import ContextEnvelope, MemorySnapshot
from services.conversation.token_budget import TokenBudget


class _ContextRepository:
    def messages(self, *_args, **_kwargs):
        return [
            {"id": "m1", "role": "user", "content": "旧消息", "estimated_tokens": 2},
        ]

    def matter_context(self, *_args, **_kwargs):
        return {
            "matter_id": "matter_1",
            "confirmed_facts": {"monthly_salary": 8000.0},
            "run_id": "run_1",
            "run_status": "awaiting_information",
            "run_error_code": None,
        }


class ConversationFoundationTest(unittest.TestCase):
    def test_recent_window_uses_token_budget(self):
        budget = TokenBudget(recent_budget=5)
        recent, older = budget.split_recent([
            {"id": "1", "content": "甲乙丙", "estimated_tokens": 3},
            {"id": "2", "content": "丁戊", "estimated_tokens": 2},
            {"id": "3", "content": "己庚辛", "estimated_tokens": 3},
        ])
        self.assertEqual([item["id"] for item in recent], ["2", "3"])
        self.assertEqual([item["id"] for item in older], ["1"])

    def test_salary_correction_supersedes_summary_item_and_rebuilds_text(self):
        manager = ConversationMemoryManager(TokenBudget(recent_budget=20))
        first = manager.update(
            MemorySnapshot(session_id="dh_1"),
            "我的工资是6500，公司拖欠三个月",
            "msg_1",
            [{"id": "msg_1", "role": "user", "content": "我的工资是6500，公司拖欠三个月"}],
        )
        second = manager.update(
            first,
            "不是6500，是7200。",
            "msg_2",
            [
                {"id": "msg_1", "role": "user", "content": "我的工资是6500，公司拖欠三个月"},
                {"id": "msg_2", "role": "user", "content": "不是6500，是7200。"},
            ],
        )
        salary_items = [
            item for item in second.summary_items
            if item["subject"] == "monthly_salary"
        ]
        self.assertEqual([item["status"] for item in salary_items], ["superseded", "active"])
        self.assertEqual(salary_items[-1]["value"], 7200.0)
        self.assertEqual(salary_items[-1]["supersedes_item_id"], salary_items[0]["item_id"])
        self.assertIn("7200", second.summary_text)
        self.assertNotIn("6500", second.summary_text)

    def test_context_excludes_summary_fact_conflicting_with_matter(self):
        builder = ConversationContextBuilder(_ContextRepository(), TokenBudget())
        memory = MemorySnapshot(
            session_id="dh_1",
            structured={
                "user_claims": [{
                    "subject": "monthly_salary",
                    "value": 7200.0,
                    "summary_item_id": "summary_1",
                }],
            },
            summary_text="用户陈述月工资：7200",
            summary_items=[{
                "item_id": "summary_1",
                "item_type": "fact",
                "subject": "monthly_salary",
                "value": 7200.0,
                "source_message_ids": ["msg_1"],
                "status": "active",
            }],
        )
        envelope = builder.build(
            "dh_1", "dhc_1", "现在怎么办", "安全规则", memory, "dhr_1",
        )
        system_text = "\n".join(
            item["content"] for item in envelope.messages if item["role"] == "system"
        )
        self.assertIn('"monthly_salary": 8000.0', system_text)
        self.assertNotIn("monthly_salary：7200.0", system_text)
        untrusted_memory = [
            item for item in envelope.messages
            if "会话结构化记忆" in item["content"]
        ]
        self.assertTrue(untrusted_memory)
        self.assertTrue(all(item["role"] == "user" for item in untrusted_memory))
        decision = ConversationRouter().route("不是6500，是7200", envelope)
        self.assertEqual(decision.route, "workspace_guidance")
        self.assertEqual(decision.reason_code, "confirmed_fact_conflict")

    def test_router_keeps_consultation_and_case_creation_separate(self):
        router = ConversationRouter()
        context = ContextEnvelope(messages=[], estimated_tokens=0)
        consultation = router.route("试用期一般最长多久？", context)
        case = router.route("公司欠薪，我要申请劳动仲裁", context)
        risk = router.route("老板威胁我不许维权", context)
        self.assertEqual(consultation.route, "labor_consultation")
        self.assertEqual(case.route, "labor_triage")
        self.assertTrue(case.side_effect_authorized)
        self.assertEqual(risk.route, "high_risk_handoff")

        informational = router.route("申请劳动仲裁需要哪些条件？", context)
        self.assertEqual(informational.route, "labor_consultation")
        self.assertFalse(informational.side_effect_authorized)

        fuzzy = router.route(
            "老板一直不肯发钱，我不知道该怎么办",
            context,
            {
                "conversation_route": "labor_consultation",
                "confidence": 0.88,
            },
        )
        self.assertEqual(fuzzy.route, "labor_consultation")
        self.assertEqual(fuzzy.reason_code, "structured_llm_fallback")

    def test_llm_fallback_route_is_schema_bounded(self):
        accepted = DigitalHumanService._parse_llm_response(json.dumps({
            "reply": "测试",
            "intent": "general_chat",
            "conversation_route": "labor_consultation",
            "emotion": "talk_normal",
            "confidence": 0.8,
        }))
        rejected = DigitalHumanService._parse_llm_response(json.dumps({
            "reply": "测试",
            "intent": "general_chat",
            "conversation_route": "free_form_tool_call",
            "emotion": "talk_normal",
            "confidence": 0.9,
        }))
        self.assertEqual(accepted["conversation_route"], "labor_consultation")
        self.assertIsNone(rejected["conversation_route"])

    def test_assistant_content_is_never_extracted_as_user_claim(self):
        manager = ConversationMemoryManager()
        snapshot = manager.update(
            MemorySnapshot(session_id="dh_1"),
            "我想咨询劳动问题",
            "user_1",
            [
                {"id": "assistant_1", "role": "assistant", "content": "你的工资可能是9000"},
                {"id": "user_1", "role": "user", "content": "我想咨询劳动问题"},
            ],
        )
        self.assertEqual(snapshot.structured["user_claims"], [])
        self.assertFalse(any(
            "assistant_1" in item.get("source_message_ids", [])
            for item in snapshot.summary_items
        ))

    def test_fifty_turns_keep_goal_and_bound_recent_window(self):
        budget = TokenBudget(recent_budget=30)
        manager = ConversationMemoryManager(budget)
        snapshot = MemorySnapshot(session_id="dh_long")
        history = []
        for index in range(50):
            content = f"第{index + 1}轮，我继续咨询工资问题。"
            message_id = f"msg_{index + 1}"
            history.append({
                "id": message_id,
                "role": "user",
                "content": content,
                "estimated_tokens": budget.estimate(content),
            })
            snapshot = manager.update(
                snapshot, content, message_id, history,
            )
        recent, older = budget.split_recent(history)
        self.assertTrue(older)
        self.assertLessEqual(
            sum(item["estimated_tokens"] for item in recent),
            budget.recent_budget,
        )
        self.assertEqual(
            snapshot.structured["user_goals"][0]["source_message_id"],
            "msg_1",
        )
        self.assertEqual(snapshot.summary_through_message_id, older[-1]["id"])


class _Chunk:
    content = json.dumps({
        "reply": "这是测试回复",
        "intent": "general_chat",
        "emotion": "talk_normal",
        "confidence": 0.9,
    }, ensure_ascii=False)


class _FakeLlm:
    @staticmethod
    def stream(_messages):
        yield _Chunk()


class _ForcedTriageChunk:
    content = json.dumps({
        "reply": "我建议直接建立案件",
        "intent": "general_chat",
        "conversation_route": "labor_triage",
        "emotion": "talk_normal",
        "confidence": 1.0,
    }, ensure_ascii=False)


class _ForcedTriageLlm:
    @staticmethod
    def stream(_messages):
        yield _ForcedTriageChunk()


class _BlockingLlm:
    def __init__(self):
        self.entered = threading.Event()
        self.release = threading.Event()

    def stream(self, _messages):
        self.entered.set()
        if not self.release.wait(timeout=10):
            raise TimeoutError("测试未释放阻塞 LLM")
        yield _Chunk()


class ConversationOrchestratorIntegrationTest(unittest.TestCase):
    def setUp(self):
        token = uuid.uuid4().hex
        self.client_id = f"dhc_stage37d_{token}"
        self.session_id = f"dh_stage37d_{token}"
        self.request_ids = [
            f"dhr_stage37d_consult_{token}",
            f"dhr_stage37d_case_{token}",
        ]
        self.service = DigitalHumanService.__new__(DigitalHumanService)
        self.service.llm = _FakeLlm()
        self.service.system_prompt = "测试安全规则"

    def tearDown(self):
        db = SessionLocal()
        try:
            matter_ids = [
                item[0] for item in db.query(Matter.id).filter(
                    Matter.client_id == self.client_id,
                ).all()
            ]
            if matter_ids:
                db.query(Matter).filter(Matter.id.in_(matter_ids)).delete(
                    synchronize_session=False,
                )
            db.query(DigitalHumanRequest).filter(
                DigitalHumanRequest.client_id == self.client_id,
            ).delete(synchronize_session=False)
            db.query(DigitalHumanSession).filter(
                DigitalHumanSession.user_id == self.client_id,
            ).delete(synchronize_session=False)
            db.commit()
        finally:
            db.close()

    def test_single_entry_keeps_consultation_out_of_matter_and_case_idempotent(self):
        consultation = self.service.chat(
            "试用期一般最长多久？",
            self.client_id,
            self.request_ids[0],
            self.session_id,
        )
        db = SessionLocal()
        try:
            self.assertEqual(
                db.query(Matter).filter(Matter.client_id == self.client_id).count(),
                0,
            )
        finally:
            db.close()
        self.assertEqual(consultation["decision"]["route"], "labor_consultation")
        self.assertEqual(consultation["action"]["type"], "reply_only")

        first = self.service.chat(
            "公司拖欠工资，我要申请劳动仲裁",
            self.client_id,
            self.request_ids[1],
            self.session_id,
        )
        repeated = self.service.chat(
            "公司拖欠工资，我要申请劳动仲裁",
            self.client_id,
            self.request_ids[1],
            self.session_id,
        )
        self.assertEqual(first, repeated)
        self.assertEqual(first["decision"]["route"], "labor_triage")
        self.assertEqual(first["action"]["type"], "ask_one_key_question")
        self.assertTrue(first["context"]["matter_id"].startswith("matter_"))
        db = SessionLocal()
        try:
            self.assertEqual(
                db.query(Matter).filter(Matter.client_id == self.client_id).count(),
                1,
            )
            request_record = db.get(
                DigitalHumanRequest,
                self.request_ids[1],
            )
            self.assertEqual(
                request_record.checkpoint_json["workspace_version"],
                0,
            )
        finally:
            db.close()

    def test_llm_cannot_authorize_labor_side_effect_without_server_intent(self):
        self.service.llm = _ForcedTriageLlm()
        result = self.service.chat(
            "你好，给我讲个笑话",
            self.client_id,
            f"dhr_stage37d_forced_{uuid.uuid4().hex}",
            self.session_id,
        )
        self.assertEqual(result["decision"]["route"], "normal_chat")
        self.assertEqual(result["action"]["type"], "reply_only")
        db = SessionLocal()
        try:
            self.assertEqual(
                db.query(Matter).filter(Matter.client_id == self.client_id).count(),
                0,
            )
            self.assertEqual(
                db.query(AgentRun).filter(AgentRun.client_id == self.client_id).count(),
                0,
            )
        finally:
            db.close()

    def test_blocked_llm_does_not_hold_advisory_lock_connection(self):
        blocking = _BlockingLlm()
        self.service.llm = blocking
        blocked_request = f"dhr_stage37d_blocked_{uuid.uuid4().hex}"
        errors = []

        def invoke_blocked():
            try:
                self.service.chat(
                    "普通问题",
                    self.client_id,
                    blocked_request,
                    self.session_id,
                )
            except Exception as exc:  # pragma: no cover - asserted below
                errors.append(exc)

        worker = threading.Thread(target=invoke_blocked)
        worker.start()
        self.assertTrue(blocking.entered.wait(timeout=5))
        lock_key = ConversationSessionLock._key(self.session_id)
        with engine.connect() as connection:
            acquired = bool(connection.execute(
                text("SELECT pg_try_advisory_lock(:key)"),
                {"key": lock_key},
            ).scalar())
            if acquired:
                connection.execute(
                    text("SELECT pg_advisory_unlock(:key)"),
                    {"key": lock_key},
                )
        self.assertTrue(acquired)

        with self.assertRaises(RequestInProgress):
            self.service.chat(
                "同一会话的并发问题",
                self.client_id,
                f"dhr_stage37d_same_session_{uuid.uuid4().hex}",
                self.session_id,
            )

        independent_service = DigitalHumanService.__new__(DigitalHumanService)
        independent_service.llm = _FakeLlm()
        independent_service.system_prompt = "测试安全规则"
        independent = independent_service.chat(
            "另一个会话的问题",
            self.client_id,
            f"dhr_stage37d_independent_{uuid.uuid4().hex}",
            f"dh_stage37d_independent_{uuid.uuid4().hex}",
        )
        self.assertEqual(independent["action"]["type"], "reply_only")

        blocking.release.set()
        worker.join(timeout=10)
        self.assertFalse(worker.is_alive())
        self.assertEqual(errors, [])

    def test_retry_recovers_committed_action_without_creating_second_run(self):
        orchestrator = self.service._build_orchestrator()
        self.service._orchestrator = orchestrator
        original_complete = orchestrator.repository.complete_request
        fail_once = {"pending": True}

        def fail_after_action(*args, **kwargs):
            if fail_once["pending"]:
                fail_once["pending"] = False
                raise RuntimeError("模拟 assistant/request 完成失败")
            return original_complete(*args, **kwargs)

        orchestrator.repository.complete_request = fail_after_action
        request_id = f"dhr_stage37d_recovery_{uuid.uuid4().hex}"
        full_facts = {
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
        }
        with patch(
            "services.conversation.actions.ConversationActions._infer_labor_facts",
            return_value=full_facts,
        ):
            with self.assertRaisesRegex(RuntimeError, "模拟 assistant"):
                self.service.chat(
                    "公司欠薪，我要申请劳动仲裁",
                    self.client_id,
                    request_id,
                    self.session_id,
                )

            db = SessionLocal()
            try:
                runs = db.query(AgentRun).filter(
                    AgentRun.client_id == self.client_id,
                ).all()
                self.assertEqual(len(runs), 1)
                runs[0].status = "completed"
                state = dict(runs[0].state_json or {})
                state["status"] = "completed"
                runs[0].state_json = state
                original_matter_id = runs[0].matter_id
                db.add(DigitalHumanMessage(
                    id=f"dhmsg_{uuid.uuid4().hex}",
                    session_id=self.session_id,
                    request_id=request_id,
                    role="assistant",
                    content="已生成但 request 尚未完成的回复",
                    intent="general_chat",
                    emotion="talk_normal",
                    confidence=0.9,
                    estimated_tokens=10,
                ))
                db.commit()
            finally:
                db.close()

            recovered = self.service.chat(
                "公司欠薪，我要申请劳动仲裁",
                self.client_id,
                request_id,
                self.session_id,
            )

        self.assertEqual(recovered["context"]["matter_id"], original_matter_id)
        db = SessionLocal()
        try:
            self.assertEqual(
                db.query(Matter).filter(Matter.client_id == self.client_id).count(),
                1,
            )
            self.assertEqual(
                db.query(AgentRun).filter(AgentRun.client_id == self.client_id).count(),
                1,
            )
            request = db.get(DigitalHumanRequest, request_id)
            self.assertEqual(request.status, "completed")
            self.assertEqual(
                db.query(DigitalHumanMessage).filter(
                    DigitalHumanMessage.request_id == request_id,
                    DigitalHumanMessage.role == "assistant",
                ).count(),
                1,
            )
        finally:
            db.close()

    def test_retry_resumes_reserved_run_without_creating_another(self):
        request_id = f"dhr_stage37d_running_{uuid.uuid4().hex}"
        full_facts = {
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
        }
        from legal_agent_system import get_legal_agent_facade

        graph = get_legal_agent_facade().capability_runtime.graph
        with patch(
            "services.conversation.actions.ConversationActions._infer_labor_facts",
            return_value=full_facts,
        ):
            with patch.object(
                graph,
                "invoke",
                side_effect=RuntimeError("模拟 Run 保留后执行中断"),
            ):
                with self.assertRaisesRegex(RuntimeError, "执行中断"):
                    self.service.chat(
                        "公司欠薪，我要申请劳动仲裁",
                        self.client_id,
                        request_id,
                        self.session_id,
                    )

            db = SessionLocal()
            try:
                self.assertEqual(
                    db.query(AgentRun).filter(
                        AgentRun.client_id == self.client_id,
                    ).count(),
                    1,
                )
            finally:
                db.close()

            recovered = self.service.chat(
                "公司欠薪，我要申请劳动仲裁",
                self.client_id,
                request_id,
                self.session_id,
            )

        self.assertTrue(recovered["context"]["run_id"])
        db = SessionLocal()
        try:
            self.assertEqual(
                db.query(AgentRun).filter(
                    AgentRun.client_id == self.client_id,
                ).count(),
                1,
            )
        finally:
            db.close()


if __name__ == "__main__":
    unittest.main()
