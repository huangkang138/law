"""阶段3.7F返修：真实模型结构化输出解析可靠性专项测试。

覆盖真实浏览器发现的失败类型：
- 模型返回纯文本（无JSON）时不再出现固定兜底句污染历史；
- 首次响应非JSON时强化格式指令重试一次；
- 平衡提取、字符串内裸换行与尾逗号修复。
"""

import json
import unittest
import uuid

from core.database import SessionLocal
from models.db_models import (
    ConversationWorkspaceState,
    DigitalHumanRequest,
    DigitalHumanSession,
    Matter,
)
from services.digital_human_service import DigitalHumanService


class ParseReliabilityTest(unittest.TestCase):
    @staticmethod
    def parse(raw):
        return DigitalHumanService._parse_llm_response(raw)

    def test_strict_json_parses(self):
        result = self.parse(
            '{"reply": "你好", "intent": "general_chat", "emotion": "talk_normal", "confidence": 0.9}'
        )
        self.assertEqual(result["reply"], "你好")
        self.assertEqual(result["confidence"], 0.9)

    def test_fenced_json_parses(self):
        result = self.parse(
            '```json\n{"reply": "你好", "intent": "general_chat", "confidence": 0.8}\n```'
        )
        self.assertEqual(result["reply"], "你好")

    def test_json_with_surrounding_prose_extracts(self):
        result = self.parse(
            '好的，这是回答：{"reply": "你好", "intent": "general_chat", "confidence": 0.7} 希望对你有帮助'
        )
        self.assertEqual(result["reply"], "你好")

    def test_literal_newline_inside_string_is_repaired(self):
        raw = '{"reply": "第一行\n第二行", "intent": "general_chat", "confidence": 0.6}'
        result = self.parse(raw)
        self.assertEqual(result["reply"], "第一行\n第二行")

    def test_double_escaped_layout_characters_are_normalized(self):
        raw = json.dumps({
            "reply": r"材料清单：\n\n1. 身份证明\n2. 工资流水\t备注",
            "intent": "general_chat",
            "confidence": 0.8,
        }, ensure_ascii=False)
        result = self.parse(raw)
        self.assertEqual(
            result["reply"],
            "材料清单：\n\n1. 身份证明\n2. 工资流水\t备注",
        )

    def test_intentional_escaped_backslash_is_preserved(self):
        result = self.parse(json.dumps({
            "reply": r"示例字符：\\n",
            "intent": "general_chat",
        }, ensure_ascii=False))
        self.assertEqual(result["reply"], r"示例字符：\\n")

    def test_trailing_comma_is_repaired(self):
        result = self.parse('{"reply": "你好", "intent": "general_chat",}')
        self.assertEqual(result["reply"], "你好")

    def test_prose_degradation_returns_model_text(self):
        prose = "您好！试用期最长是**6个月**。合同期限越长，试用期可以越长，但上限就是6个月。"
        result = self.parse(prose)
        self.assertEqual(result["reply"], prose.replace("**", ""))
        self.assertEqual(result["intent"], "general_chat")
        self.assertIsNone(result["conversation_route"])
        self.assertEqual(result["confidence"], 0.0)

    def test_broken_json_with_braces_does_not_degrade_to_prose(self):
        # 含花括号说明更可能是损坏的JSON而不是纯文本。
        result = self.parse('{"reply": "你好", ')
        self.assertEqual(result["reply"], "我还不太确定你的需求，可以换一种简单的说法告诉我吗？")

    def test_garbage_falls_back_to_fixed_reply(self):
        result = self.parse("a")
        self.assertEqual(result["reply"], "我还不太确定你的需求，可以换一种简单的说法告诉我吗？")

    def test_invalid_route_and_emotion_are_normalized(self):
        result = self.parse(
            '{"reply": "你好", "conversation_route": "free_form_tool_call", "emotion": "angry", "confidence": 2.0}'
        )
        self.assertIsNone(result["conversation_route"])
        self.assertEqual(result["emotion"], "talk_normal")
        self.assertEqual(result["confidence"], 1.0)


class _QueueChunk:
    def __init__(self, content):
        self.content = content


class _QueueLlm:
    """按队列依次返回payload；payload为Exception时抛出。"""

    def __init__(self, payloads):
        self.payloads = list(payloads)
        self.calls = 0
        self.last_messages = None

    def stream(self, messages):
        self.calls += 1
        self.last_messages = messages
        payload = self.payloads.pop(0)
        if isinstance(payload, Exception):
            raise payload
        yield _QueueChunk(payload)


VALID_JSON = (
    '{"reply": "重试后的回答", "intent": "general_chat", '
    '"conversation_route": "normal_chat", "emotion": "talk_normal", "confidence": 0.8}'
)
PROSE = "您好！试用期最长是6个月。"


class InvokeRetryTest(unittest.TestCase):
    def test_retries_once_when_first_response_is_prose(self):
        llm = _QueueLlm([PROSE, VALID_JSON])
        raw = DigitalHumanService._invoke_llm_streaming(
            [{"role": "user", "content": "问题"}],
            llm,
        )
        self.assertEqual(raw, VALID_JSON)
        self.assertEqual(llm.calls, 2)
        last_human = [
            item for item in llm.last_messages
            if getattr(item, "content", "") and "合法JSON" in str(item.content)
        ]
        self.assertTrue(last_human)

    def test_no_retry_when_first_response_is_valid(self):
        llm = _QueueLlm([VALID_JSON])
        raw = DigitalHumanService._invoke_llm_streaming([], llm)
        self.assertEqual(raw, VALID_JSON)
        self.assertEqual(llm.calls, 1)

    def test_returns_second_prose_for_downstream_degradation(self):
        llm = _QueueLlm([PROSE, PROSE])
        raw = DigitalHumanService._invoke_llm_streaming([], llm)
        self.assertEqual(raw, PROSE)
        self.assertEqual(llm.calls, 2)

    def test_empty_response_raises(self):
        llm = _QueueLlm([""])
        with self.assertRaises(ValueError):
            DigitalHumanService._invoke_llm_streaming([], llm)


class _ProseChunk:
    content = "试用期最长不能超过6个月，具体要看劳动合同期限。"


class _ProseLlm:
    @staticmethod
    def stream(_messages):
        yield _ProseChunk()


class ConversationProseDegradationIntegrationTest(unittest.TestCase):
    def setUp(self):
        token = uuid.uuid4().hex
        self.client_id = f"dhc_prose_{token}"
        self.session_id = f"dh_prose_{token}"
        self.service = DigitalHumanService.__new__(DigitalHumanService)
        self.service.llm = _ProseLlm()
        self.service.system_prompt = "测试安全规则"
        self.service._orchestrator = self.service._build_orchestrator()

    def tearDown(self):
        db = SessionLocal()
        try:
            db.query(Matter).filter(
                Matter.client_id == self.client_id,
            ).delete(synchronize_session=False)
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

    def test_prose_model_answer_is_kept_with_rule_based_route(self):
        request_id = f"dhr_prose_{uuid.uuid4().hex}"
        result = self.service.chat(
            "试用期一般最长多久？",
            self.client_id,
            request_id,
            self.session_id,
        )
        # 展示模型真实回答，而不是固定兜底句。
        self.assertEqual(result["reply"], _ProseChunk.content)
        self.assertEqual(result["decision"]["route"], "labor_consultation")
        self.assertEqual(result["action"]["type"], "reply_only")

        db = SessionLocal()
        try:
            self.assertEqual(
                db.query(Matter).filter(
                    Matter.client_id == self.client_id,
                ).count(),
                0,
            )
        finally:
            db.close()

        # 历史中持久化的是模型真实回答，固定兜底句不会进入会话历史。
        messages = DigitalHumanService.get_messages(
            self.session_id,
            self.client_id,
        )
        assistant = [item for item in messages if item["role"] == "assistant"]
        self.assertTrue(assistant)
        self.assertEqual(assistant[-1]["content"], _ProseChunk.content)


if __name__ == "__main__":
    unittest.main()
