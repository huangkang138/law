"""阶段3.7F第二部分：服务端取消专项测试。"""

import json
import re
import threading
import time
import unittest
import uuid
from datetime import datetime, timedelta, timezone
from pathlib import Path
from unittest.mock import patch

from flask import Flask

from core.database import SessionLocal
from models.db_models import (
    AgentRun,
    ConversationWorkspaceState,
    DigitalHumanMessage,
    DigitalHumanRequest,
    DigitalHumanSession,
    Matter,
)
from services.conversation import cancel as cancel_mod
from services.conversation.cancel import (
    REGISTRY_TTL_SECONDS,
    ConversationCancelled,
    arm,
    disarm,
    is_cancelled,
    set_cancelled,
)
from services.conversation.repository import (
    ConversationRepository,
    RequestInProgress,
)
from services.conversation.sse import EVENT_ERROR, EVENT_STATUS
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


class CancelRegistryTest(unittest.TestCase):
    def test_arm_set_disarm(self):
        request_id = f"dhr_reg_{uuid.uuid4().hex}"
        try:
            arm(request_id)
            self.assertFalse(is_cancelled(request_id))
            set_cancelled(request_id)
            self.assertTrue(is_cancelled(request_id))
            disarm(request_id)
            self.assertFalse(is_cancelled(request_id))
        finally:
            disarm(request_id)

    def test_arm_does_not_reset_existing_flag(self):
        request_id = f"dhr_reg_{uuid.uuid4().hex}"
        try:
            set_cancelled(request_id)
            arm(request_id)
            self.assertTrue(is_cancelled(request_id))
        finally:
            disarm(request_id)

    def test_registry_ttl_prune(self):
        request_id = f"dhr_reg_{uuid.uuid4().hex}"
        try:
            arm(request_id)
            with cancel_mod._REGISTRY_LOCK:
                cancel_mod._REGISTRY[request_id].created_at -= (
                    REGISTRY_TTL_SECONDS + 1
                )
            self.assertFalse(is_cancelled(request_id))
            with cancel_mod._REGISTRY_LOCK:
                self.assertNotIn(request_id, cancel_mod._REGISTRY)
        finally:
            disarm(request_id)

    def test_db_poll_detects_cancelling_and_throttles(self):
        token = uuid.uuid4().hex
        request_id = f"dhr_reg_{token}"
        session_id = f"dh_reg_{token}"
        client_id = f"dhc_reg_{token}"
        db = SessionLocal()
        try:
            db.add(DigitalHumanSession(
                id=session_id, user_id=client_id, title="注册表测试", is_active=True,
            ))
            db.add(DigitalHumanRequest(
                request_id=request_id,
                client_id=client_id,
                session_id=session_id,
                status="cancelling",
                lease_token="lease",
                lease_expires_at=datetime.now(timezone.utc) + timedelta(minutes=5),
            ))
            db.commit()
        finally:
            db.close()

        try:
            arm(request_id)
            self.assertTrue(is_cancelled(request_id, poll_db=True))
            # 轮询发现取消后本地标志已置位：后续调用走进程标志短路。
            self.assertTrue(is_cancelled(request_id, poll_db=True))
        finally:
            disarm(request_id)
            db = SessionLocal()
            try:
                db.query(DigitalHumanRequest).filter(
                    DigitalHumanRequest.request_id == request_id
                ).delete(synchronize_session=False)
                db.query(DigitalHumanSession).filter(
                    DigitalHumanSession.id == session_id
                ).delete(synchronize_session=False)
                db.commit()
            finally:
                db.close()


class CancelRepositoryTest(unittest.TestCase):
    def setUp(self):
        token = uuid.uuid4().hex
        self.client_id = f"dhc_repo_{token}"
        self.session_id = f"dh_repo_{token}"
        self.request_id = f"dhr_repo_{token}"
        db = SessionLocal()
        try:
            db.add(DigitalHumanSession(
                id=self.session_id, user_id=self.client_id, title="仓库测试", is_active=True,
            ))
            db.commit()
        finally:
            db.close()

    def tearDown(self):
        db = SessionLocal()
        try:
            db.query(ConversationWorkspaceState).filter(
                ConversationWorkspaceState.session_id == self.session_id
            ).delete(synchronize_session=False)
            db.query(DigitalHumanRequest).filter(
                DigitalHumanRequest.client_id == self.client_id
            ).delete(synchronize_session=False)
            db.query(DigitalHumanSession).filter(
                DigitalHumanSession.user_id == self.client_id
            ).delete(synchronize_session=False)
            db.commit()
        finally:
            db.close()

    def _insert_request(self, **overrides):
        values = {
            "request_id": self.request_id,
            "client_id": self.client_id,
            "session_id": self.session_id,
            "status": "processing",
            "lease_token": "lease_a",
            "lease_expires_at": datetime.now(timezone.utc) + timedelta(minutes=5),
            "checkpoint_json": None,
        }
        values.update(overrides)
        db = SessionLocal()
        try:
            db.add(DigitalHumanRequest(**values))
            db.commit()
        finally:
            db.close()

    def test_mark_cancelling_keeps_lease_and_checkpoint(self):
        checkpoint = {"question": "问题"}
        self._insert_request(checkpoint_json=checkpoint)
        status = ConversationRepository.mark_cancelling(self.request_id)
        self.assertEqual(status, "cancelling")
        db = SessionLocal()
        try:
            record = db.get(DigitalHumanRequest, self.request_id)
            self.assertEqual(record.status, "cancelling")
            self.assertEqual(record.lease_token, "lease_a")
            self.assertEqual(record.checkpoint_json, checkpoint)
        finally:
            db.close()

    def test_mark_cancelling_ignores_terminal(self):
        self._insert_request(status="completed")
        status = ConversationRepository.mark_cancelling(self.request_id)
        self.assertEqual(status, "completed")

    def test_mark_cancelled_asserts_lease_and_keeps_checkpoint(self):
        checkpoint = {"question": "问题"}
        self._insert_request(status="cancelling", checkpoint_json=checkpoint)
        with self.assertRaises(RequestInProgress):
            ConversationRepository.mark_cancelled(self.request_id, "wrong_lease")
        ConversationRepository.mark_cancelled(self.request_id, "lease_a")
        db = SessionLocal()
        try:
            record = db.get(DigitalHumanRequest, self.request_id)
            self.assertEqual(record.status, "cancelled")
            self.assertIsNone(record.lease_token)
            self.assertEqual(record.checkpoint_json, checkpoint)
        finally:
            db.close()

    def test_begin_request_retry_from_cancelled(self):
        self._insert_request(
            status="cancelled",
            lease_token=None,
            lease_expires_at=None,
            checkpoint_json={"question": "问题"},
        )
        db = SessionLocal()
        try:
            db.add(DigitalHumanMessage(
                id=f"dhmsg_{uuid.uuid4().hex}",
                session_id=self.session_id,
                request_id=self.request_id,
                role="user",
                content="问题",
            ))
            db.commit()
        finally:
            db.close()
        repository = ConversationRepository()
        _cached, _message_id, lease = repository.begin_request(
            self.request_id, self.client_id, self.session_id, "问题",
        )
        self.assertTrue(lease)
        db = SessionLocal()
        try:
            record = db.get(DigitalHumanRequest, self.request_id)
            self.assertEqual(record.status, "action_running")
        finally:
            db.close()

    def test_begin_request_rerun_cancelled_without_checkpoint(self):
        self._insert_request(status="cancelled", lease_token=None, lease_expires_at=None)
        db = SessionLocal()
        try:
            db.add(DigitalHumanMessage(
                id=f"dhmsg_{uuid.uuid4().hex}",
                session_id=self.session_id,
                request_id=self.request_id,
                role="user",
                content="问题",
            ))
            db.commit()
        finally:
            db.close()
        repository = ConversationRepository()
        _cached, _message_id, lease = repository.begin_request(
            self.request_id, self.client_id, self.session_id, "问题",
        )
        self.assertTrue(lease)
        db = SessionLocal()
        try:
            record = db.get(DigitalHumanRequest, self.request_id)
            self.assertEqual(record.status, "processing")
        finally:
            db.close()

    def test_begin_request_rejects_cancelling_with_valid_lease(self):
        self._insert_request(status="cancelling")
        repository = ConversationRepository()
        with self.assertRaises(ConversationCancelled):
            repository.begin_request(
                self.request_id, self.client_id, self.session_id, "问题",
            )

    def test_other_active_conflict_includes_cancelling(self):
        self._insert_request(status="cancelling")
        repository = ConversationRepository()
        with self.assertRaises(RequestInProgress):
            repository.begin_request(
                f"dhr_other_{uuid.uuid4().hex}",
                self.client_id,
                self.session_id,
                "问题",
            )

    def test_complete_request_rejects_cancelled_statuses(self):
        from services.conversation.schemas import MemorySnapshot

        parsed = {
            "reply": "普通回复",
            "intent": "general_chat",
            "emotion": "talk_normal",
            "confidence": 0.9,
        }
        for status in ("cancelling", "cancelled"):
            with self.subTest(status=status):
                request_id = f"dhr_complete_{uuid.uuid4().hex}"
                self._insert_request(
                    request_id=request_id,
                    status=status,
                    lease_token="lease_a",
                )
                with self.assertRaises(ConversationCancelled):
                    ConversationRepository().complete_request(
                        request_id,
                        self.session_id,
                        parsed,
                        {"ok": True},
                        MemorySnapshot(session_id=self.session_id),
                        "lease_a",
                    )
                db = SessionLocal()
                try:
                    record = db.get(DigitalHumanRequest, request_id)
                    self.assertEqual(record.status, status)
                    self.assertIsNone(record.response_json)
                    self.assertEqual(record.lease_token, "lease_a")
                    assistant = db.query(DigitalHumanMessage).filter(
                        DigitalHumanMessage.session_id == self.session_id,
                        DigitalHumanMessage.role == "assistant",
                    ).count()
                    self.assertEqual(assistant, 0)
                finally:
                    db.close()


class _SlowChunk:
    def __init__(self, content):
        self.content = content


class _SlowStreamLlm:
    """每 20ms 产出一个分块；生成器被 close 时置 closed=True。"""

    def __init__(self):
        self.served = threading.Event()
        self.closed = False
        self._chunks_served = 0

    def stream(self, _messages):
        try:
            for _ in range(200):
                self._chunks_served += 1
                self.served.set()
                yield _SlowChunk("你")
                time.sleep(0.02)
        finally:
            self.closed = True


class _FastJsonChunk:
    content = json.dumps({
        "reply": "这是取消测试的普通回复。",
        "intent": "general_chat",
        "conversation_route": "normal_chat",
        "emotion": "talk_normal",
        "confidence": 0.9,
    }, ensure_ascii=False)


class _FastJsonLlm:
    @staticmethod
    def stream(_messages):
        yield _FastJsonChunk()


class CancelServiceIntegrationTest(unittest.TestCase):
    def setUp(self):
        token = uuid.uuid4().hex
        self.client_id = f"dhc_cancel_{token}"
        self.session_id = f"dh_cancel_{token}"
        self.service = DigitalHumanService.__new__(DigitalHumanService)
        self.service.system_prompt = "测试安全规则"
        self.service.llm = _FastJsonLlm()
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

    def _consume_in_thread(self, stream, events, errors):
        def consume():
            try:
                for event_text in stream:
                    events.append(_parse_sse_event(event_text))
            except Exception as exc:  # pragma: no cover - 调试辅助
                errors.append(exc)
        worker = threading.Thread(target=consume)
        worker.start()
        return worker

    def test_cancel_during_llm_aborts_stream_and_marks_cancelled(self):
        slow_llm = _SlowStreamLlm()
        self.service.llm = slow_llm
        self.service._orchestrator = self.service._build_orchestrator()
        request_id = f"dhr_cancel_{uuid.uuid4().hex}"
        events = []
        errors = []
        stream = self.service.chat_stream(
            "普通问题",
            self.client_id,
            request_id,
            self.session_id,
            chunk_delay=0,
        )
        worker = self._consume_in_thread(stream, events, errors)
        self.assertTrue(slow_llm.served.wait(timeout=10))

        result = self.service.cancel_request(request_id, self.client_id)
        self.assertTrue(result["cancelled"])
        self.assertEqual(result["status"], "cancelling")

        worker.join(timeout=30)
        self.assertFalse(worker.is_alive())
        self.assertTrue(slow_llm.closed)

        names = [name for name, _ in events]
        self.assertEqual(names[:2], [EVENT_STATUS, EVENT_STATUS])
        self.assertEqual(events[-1][0], EVENT_ERROR)
        error = events[-1][1]
        self.assertEqual(error["code"], "CANCELLED")
        self.assertTrue(error["retryable"])

        db = SessionLocal()
        try:
            record = db.get(DigitalHumanRequest, request_id)
            self.assertEqual(record.status, "cancelled")
            self.assertIsNone(record.lease_token)
            assistant = db.query(DigitalHumanMessage).filter(
                DigitalHumanMessage.session_id == self.session_id,
                DigitalHumanMessage.role == "assistant",
            ).count()
            self.assertEqual(assistant, 0)
        finally:
            db.close()

    def test_cancel_during_llm_creates_no_matter_for_triage(self):
        slow_llm = _SlowStreamLlm()
        self.service.llm = slow_llm
        self.service._orchestrator = self.service._build_orchestrator()
        request_id = f"dhr_cancel_{uuid.uuid4().hex}"
        events = []
        errors = []
        stream = self.service.chat_stream(
            "公司拖欠工资，我要申请劳动仲裁",
            self.client_id,
            request_id,
            self.session_id,
            chunk_delay=0,
        )
        worker = self._consume_in_thread(stream, events, errors)
        self.assertTrue(slow_llm.served.wait(timeout=10))
        self.service.cancel_request(request_id, self.client_id)
        worker.join(timeout=30)

        self.assertEqual(events[-1][1]["code"], "CANCELLED")
        db = SessionLocal()
        try:
            self.assertEqual(
                db.query(Matter).filter(
                    Matter.client_id == self.client_id,
                ).count(),
                0,
            )
            self.assertEqual(
                db.query(AgentRun).filter(
                    AgentRun.client_id == self.client_id,
                ).count(),
                0,
            )
            record = db.get(DigitalHumanRequest, request_id)
            self.assertIsNone(record.checkpoint_json)
        finally:
            db.close()

    def test_cancel_then_retry_same_request_id_reruns(self):
        slow_llm = _SlowStreamLlm()
        self.service.llm = slow_llm
        self.service._orchestrator = self.service._build_orchestrator()
        request_id = f"dhr_cancel_{uuid.uuid4().hex}"
        events = []
        errors = []
        stream = self.service.chat_stream(
            "普通问题",
            self.client_id,
            request_id,
            self.session_id,
            chunk_delay=0,
        )
        worker = self._consume_in_thread(stream, events, errors)
        self.assertTrue(slow_llm.served.wait(timeout=10))
        self.service.cancel_request(request_id, self.client_id)
        worker.join(timeout=30)
        self.assertEqual(events[-1][1]["code"], "CANCELLED")

        # 快 LLM 重跑同一 request_id：正常完成。
        self.service.llm = _FastJsonLlm()
        self.service._orchestrator = self.service._build_orchestrator()
        retry_events = []
        retry_stream = self.service.chat_stream(
            "普通问题",
            self.client_id,
            request_id,
            self.session_id,
            chunk_delay=0,
        )
        for event_text in retry_stream:
            retry_events.append(_parse_sse_event(event_text))
        self.assertEqual(retry_events[-1][0], "completed")
        db = SessionLocal()
        try:
            record = db.get(DigitalHumanRequest, request_id)
            self.assertEqual(record.status, "completed")
        finally:
            db.close()

    def test_cancel_before_begin_request_short_circuits(self):
        request_id = f"dhr_cancel_{uuid.uuid4().hex}"
        set_cancelled(request_id)
        events = []
        errors = []
        for event_text in self.service.chat_stream(
            "普通问题",
            self.client_id,
            request_id,
            self.session_id,
            chunk_delay=0,
        ):
            events.append(_parse_sse_event(event_text))
        self.assertEqual(events[-1][0], EVENT_ERROR)
        self.assertEqual(events[-1][1]["code"], "CANCELLED")
        db = SessionLocal()
        try:
            self.assertIsNone(db.get(DigitalHumanRequest, request_id))
        finally:
            db.close()
        disarm(request_id)

    def test_cancel_during_actions_keeps_side_effects_and_recovers(self):
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
        from services.conversation.actions import ConversationActions

        real_execute = ConversationActions.execute
        action_entered = threading.Event()
        action_release = threading.Event()

        def blocking_execute(self, decision, question, client_id, session_id, context, **kwargs):
            result = real_execute(
                self, decision, question, client_id, session_id, context, **kwargs,
            )
            action_entered.set()
            action_release.wait(timeout=15)
            return result

        request_id = f"dhr_cancel_{uuid.uuid4().hex}"
        events = []
        errors = []
        with patch(
            "services.conversation.actions.ConversationActions._infer_labor_facts",
            return_value=full_facts,
        ):
            with patch.object(ConversationActions, "execute", new=blocking_execute):
                stream = self.service.chat_stream(
                    "公司欠薪，我要申请劳动仲裁",
                    self.client_id,
                    request_id,
                    self.session_id,
                    chunk_delay=0,
                )
                worker = self._consume_in_thread(stream, events, errors)
                self.assertTrue(
                    action_entered.wait(timeout=30),
                    f"动作未进入: events={events} errors={errors}",
                )
                result = self.service.cancel_request(request_id, self.client_id)
                self.assertTrue(result["cancelled"])
                action_release.set()
                worker.join(timeout=30)
        self.assertFalse(worker.is_alive())
        self.assertEqual(events[-1][1]["code"], "CANCELLED")

        db = SessionLocal()
        try:
            record = db.get(DigitalHumanRequest, request_id)
            self.assertEqual(record.status, "cancelled")
            self.assertIsNotNone(record.action_resource_json)
            self.assertTrue(record.action_resource_json.get("matter_id"))
            self.assertEqual(
                db.query(Matter).filter(Matter.client_id == self.client_id).count(),
                1,
            )
            self.assertEqual(
                db.query(AgentRun).filter(AgentRun.client_id == self.client_id).count(),
                1,
            )
        finally:
            db.close()

        # 同 request_id 重试：按检查点幂等恢复，不重复创建。
        retry_events = []
        with patch(
            "services.conversation.actions.ConversationActions._infer_labor_facts",
            return_value=full_facts,
        ):
            for event_text in self.service.chat_stream(
                "公司欠薪，我要申请劳动仲裁",
                self.client_id,
                request_id,
                self.session_id,
                chunk_delay=0,
            ):
                retry_events.append(_parse_sse_event(event_text))
        self.assertEqual(retry_events[-1][0], "completed")
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
        finally:
            db.close()

    def test_cancel_before_actions_skips_side_effects(self):
        from services.conversation.orchestrator import ConversationOrchestrator

        real_ensure = ConversationOrchestrator._ensure_not_cancelled
        check_entered = threading.Event()
        check_release = threading.Event()
        calls = {"count": 0}

        def blocking_ensure(self, request_id, session_id, lease_token):
            calls["count"] += 1
            if calls["count"] == 1:
                check_entered.set()
                check_release.wait(timeout=15)
            return real_ensure(self, request_id, session_id, lease_token)

        request_id = f"dhr_cancel_{uuid.uuid4().hex}"
        events = []
        errors = []
        with patch.object(ConversationOrchestrator, "_ensure_not_cancelled", new=blocking_ensure):
            stream = self.service.chat_stream(
                "公司拖欠工资，我要申请劳动仲裁",
                self.client_id,
                request_id,
                self.session_id,
                chunk_delay=0,
            )
            worker = self._consume_in_thread(stream, events, errors)
            self.assertTrue(
                check_entered.wait(timeout=30),
                f"检查点未进入: events={events} errors={errors}",
            )
            result = self.service.cancel_request(request_id, self.client_id)
            self.assertTrue(result["cancelled"])
            check_release.set()
            worker.join(timeout=30)
        self.assertFalse(worker.is_alive())
        self.assertEqual(events[-1][1]["code"], "CANCELLED")
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
            record = db.get(DigitalHumanRequest, request_id)
            self.assertEqual(record.status, "cancelled")
        finally:
            db.close()

    def test_cancel_in_action_completed_window_keeps_checkpoint_and_recovers(self):
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
        request_id = f"dhr_cancel_{uuid.uuid4().hex}"
        with patch(
            "services.conversation.actions.ConversationActions._infer_labor_facts",
            return_value=full_facts,
        ):
            first_events = []
            for event_text in self.service.chat_stream(
                "公司欠薪，我要申请劳动仲裁",
                self.client_id,
                request_id,
                self.session_id,
                chunk_delay=0,
            ):
                first_events.append(_parse_sse_event(event_text))
        self.assertEqual(first_events[-1][0], "completed")

        # 模拟崩溃残留：action_completed + 过期租约。
        db = SessionLocal()
        try:
            record = db.get(DigitalHumanRequest, request_id)
            record.status = "action_completed"
            record.lease_token = "stale_lease"
            record.lease_expires_at = datetime.now(timezone.utc) - timedelta(minutes=1)
            db.commit()
        finally:
            db.close()

        # 取消恰在完成窗口到达：落 cancelled 但检查点保留。
        from services.conversation.orchestrator import ConversationOrchestrator

        real_ensure = ConversationOrchestrator._ensure_not_cancelled
        def ensure_then_flag(self, request_id, session_id, lease_token):
            set_cancelled(request_id)
            return real_ensure(self, request_id, session_id, lease_token)

        with patch.object(ConversationOrchestrator, "_ensure_not_cancelled", new=ensure_then_flag):
            second_events = []
            for event_text in self.service.chat_stream(
                "公司欠薪，我要申请劳动仲裁",
                self.client_id,
                request_id,
                self.session_id,
                chunk_delay=0,
            ):
                second_events.append(_parse_sse_event(event_text))
        self.assertEqual(second_events[-1][1]["code"], "CANCELLED")
        db = SessionLocal()
        try:
            record = db.get(DigitalHumanRequest, request_id)
            self.assertEqual(record.status, "cancelled")
            self.assertIsNotNone(record.checkpoint_json)
        finally:
            db.close()

        # 再重试：按检查点幂等恢复并完成，Matter/Run 仍各 1。
        with patch(
            "services.conversation.actions.ConversationActions._infer_labor_facts",
            return_value=full_facts,
        ):
            third_events = []
            for event_text in self.service.chat_stream(
                "公司欠薪，我要申请劳动仲裁",
                self.client_id,
                request_id,
                self.session_id,
                chunk_delay=0,
            ):
                third_events.append(_parse_sse_event(event_text))
        self.assertEqual(third_events[-1][0], "completed")
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
        finally:
            db.close()


    def test_cancel_landing_between_action_completed_and_complete_request(self):
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
        real_mark_action_completed = ConversationRepository.mark_action_completed

        def completing_then_cancel(self, request_id, lease_token, resources, checkpoint):
            real_mark_action_completed(request_id, lease_token, resources, checkpoint)
            # 模拟取消端点恰在动作完成后到达（进程标志 + 库状态同时生效；
            # 不经会话锁，避免同线程重入 advisory lock 死锁）。
            set_cancelled(request_id)
            ConversationRepository.mark_cancelling(request_id)

        request_id = f"dhr_cancel_{uuid.uuid4().hex}"
        events = []
        with patch(
            "services.conversation.actions.ConversationActions._infer_labor_facts",
            return_value=full_facts,
        ):
            with patch.object(
                ConversationRepository,
                "mark_action_completed",
                new=completing_then_cancel,
            ):
                for event_text in self.service.chat_stream(
                    "公司欠薪，我要申请劳动仲裁",
                    self.client_id,
                    request_id,
                    self.session_id,
                    chunk_delay=0,
                ):
                    events.append(_parse_sse_event(event_text))
        self.assertEqual(events[-1][0], EVENT_ERROR)
        self.assertEqual(events[-1][1]["code"], "CANCELLED")

        db = SessionLocal()
        try:
            record = db.get(DigitalHumanRequest, request_id)
            self.assertEqual(record.status, "cancelled")
            self.assertIsNotNone(record.checkpoint_json)
            self.assertTrue(record.action_resource_json.get("matter_id"))
            self.assertEqual(
                db.query(Matter).filter(Matter.client_id == self.client_id).count(),
                1,
            )
        finally:
            db.close()

        # 同 request_id 重试：检查点幂等恢复并正常完成，Matter 不重复创建。
        retry_events = []
        with patch(
            "services.conversation.actions.ConversationActions._infer_labor_facts",
            return_value=full_facts,
        ):
            for event_text in self.service.chat_stream(
                "公司欠薪，我要申请劳动仲裁",
                self.client_id,
                request_id,
                self.session_id,
                chunk_delay=0,
            ):
                retry_events.append(_parse_sse_event(event_text))
        self.assertEqual(retry_events[-1][0], "completed")
        db = SessionLocal()
        try:
            self.assertEqual(
                db.query(Matter).filter(Matter.client_id == self.client_id).count(),
                1,
            )
            record = db.get(DigitalHumanRequest, request_id)
            self.assertEqual(record.status, "completed")
        finally:
            db.close()


class _FakeCancelService:
    def __init__(self, result=None, exc=None):
        self.result = result or {"cancelled": True, "request_id": "dhr_fake", "status": "cancelling"}
        self.exc = exc

    def cancel_request(self, _request_id, _client_id):
        if self.exc is not None:
            raise self.exc
        return self.result


class CancelRouteTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        from routers import digital_human

        cls.blueprint = digital_human
        cls.app = Flask(__name__)
        cls.app.register_blueprint(digital_human.router, url_prefix="/api")
        cls.client = cls.app.test_client()

    def _post(self, payload, headers=None):
        return self.client.post(
            "/api/digital-human/chat/cancel",
            json=payload,
            headers=headers or {"X-Digital-Human-Client-ID": "dhc_cancel_route"},
        )

    def test_cancel_endpoint_validation(self):
        with patch.object(
            self.blueprint, "get_digital_human_service",
            return_value=_FakeCancelService(),
        ):
            bad_body = self._post(None)
            self.assertEqual(bad_body.status_code, 400)
            bad_id = self._post({"request_id": "not_dhr"})
            self.assertEqual(bad_id.status_code, 400)
            self.assertIn("request_id", bad_id.get_json()["error"])

    def test_cancel_endpoint_maps_domain_errors(self):
        with patch.object(
            self.blueprint, "get_digital_human_service",
            return_value=_FakeCancelService(exc=LookupError("数字人请求不存在")),
        ):
            missing = self._post({"request_id": "dhr_missing"})
            self.assertEqual(missing.status_code, 404)
            self.assertEqual(missing.get_json()["code"], "NOT_FOUND")
        with patch.object(
            self.blueprint, "get_digital_human_service",
            return_value=_FakeCancelService(exc=PermissionError("无权取消该请求")),
        ):
            forbidden = self._post({"request_id": "dhr_missing"})
            self.assertEqual(forbidden.status_code, 403)
            self.assertEqual(forbidden.get_json()["code"], "FORBIDDEN")

    def test_cancel_endpoint_contract(self):
        with patch.object(
            self.blueprint, "get_digital_human_service",
            return_value=_FakeCancelService(),
        ):
            response = self._post({"request_id": "dhr_ok"})
        self.assertEqual(response.status_code, 200)
        payload = response.get_json()
        self.assertTrue(payload["success"])
        self.assertTrue(payload["cancelled"])
        self.assertEqual(payload["status"], "cancelling")

    def test_chat_route_maps_cancelled_to_409(self):
        class _CancellingService:
            def chat(self, **_kwargs):
                raise ConversationCancelled()
        with patch.object(
            self.blueprint, "get_digital_human_service",
            return_value=_CancellingService(),
        ):
            response = self.client.post(
                "/api/digital-human/chat",
                json={
                    "question": "普通问题",
                    "request_id": "dhr_cancel_route",
                },
                headers={"X-Digital-Human-Client-ID": "dhc_cancel_route"},
            )
        self.assertEqual(response.status_code, 409)
        self.assertEqual(response.get_json()["code"], "CANCELLED")
        self.assertTrue(response.get_json()["retryable"])

    def test_frontend_cancel_wiring_guards(self):
        root = Path(__file__).resolve().parents[2]
        store = (
            root / "frontend/src/store/digitalHumanStore.ts"
        ).read_text(encoding="utf-8")
        api = (
            root / "frontend/src/services/digitalHumanApi.ts"
        ).read_text(encoding="utf-8")
        self.assertIn("cancelDigitalHumanChatRequest", api)
        self.assertIn("/api/digital-human/chat/cancel", api)
        self.assertIn("activeRequestId", store)
        self.assertIn("void cancelDigitalHumanChatRequest(requestId)", store)
        self.assertIn("code === 'CANCELLED'", store)
        self.assertIn("'已停止回复'", store)

    def test_frontend_stop_notice_synchronous_without_error_bubble(self):
        root = Path(__file__).resolve().parents[2]
        store = (
            root / "frontend/src/store/digitalHumanStore.ts"
        ).read_text(encoding="utf-8")
        match = re.search(
            r"cancelRequest: \(\) => \{(.*?)\n      \},",
            store,
            re.S,
        )
        self.assertIsNotNone(match, "未找到 cancelRequest 函数体")
        body = match.group(1)
        # 点击停止后提示必须同步给出且不清空（操作序列已失效，
        # 异步 CANCELLED 分支不会执行）；不得追加错误气泡。
        self.assertIn("streamFallbackNotice: '已停止回复'", body)
        self.assertNotIn("streamFallbackNotice: ''", body)
        self.assertNotIn("createMessageId('error')", body)


if __name__ == "__main__":
    unittest.main()
