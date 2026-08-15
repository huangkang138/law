"""阶段3.7F第一部分：SSE增量呈现专项测试。"""

import json
import unittest
import uuid
from unittest.mock import patch

from flask import Flask
from sqlalchemy.exc import SQLAlchemyError

from core.database import SessionLocal
from models.db_models import (
    AgentRun,
    ConversationWorkspaceState,
    DigitalHumanRequest,
    DigitalHumanSession,
    Matter,
)
from services.conversation.repository import RequestInProgress
from services.conversation.sse import (
    EVENT_COMPLETED,
    EVENT_DELTA,
    EVENT_ERROR,
    EVENT_STATUS,
    STATUS_ACCEPTED,
    STATUS_THINKING,
    encode_event,
    iter_text_chunks,
    stream_error_data,
)
from services.digital_human_service import DigitalHumanService


def _parse_sse_event(event_text):
    """解析一条SSE事件文本，返回(event名, data字典)。"""
    name = ""
    data = None
    for line in event_text.split("\n"):
        if line.startswith("event:"):
            name = line[len("event:"):].strip()
        elif line.startswith("data:"):
            data = json.loads(line[len("data:"):].lstrip())
    return name, data


class SseEncodingTest(unittest.TestCase):
    def test_event_encoding_carries_request_id(self):
        text = encode_event(EVENT_STATUS, {"status": STATUS_ACCEPTED}, "dhr_1")
        self.assertTrue(text.startswith("event: status\n"))
        self.assertTrue(text.endswith("\n\n"))
        self.assertIn('"request_id": "dhr_1"', text)

    def test_event_payload_cannot_override_request_id(self):
        text = encode_event(
            EVENT_DELTA,
            {"text": "你好", "request_id": "dhr_forged"},
            "dhr_real",
        )
        _, payload = _parse_sse_event(text)
        self.assertEqual(payload["request_id"], "dhr_real")
        self.assertEqual(payload["text"], "你好")

    def test_chunks_join_exactly_to_original(self):
        samples = [
            "",
            "你好",
            "这是一段包含中文、标点，以及emoji😀的完整回复。",
            "a" * 37,
        ]
        for text in samples:
            for size in (1, 3, 12):
                joined = "".join(iter_text_chunks(text, size))
                self.assertEqual(joined, text, (text[:20], size))

    def test_chunk_size_must_be_positive(self):
        with self.assertRaises(ValueError):
            list(iter_text_chunks("你好", 0))

    def test_stream_error_mapping_is_stable(self):
        cases = [
            (RequestInProgress("该请求正在处理中"), "REQUEST_IN_PROGRESS", True),
            (PermissionError("无权访问该数字人会话"), "FORBIDDEN", False),
            (LookupError("会话不存在"), "NOT_FOUND", False),
            (ValueError("问题不能为空"), "INVALID_INPUT", False),
            (SQLAlchemyError("模拟数据库故障"), "DATABASE_UNAVAILABLE", True),
            (RuntimeError("模拟内部错误"), "INTERNAL_ERROR", True),
        ]
        for exc, code, retryable in cases:
            data = stream_error_data(exc)
            self.assertEqual(data["code"], code)
            self.assertEqual(data["retryable"], retryable)
            self.assertTrue(data["error"])
        # 通用异常不把原始错误文本透传给前端。
        self.assertEqual(
            stream_error_data(RuntimeError("内部秘密细节"))["error"],
            "数字人暂时无法回答，请稍后重试",
        )


class _Chunk:
    content = json.dumps({
        "reply": "这是流式测试回复。",
        "intent": "general_chat",
        "conversation_route": "labor_triage",
        "emotion": "talk_normal",
        "confidence": 1.0,
    }, ensure_ascii=False)


class _FakeLlm:
    @staticmethod
    def stream(_messages):
        yield _Chunk()


class _RaisingOrchestrator:
    def __init__(self, exc):
        self.exc = exc

    def chat(self, *_args, **_kwargs):
        raise self.exc


class ConversationStreamIntegrationTest(unittest.TestCase):
    def setUp(self):
        token = uuid.uuid4().hex
        self.client_id = f"dhc_stage37f_{token}"
        self.session_id = f"dh_stage37f_{token}"
        self.service = DigitalHumanService.__new__(DigitalHumanService)
        self.service.llm = _FakeLlm()
        self.service.system_prompt = "测试安全规则"
        self.service._orchestrator = self.service._build_orchestrator()

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
            db.query(ConversationWorkspaceState).filter(
                ConversationWorkspaceState.session_id == self.session_id
            ).delete(synchronize_session=False)
            db.query(DigitalHumanRequest).filter(
                DigitalHumanRequest.client_id == self.client_id,
            ).delete(synchronize_session=False)
            db.query(DigitalHumanSession).filter(
                DigitalHumanSession.user_id == self.client_id,
            ).delete(synchronize_session=False)
            db.commit()
        finally:
            db.close()

    def _collect(self, stream):
        events = []
        for event_text in stream:
            events.append(_parse_sse_event(event_text))
        return events

    def test_stream_events_order_and_delta_join_completed(self):
        request_id = f"dhr_stage37f_order_{uuid.uuid4().hex}"
        stream = self.service.chat_stream(
            "公司拖欠工资，我要申请劳动仲裁",
            self.client_id,
            request_id,
            self.session_id,
            chunk_delay=0,
        )
        events = self._collect(stream)

        names = [name for name, _ in events]
        self.assertEqual(names[:2], [EVENT_STATUS, EVENT_STATUS])
        self.assertEqual(
            [payload["status"] for _, payload in events[:2]],
            [STATUS_ACCEPTED, STATUS_THINKING],
        )
        self.assertEqual(names[-1], EVENT_COMPLETED)
        self.assertTrue(all(
            name == EVENT_DELTA for name in names[2:-1]
        ))
        self.assertTrue(all(
            payload["request_id"] == request_id for _, payload in events
        ))

        joined = "".join(
            payload["text"] for name, payload in events[2:-1]
        )
        completed = events[-1][1]
        self.assertEqual(joined, completed["reply"])
        self.assertEqual(completed["session_id"], self.session_id)
        self.assertIn("decision", completed)
        self.assertIn("action", completed)
        self.assertIn("context", completed)

        messages = DigitalHumanService.get_messages(
            self.session_id,
            self.client_id,
        )
        assistant = [item for item in messages if item["role"] == "assistant"]
        self.assertTrue(assistant)
        self.assertEqual(assistant[-1]["content"], completed["reply"])

    def test_stream_retry_with_same_request_id_reuses_cache(self):
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
        request_id = f"dhr_stage37f_cache_{uuid.uuid4().hex}"
        with patch(
            "services.conversation.actions.ConversationActions._infer_labor_facts",
            return_value=full_facts,
        ):
            first = self._collect(self.service.chat_stream(
                "公司欠薪，我要申请劳动仲裁",
                self.client_id,
                request_id,
                self.session_id,
                chunk_delay=0,
            ))
            second = self._collect(self.service.chat_stream(
                "公司欠薪，我要申请劳动仲裁",
                self.client_id,
                request_id,
                self.session_id,
                chunk_delay=0,
            ))

        completed_first = first[-1][1]
        completed_second = second[-1][1]
        self.assertEqual(completed_first, completed_second)
        first_joined = "".join(
            payload["text"] for name, payload in first[2:-1]
        )
        self.assertEqual(first_joined, completed_first["reply"])

        db = SessionLocal()
        try:
            self.assertEqual(
                db.query(Matter).filter(
                    Matter.client_id == self.client_id,
                ).count(),
                1,
            )
            self.assertEqual(
                db.query(AgentRun).filter(
                    AgentRun.client_id == self.client_id,
                ).count(),
                1,
            )
        finally:
            db.close()

    def test_interrupted_stream_still_recovers_history(self):
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
        request_id = f"dhr_stage37f_interrupt_{uuid.uuid4().hex}"
        with patch(
            "services.conversation.actions.ConversationActions._infer_labor_facts",
            return_value=full_facts,
        ):
            stream = self.service.chat_stream(
                "公司欠薪，我要申请劳动仲裁",
                self.client_id,
                request_id,
                self.session_id,
                chunk_delay=0,
            )
            first_event = _parse_sse_event(next(stream))
            second_event = _parse_sse_event(next(stream))
            first_delta = _parse_sse_event(next(stream))
            stream.close()  # 模拟客户端在增量期间断开

        self.assertEqual(first_event[1]["status"], STATUS_ACCEPTED)
        self.assertEqual(second_event[1]["status"], STATUS_THINKING)
        self.assertEqual(first_delta[0], EVENT_DELTA)
        self.assertTrue(first_delta[1]["text"])

        # 服务端已完成持久化：中断后仍可通过历史恢复完整回复。
        db = SessionLocal()
        try:
            record = db.get(DigitalHumanRequest, request_id)
            self.assertEqual(record.status, "completed")
        finally:
            db.close()
        messages = DigitalHumanService.get_messages(
            self.session_id,
            self.client_id,
        )
        assistant = [item for item in messages if item["role"] == "assistant"]
        self.assertTrue(assistant)
        interrupted_reply = assistant[-1]["content"]
        self.assertTrue(interrupted_reply)

        # 同 request_id 重试复用缓存，完整回复与历史一致。
        replay = self._collect(self.service.chat_stream(
            "公司欠薪，我要申请劳动仲裁",
            self.client_id,
            request_id,
            self.session_id,
            chunk_delay=0,
        ))
        self.assertEqual(replay[-1][1]["reply"], interrupted_reply)

    def test_stream_error_event_is_stable_and_retryable(self):
        request_id = f"dhr_stage37f_error_{uuid.uuid4().hex}"
        self.service._orchestrator = _RaisingOrchestrator(
            PermissionError("无权访问该数字人会话")
        )
        events = self._collect(self.service.chat_stream(
            "任意问题",
            self.client_id,
            request_id,
            self.session_id,
            chunk_delay=0,
        ))
        names = [name for name, _ in events]
        self.assertEqual(names, [EVENT_STATUS, EVENT_STATUS, EVENT_ERROR])
        error = events[-1][1]
        self.assertEqual(error["code"], "FORBIDDEN")
        self.assertFalse(error["retryable"])
        self.assertEqual(error["request_id"], request_id)

        self.service._orchestrator = _RaisingOrchestrator(
            RequestInProgress("该请求正在处理中")
        )
        events = self._collect(self.service.chat_stream(
            "任意问题",
            self.client_id,
            request_id,
            self.session_id,
            chunk_delay=0,
        ))
        error = events[-1][1]
        self.assertEqual(error["code"], "REQUEST_IN_PROGRESS")
        self.assertTrue(error["retryable"])

    def test_stream_input_validation_raises_before_generator(self):
        with self.assertRaises(ValueError):
            self.service.chat_stream(
                "   ",
                self.client_id,
                "dhr_stage37f_x",
                self.session_id,
            )
        with self.assertRaises(ValueError):
            self.service.chat_stream(
                "问题",
                self.client_id,
                "bad_request_id",
                self.session_id,
            )


class _FakeStreamService:
    """路由测试用：不调用LLM，直接返回契约事件流。"""

    def chat_stream(
        self, question, client_id, request_id,
        session_id=None, custom_config=None, voice=False,
    ):
        # voice 为 Phase 1 新增的可选契约参数；本假服务始终返回纯文本流。
        reply = "你好世界"

        def generate():
            yield encode_event(EVENT_STATUS, {"status": STATUS_ACCEPTED}, request_id)
            yield encode_event(EVENT_STATUS, {"status": STATUS_THINKING}, request_id)
            for chunk in iter_text_chunks(reply, 2):
                yield encode_event(EVENT_DELTA, {"text": chunk}, request_id)
            yield encode_event(EVENT_COMPLETED, {
                "reply": reply,
                "intent": "general_chat",
                "emotion": "talk_normal",
                "confidence": 1.0,
                "route": None,
                "route_label": None,
                "session_id": session_id or "dh_fake",
                "decision": {
                    "route": "normal_chat",
                    "confidence": 1.0,
                    "reason_code": "fake",
                },
                "action": {
                    "type": "reply_only",
                    "status": "completed",
                    "matter_id": None,
                    "run_id": None,
                    "question": None,
                },
                "context": {
                    "matter_id": None,
                    "run_id": None,
                    "run_status": None,
                    "input_tokens_estimated": 0,
                },
            }, request_id)

        return generate()


class DigitalHumanStreamRouteTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        from routers import digital_human

        cls.blueprint = digital_human
        cls.app = Flask(__name__)
        cls.app.register_blueprint(digital_human.router, url_prefix="/api")
        cls.client = cls.app.test_client()

    def _post(self, payload, headers=None):
        return self.client.post(
            "/api/digital-human/chat/stream",
            json=payload,
            headers=headers or {"X-Digital-Human-Client-ID": "dhc_stage37f_route"},
        )

    def test_stream_endpoint_contract_and_headers(self):
        request_id = f"dhr_stage37f_route_{uuid.uuid4().hex}"
        with patch.object(
            self.blueprint,
            "get_digital_human_service",
            return_value=_FakeStreamService(),
        ):
            response = self._post({
                "question": "你好",
                "request_id": request_id,
                "session_id": "dh_stage37f_route",
            })

        self.assertEqual(response.status_code, 200)
        self.assertIn("text/event-stream", response.headers.get("Content-Type", ""))
        self.assertIn("no-cache", response.headers.get("Cache-Control", ""))
        self.assertEqual(response.headers.get("X-Accel-Buffering"), "no")

        body = response.get_data(as_text=True)
        events = [
            _parse_sse_event(block)
            for block in body.split("\n\n")
            if block.strip()
        ]
        names = [name for name, _ in events]
        self.assertEqual(names[:2], [EVENT_STATUS, EVENT_STATUS])
        self.assertEqual(names[-1], EVENT_COMPLETED)
        joined = "".join(
            payload["text"] for name, payload in events[2:-1]
        )
        completed = events[-1][1]
        self.assertEqual(joined, completed["reply"])
        self.assertEqual(completed["session_id"], "dh_stage37f_route")
        self.assertTrue(all(
            payload["request_id"] == request_id for _, payload in events
        ))

    def test_stream_endpoint_rejects_invalid_input_with_json(self):
        with patch.object(
            self.blueprint,
            "get_digital_human_service",
            return_value=_FakeStreamService(),
        ):
            missing_question = self._post({"request_id": "dhr_stage37f_x"})
            self.assertEqual(missing_question.status_code, 400)
            self.assertTrue(missing_question.is_json)
            self.assertIn("question", missing_question.get_json()["error"])

            bad_request = self._post({
                "question": "你好",
                "request_id": "not_dhr",
            })
            self.assertEqual(bad_request.status_code, 400)
            self.assertIn("request_id", bad_request.get_json()["error"])


if __name__ == "__main__":
    unittest.main()
