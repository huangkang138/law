"""数字人最小全链路 Trace：trace_id(=request_id) 串联 会话→路由→案件→Agent。

正常运行时按 trace_id 可回溯一次会话：请求开始 → 路由决策 → 动作执行
（建案/启动 Run，run_id↔trace_id 关联）→ 完成/取消/失败。步骤级明细
仍以 DB AgentRun.steps 为准，Trace 负责关联与可查询（logs/trace.jsonl）。
"""

import json
import os
import tempfile
import unittest
import uuid
from pathlib import Path
from unittest.mock import patch

from core.database import SessionLocal
from models.db_models import (
    ConversationWorkspaceState,
    DigitalHumanRequest,
    DigitalHumanSession,
    Matter,
)
from services.conversation import tracing
from services.conversation.tracing import (
    link_run,
    set_trace_file,
    trace,
    trace_for_run,
    unlink_run,
)
from services.digital_human_service import DigitalHumanService
from services.voice import VoiceOrchestrator


class _FastJsonChunk:
    content = json.dumps({
        "reply": "这是链路追踪测试回复。",
        "intent": "general_chat",
        "conversation_route": "normal_chat",
        "emotion": "talk_normal",
        "confidence": 0.9,
    }, ensure_ascii=False)


class _FastJsonLlm:
    @staticmethod
    def stream(_messages):
        yield _FastJsonChunk()


def _read_trace_lines(path):
    with open(path, "r", encoding="utf-8") as file:
        return [json.loads(line) for line in file if line.strip()]


class TracingModuleTest(unittest.TestCase):
    """tracing 模块本身：写入、容错与 run 关联。"""

    def setUp(self):
        self.tmp = tempfile.mkdtemp()
        self.path = os.path.join(self.tmp, "trace.jsonl")
        set_trace_file(self.path)

    def tearDown(self):
        set_trace_file(tracing.DEFAULT_TRACE_FILE)

    def test_trace_writes_jsonl_line(self):
        trace("route_decision", "dhr_t1", route="normal_chat", confidence=0.9)
        lines = _read_trace_lines(self.path)
        self.assertEqual(len(lines), 1)
        line = lines[0]
        self.assertEqual(line["trace_id"], "dhr_t1")
        self.assertEqual(line["event"], "route_decision")
        self.assertEqual(line["route"], "normal_chat")
        self.assertEqual(line["confidence"], 0.9)
        self.assertIn("ts", line)

    def test_trace_failure_never_raises(self):
        # trace 失败绝不拖垮业务。
        with patch("builtins.open", side_effect=OSError("模拟磁盘故障")):
            trace("request_start", "dhr_t2")  # 不应抛异常
        self.assertFalse(os.path.exists(self.path))

    def test_run_trace_link_and_unlink(self):
        link_run("run_1", "dhr_t3")
        self.assertEqual(trace_for_run("run_1"), "dhr_t3")
        unlink_run("run_1")
        self.assertIsNone(trace_for_run("run_1"))


class TraceIntegrationTest(unittest.TestCase):
    """服务层集成：同 trace_id 串起 请求→路由→动作→完成，取消与 Agent 关联。"""

    def setUp(self):
        token = uuid.uuid4().hex
        self.client_id = f"dhc_trace_{token}"
        self.session_id = f"dh_trace_{token}"
        self.service = DigitalHumanService.__new__(DigitalHumanService)
        self.service.system_prompt = "测试安全规则"
        self.service.llm = _FastJsonLlm()
        self.service._orchestrator = self.service._build_orchestrator()
        self.service._voice_orchestrator = VoiceOrchestrator(provider=None)
        self.tmp = tempfile.mkdtemp()
        self.trace_path = os.path.join(self.tmp, "trace.jsonl")
        set_trace_file(self.trace_path)

    def tearDown(self):
        set_trace_file(tracing.DEFAULT_TRACE_FILE)
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
                ConversationWorkspaceState.session_id == self.session_id,
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

    def _events_for(self, trace_id):
        return [
            line for line in _read_trace_lines(self.trace_path)
            if line.get("trace_id") == trace_id
        ]

    def test_full_chain_events_linked_by_trace_id(self):
        request_id = f"dhr_trace_{uuid.uuid4().hex}"
        list(self.service.chat_stream(
            "普通问题", self.client_id, request_id,
            self.session_id, chunk_delay=0,
        ))
        events = [line["event"] for line in self._events_for(request_id)]
        # 关键事件按序出现且同一 trace_id。
        self.assertEqual(events[0], "request_start")
        self.assertIn("route_decision", events)
        self.assertIn("action_executed", events)
        self.assertIn("request_completed", events)
        self.assertLess(
            events.index("request_start"), events.index("route_decision"),
            "请求开始必须先于路由决策",
        )
        self.assertLess(
            events.index("route_decision"), events.index("request_completed"),
            "路由决策必须先于完成",
        )
        completed = [
            line for line in self._events_for(request_id)
            if line["event"] == "request_completed"
        ][0]
        self.assertEqual(completed["action_type"], "reply_only")

    def test_cancel_event_recorded(self):
        request_id = f"dhr_trace_{uuid.uuid4().hex}"
        list(self.service.chat_stream(
            "普通问题", self.client_id, request_id,
            self.session_id, chunk_delay=0,
        ))
        self.service.cancel_request(request_id, self.client_id)
        events = [line["event"] for line in self._events_for(request_id)]
        self.assertIn("request_cancelled", events)

    def test_labor_action_links_matter_and_run(self):
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
        request_id = f"dhr_trace_{uuid.uuid4().hex}"
        with patch(
            "services.conversation.actions.ConversationActions._infer_labor_facts",
            return_value=full_facts,
        ):
            with patch(
                "legal_agent_system.facade.LegalAgentFacade._try_sync_authorities",
                return_value={"ok": True, "skipped": True, "reason": "test_offline"},
            ):
                with patch(
                    "legal_agent_system.facade.LegalAgentFacade.start_task",
                    return_value={
                        "run_id": "run_trace_labor",
                        "status": "completed",
                    },
                ):
                    list(self.service.chat_stream(
                        "公司欠薪，我要申请劳动仲裁",
                        self.client_id,
                        request_id,
                        self.session_id,
                        chunk_delay=0,
                    ))
        events = self._events_for(request_id)
        event_names = [line["event"] for line in events]
        self.assertIn("matter_created", event_names)
        self.assertIn("run_started", event_names)
        run_started = [
            line for line in events if line["event"] == "run_started"
        ][0]
        self.assertEqual(run_started["run_id"], "run_trace_labor")
        self.assertEqual(run_started["task_type"], "labor_case_analysis")
        # run_id ↔ trace_id 关联可用于回溯 Agent 步骤。
        self.assertEqual(trace_for_run("run_trace_labor"), request_id)
        unlink_run("run_trace_labor")


class TraceSourceGuardTest(unittest.TestCase):
    """挂点源码守卫：编排器/动作/服务的关键事件不因重构丢失。"""

    def setUp(self):
        root = Path(__file__).resolve().parents[2]
        self.orchestrator = (root / "flask_app/services/conversation/orchestrator.py").read_text(encoding="utf-8")
        self.actions = (root / "flask_app/services/conversation/actions.py").read_text(encoding="utf-8")
        self.service = (root / "flask_app/services/digital_human_service.py").read_text(encoding="utf-8")
        self.tracing = (root / "flask_app/services/conversation/tracing.py").read_text(encoding="utf-8")

    def test_tracing_module_contract(self):
        for fragment in (
            "def trace(event: str, trace_id: str, **fields)",
            "def link_run(",
            "def trace_for_run(",
            "DEFAULT_TRACE_FILE",
        ):
            self.assertIn(fragment, self.tracing, f"tracing 模块缺少: {fragment}")

    def test_orchestrator_hooks(self):
        for fragment in (
            '"route_decision"',
            '"action_executed"',
            '"request_completed"',
            '"request_cancelled"',
            '"request_failed"',
        ):
            self.assertIn(fragment, self.orchestrator, f"编排器缺少挂点: {fragment}")

    def test_actions_hooks(self):
        self.assertIn('"matter_created"', self.actions)
        self.assertIn('"run_started"', self.actions)
        self.assertIn("link_run(run_id, request_id)", self.actions)

    def test_service_hooks(self):
        self.assertIn('"request_start"', self.service)
        self.assertIn('"request_cancelled"', self.service)


if __name__ == "__main__":
    unittest.main()
