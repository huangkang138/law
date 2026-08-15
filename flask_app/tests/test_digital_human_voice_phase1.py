"""数字人语音 Phase 1：后端句级语音层 + SSE voice 事件 + 前端播放器守卫。

链路：展示文本 → 句级切分 → 朗读归一化 → TTS（供应商抽象，当前未接入，
明确 fallback）→ SSE voice 事件 → 前端队列连续播放；按 requestId 隔离与取消。
本阶段不做：ASR、口型、动画；不修改聊天/Agent 逻辑。
"""

import base64
import json
import sys
import types
import unittest
import uuid
from pathlib import Path
from unittest.mock import patch

from core.config import settings
from core.database import SessionLocal
from models.db_models import (
    ConversationWorkspaceState,
    DigitalHumanRequest,
    DigitalHumanSession,
    Matter,
)

from services.digital_human_service import DigitalHumanService
from services.conversation.cancel import disarm, set_cancelled
from services.conversation.sse import (
    EVENT_COMPLETED,
    EVENT_DELTA,
    EVENT_ERROR,
    EVENT_VOICE,
)
from services.voice import (
    SentenceSegmenter,
    SpeechTextNormalizer,
    TtsProvider,
    VoiceOrchestrator,
    VoiceProfile,
)

ROOT = Path(__file__).resolve().parents[2]
FRONTEND = ROOT / "frontend" / "src"


def _read(rel):
    return (FRONTEND / rel).read_text(encoding="utf-8")


def _parse_sse_event(event_text):
    name = ""
    data = None
    for line in event_text.split("\n"):
        if line.startswith("event:"):
            name = line[len("event:"):].strip()
        elif line.startswith("data:"):
            data = json.loads(line[len("data:"):].lstrip())
    return name, data


class _FastJsonChunk:
    content = json.dumps({
        "reply": "依据《劳动合同法》第 30 条，你可以要求公司支付 12,500 元工资。"
                 "这是第二句！你还可以向劳动监察大队投诉；最后请保留证据。",
        "intent": "legal_chat",
        "conversation_route": "labor_consultation",
        "emotion": "serious",
        "confidence": 0.9,
    }, ensure_ascii=False)


class _FastJsonLlm:
    @staticmethod
    def stream(_messages):
        yield _FastJsonChunk()


class SpeechTextNormalizerTest(unittest.TestCase):
    def test_markdown_symbols_removed(self):
        text = "## 重点\n- 第一点\n**加粗** 内容 `代码` 结尾"
        result = SpeechTextNormalizer.normalize(text)
        self.assertNotIn("#", result)
        self.assertNotIn("*", result)
        self.assertNotIn("`", result)
        self.assertIn("第一点", result)

    def test_url_replaced_with_link_word(self):
        text = "详见 https://www.example.com/rule/1 说明"
        result = SpeechTextNormalizer.normalize(text)
        self.assertNotIn("http", result)
        self.assertIn("链接", result)

    def test_brackets_removed_content_kept(self):
        result = SpeechTextNormalizer.normalize("（如有）争议【可以】申请仲裁。")
        self.assertNotIn("（", result)
        self.assertNotIn("）", result)
        self.assertNotIn("【", result)
        self.assertIn("如有", result)
        self.assertIn("可以", result)

    def test_amounts_and_percent_readable(self):
        result = SpeechTextNormalizer.normalize("支付 12,500 元，涨幅 30%。")
        self.assertIn("12500", result)
        self.assertNotIn("12,500", result)
        self.assertIn("百分之30", result)
        self.assertNotIn("30%", result)

    def test_legal_citations_and_dates_kept(self):
        text = "依据《劳动合同法》第 30 条，2026 年 8 月 15 日生效。"
        result = SpeechTextNormalizer.normalize(text)
        self.assertIn("《劳动合同法》", result)
        self.assertIn("第 30 条", result)
        self.assertIn("2026 年 8 月 15 日", result)

    def test_only_form_changes_meaning_kept(self):
        # 归一化只改变朗读形式：核心法律表述必须逐字保留。
        text = "你可以要求公司支付工资。"
        result = SpeechTextNormalizer.normalize(text)
        self.assertIn("要求公司支付工资", result)


class SentenceSegmenterTest(unittest.TestCase):
    def test_split_on_sentence_enders(self):
        segmenter = SentenceSegmenter()
        sentences = segmenter.push("第一句。第二句！第三句？第四句；")
        self.assertEqual(sentences, ["第一句。", "第二句！", "第三句？", "第四句；"])

    def test_short_fragments_buffered_until_sentence(self):
        # 碎片级文本不得单独成句（避免"根据""你的"级 TTS）。
        segmenter = SentenceSegmenter()
        self.assertEqual(segmenter.push("根据"), [])
        self.assertEqual(segmenter.push("你的"), [])
        self.assertEqual(segmenter.push("情况。"), ["根据你的情况。"])

    def test_long_text_without_ender_flushed_at_limit(self):
        segmenter = SentenceSegmenter(max_chars=10)
        sentences = segmenter.push("一二三四五六七八九十十一")
        self.assertEqual(len(sentences), 1)
        self.assertEqual(len(sentences[0]), 10)

    def test_flush_returns_tail(self):
        segmenter = SentenceSegmenter()
        segmenter.push("完整句。")
        self.assertEqual(segmenter.push("没有标点的尾巴"), [])
        self.assertEqual(segmenter.flush(), ["没有标点的尾巴"])


class _FakeProvider(TtsProvider):
    name = "fake"

    def __init__(self, fail=False):
        self.fail = fail
        self.synthesized = []
        self.cancelled = []

    def synthesize(self, text, request_id, profile):
        if self.fail:
            raise RuntimeError("模拟供应商故障")
        self.synthesized.append((text, request_id))
        return ("audio-" + text).encode("utf-8")

    def cancel(self, request_id):
        self.cancelled.append(request_id)


class VoiceOrchestratorTest(unittest.TestCase):
    def test_fallback_mode_without_provider(self):
        orchestrator = VoiceOrchestrator(provider=None)
        chunks = orchestrator.push_text("dhr_v1", "第一句。")
        self.assertEqual(len(chunks), 1)
        chunk = chunks[0]
        self.assertEqual(chunk.tts_mode, "fallback")
        self.assertIsNone(chunk.audio_b64)
        self.assertEqual(chunk.seq, 1)

    def test_primary_mode_with_provider(self):
        provider = _FakeProvider()
        orchestrator = VoiceOrchestrator(provider=provider, profile=VoiceProfile())
        chunks = orchestrator.push_text("dhr_v2", "第一句。第二句。")
        self.assertEqual([c.seq for c in chunks], [1, 2])
        for chunk in chunks:
            self.assertEqual(chunk.tts_mode, "primary")
            self.assertTrue(chunk.audio_b64)
            self.assertEqual(
                base64.b64decode(chunk.audio_b64).decode("utf-8"),
                "audio-" + chunk.text,
            )

    def test_provider_failure_degrades_to_fallback(self):
        orchestrator = VoiceOrchestrator(provider=_FakeProvider(fail=True))
        chunks = orchestrator.push_text("dhr_v3", "第一句。")
        self.assertEqual(chunks[0].tts_mode, "fallback")
        self.assertIsNone(chunks[0].audio_b64)

    def test_cancel_drops_buffer_and_cancels_provider(self):
        provider = _FakeProvider()
        orchestrator = VoiceOrchestrator(provider=provider)
        self.assertEqual(len(orchestrator.push_text("dhr_v4", "第一句。")), 1)
        orchestrator.cancel("dhr_v4")
        # 取消后：迟到文本不再产出，finish 为空，供应商收到 cancel。
        self.assertEqual(orchestrator.push_text("dhr_v4", "第二句。"), [])
        self.assertEqual(orchestrator.finish("dhr_v4"), [])
        self.assertEqual(provider.cancelled, ["dhr_v4"])

    def test_requests_isolated_by_request_id(self):
        orchestrator = VoiceOrchestrator(provider=_FakeProvider())
        first = orchestrator.push_text("dhr_a", "甲句。")
        second = orchestrator.push_text("dhr_b", "乙句。")
        self.assertEqual(first[0].request_id, "dhr_a")
        self.assertEqual(second[0].request_id, "dhr_b")
        self.assertEqual(second[0].seq, 1)  # 序号按请求独立


class VoiceStreamPresentationTest(unittest.TestCase):
    """chat_stream 的句级 voice 事件与取消（服务层可执行验证）。"""

    def setUp(self):
        token = uuid.uuid4().hex
        self.client_id = f"dhc_voice_{token}"
        self.session_id = f"dh_voice_{token}"
        self.service = DigitalHumanService.__new__(DigitalHumanService)
        self.service.system_prompt = "测试安全规则"
        self.service.llm = _FastJsonLlm()
        self.service._orchestrator = self.service._build_orchestrator()
        self.service._voice_orchestrator = VoiceOrchestrator(provider=None)

    def tearDown(self):
        # 与 3.7F 取消测试一致：清理本用例产生的行，保证可重复运行。
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

    def test_voice_events_sentence_ordered_and_fallback_marked(self):
        request_id = f"dhr_voice_{uuid.uuid4().hex}"
        events = [
            _parse_sse_event(event_text)
            for event_text in self.service.chat_stream(
                "普通问题", self.client_id, request_id,
                self.session_id, chunk_delay=0, voice=True,
            )
        ]
        names = [name for name, _ in events]
        self.assertEqual(names[0], "status")
        self.assertIn(EVENT_DELTA, names)
        self.assertIn(EVENT_COMPLETED, names)
        voice_events = [data for name, data in events if name == EVENT_VOICE]
        self.assertGreaterEqual(len(voice_events), 2, "应至少产出两个句子")
        self.assertEqual(
            [data["seq"] for data in voice_events],
            list(range(1, len(voice_events) + 1)),
            "seq 必须按句递增",
        )
        for data in voice_events:
            self.assertEqual(data["tts_mode"], "fallback")
            self.assertIsNone(data["audio_b64"])
            self.assertEqual(data["request_id"], request_id)

    def test_no_voice_events_without_voice_flag(self):
        request_id = f"dhr_voice_{uuid.uuid4().hex}"
        events = [
            _parse_sse_event(event_text)
            for event_text in self.service.chat_stream(
                "普通问题", self.client_id, request_id,
                self.session_id, chunk_delay=0,
            )
        ]
        self.assertNotIn(EVENT_VOICE, [name for name, _ in events])

    def test_cancel_during_presentation_stops_voice_events(self):
        # 取消信号到达后，呈现循环立即以 CANCELLED 收尾，不再下发 voice 事件。
        request_id = f"dhr_voice_{uuid.uuid4().hex}"
        set_cancelled(request_id)
        try:
            events = [
                _parse_sse_event(event_text)
                for event_text in self.service._stream_voice_presentation(
                    "第一句。第二句。", request_id, chunk_delay=0,
                )
            ]
        finally:
            disarm(request_id)
        self.assertNotIn(EVENT_VOICE, [name for name, _ in events])
        self.assertNotIn(EVENT_DELTA, [name for name, _ in events])
        self.assertEqual(events[-1][0], EVENT_ERROR)
        self.assertEqual(events[-1][1]["code"], "CANCELLED")

    def test_cancel_request_clears_voice_orchestrator(self):
        # cancel_request 必须联动语音编排器（句缓冲丢弃 + 供应商取消）。
        request_id = f"dhr_voice_{uuid.uuid4().hex}"
        self.service._voice_orchestrator.push_text(request_id, "第一句。")
        self.service._voice_orchestrator.cancel(request_id)
        self.assertEqual(
            self.service._voice_orchestrator.push_text(request_id, "第二句。"),
            [],
        )


class _FakeSynthesizer:
    calls = []

    def __init__(self, **kwargs):
        self.kwargs = kwargs

    def call(self, text):
        _FakeSynthesizer.calls.append((text, self.kwargs))
        return b"audio-bytes"


def _fake_dashscope_modules():
    fake_dashscope = types.ModuleType("dashscope")
    fake_audio = types.ModuleType("dashscope.audio")
    fake_tts_v2 = types.ModuleType("dashscope.audio.tts_v2")
    fake_tts_v2.SpeechSynthesizer = _FakeSynthesizer
    fake_audio.tts_v2 = fake_tts_v2
    fake_dashscope.audio = fake_audio

    class _FakeAudioFormatMember:
        value = ("mp3", 22050)

    class _FakeAudioFormat:
        DEFAULT = _FakeAudioFormatMember()
        __members__ = {"MP3_22050HZ_MONO_256KBPS": _FakeAudioFormatMember()}

    fake_speech_synthesizer = types.ModuleType("dashscope.audio.tts_v2.speech_synthesizer")
    fake_speech_synthesizer.AudioFormat = _FakeAudioFormat
    fake_tts_v2.speech_synthesizer = fake_speech_synthesizer
    return {
        "dashscope": fake_dashscope,
        "dashscope.audio": fake_audio,
        "dashscope.audio.tts_v2": fake_tts_v2,
        "dashscope.audio.tts_v2.speech_synthesizer": fake_speech_synthesizer,
    }


class QwenProviderTest(unittest.TestCase):
    """Qwen DashScope Provider（WebSocket SDK 语义）：参数映射、失败抛出、迟到丢弃。"""

    def setUp(self):
        _FakeSynthesizer.calls = []

    def test_synthesize_returns_audio_and_maps_parameters(self):
        from services.voice.provider.qwen_provider import QwenDashScopeTtsProvider

        provider = QwenDashScopeTtsProvider()
        with patch.object(settings, "DASHSCOPE_API_KEY", "sk-test"):
            with patch.dict(sys.modules, _fake_dashscope_modules()):
                data = provider.synthesize("你好。", "dhr_qwen_1", VoiceProfile())
        self.assertEqual(data, b"audio-bytes")
        _, kwargs = _FakeSynthesizer.calls[0]
        self.assertEqual(kwargs["model"], settings.TTS_MODEL)
        self.assertEqual(kwargs["voice"], settings.TTS_VOICE)
        # format 映射为 SDK 的 AudioFormat 枚举（按 TTS_FORMAT + TTS_SAMPLE_RATE）。
        self.assertIsNotNone(kwargs["format"])
        self.assertEqual(kwargs["volume"], settings.TTS_VOLUME)
        # 该协议语速参数名是 speech_rate，不是 rate。
        self.assertIn("speech_rate", kwargs)

    def test_missing_api_key_raises_before_sdk_call(self):
        from services.voice.provider.qwen_provider import QwenDashScopeTtsProvider

        provider = QwenDashScopeTtsProvider()
        with patch.object(settings, "DASHSCOPE_API_KEY", None):
            with self.assertRaises(RuntimeError):
                provider.synthesize("你好。", "dhr_qwen_2", VoiceProfile())
        self.assertEqual(_FakeSynthesizer.calls, [])

    def test_empty_audio_raises(self):
        from services.voice.provider.qwen_provider import QwenDashScopeTtsProvider

        class _EmptySynthesizer(_FakeSynthesizer):
            def call(self, text):
                return b""

        fake = _fake_dashscope_modules()
        fake["dashscope.audio.tts_v2"].SpeechSynthesizer = _EmptySynthesizer
        provider = QwenDashScopeTtsProvider()
        with patch.object(settings, "DASHSCOPE_API_KEY", "sk-test"):
            with patch.dict(sys.modules, fake):
                with self.assertRaises(RuntimeError):
                    provider.synthesize("你好。", "dhr_qwen_3", VoiceProfile())

    def test_cancelled_request_discards_result(self):
        from services.voice.provider.qwen_provider import QwenDashScopeTtsProvider

        provider = QwenDashScopeTtsProvider()
        provider.cancel("dhr_qwen_4")
        with patch.object(settings, "DASHSCOPE_API_KEY", "sk-test"):
            data = provider.synthesize("你好。", "dhr_qwen_4", VoiceProfile())
        self.assertIsNone(data, "取消后的迟到合成结果必须丢弃")
        self.assertEqual(_FakeSynthesizer.calls, [], "已取消请求不应再发起合成")

    def test_registry_activation_by_env_name(self):
        from services.voice import get_active_provider
        from services.voice.provider.qwen_provider import QwenDashScopeTtsProvider

        with patch.object(settings, "TTS_PROVIDER", "qwen"):
            provider = get_active_provider()
            self.assertIsInstance(provider, QwenDashScopeTtsProvider)
        with patch.object(settings, "TTS_PROVIDER", None):
            self.assertIsNone(get_active_provider())

    def test_orchestrator_latches_fallback_after_provider_failure(self):
        # Provider 失败一次后，该请求其余句子直接 fallback，不再调用供应商。
        provider = _FakeProvider(fail=True)
        orchestrator = VoiceOrchestrator(provider=provider)
        chunks = orchestrator.push_text("dhr_qwen_5", "第一句。第二句。")
        self.assertEqual([c.tts_mode for c in chunks], ["fallback", "fallback"])
        self.assertEqual(len(provider.synthesized), 0)

    def test_cancel_stops_synthesizing_remaining_sentences(self):
        # 多句之间取消：后续句子不再合成。
        class _CancelAfterFirst(_FakeProvider):
            def synthesize(self, text, request_id, profile):
                result = super().synthesize(text, request_id, profile)
                self.owner.cancel(request_id)
                return result

        provider = _CancelAfterFirst()
        orchestrator = VoiceOrchestrator(provider=provider)
        provider.owner = orchestrator
        chunks = orchestrator.push_text("dhr_qwen_6", "第一句。第二句。")
        self.assertEqual([c.seq for c in chunks], [1])


class FrontendVoicePhase1GuardTest(unittest.TestCase):
    """前端播放器与集成点的源码守卫（浏览器行为由人工验收覆盖）。"""

    def setUp(self):
        self.player = _read("lib/voice/streamingAudioPlayer.ts")
        self.api = _read("services/digitalHumanApi.ts")
        self.store = _read("store/digitalHumanStore.ts")

    def test_player_queue_contract(self):
        for fragment in (
            "enqueue(chunk: VoiceChunk)",
            "pause(): void",
            "resume(): void",
            "stop(): void",
            "clear(): void",
            "destroy(): void",
            "private playNext(): void",
        ):
            self.assertIn(fragment, self.player, f"播放器缺少: {fragment}")

    def test_player_state_machine(self):
        for state in ("IDLE", "BUFFERING", "PLAYING", "PAUSED", "STOPPED", "ERROR"):
            self.assertIn(state, self.player, f"缺少状态: {state}")

    def test_player_request_id_isolation(self):
        # 迟到旧请求片段直接丢弃，不得进入新队列。
        self.assertIn("chunk.requestId !== this.requestId", self.player)
        self.assertIn("setRequest(requestId: string)", self.player)

    def test_player_error_skips_chunk_not_stuck(self):
        # 异常片段跳过继续下一条，不卡死队列。
        self.assertIn("handleChunkError", self.player)
        self.assertIn("this.playNext();", self.player)

    def test_api_sends_voice_flag_and_parses_voice_event(self):
        self.assertIn("question, request_id: requestId, voice,", self.api)
        self.assertIn("parsed.event === 'voice'", self.api)
        self.assertIn("data:${mimeType};base64,", self.api)

    def test_store_voice_guard_and_cancel_chain(self):
        # 发送时切换播放器作用域；voice 事件双重守卫（发送时 + 当前开关）。
        self.assertIn("voicePlayer.setRequest(requestId);", self.store)
        self.assertIn("if (!voiceRequested || !get().voiceEnabled) return;", self.store)
        self.assertIn("voicePlayer.enqueue({", self.store)
        # 停止生成：取消 LLM + 清空音频队列。
        self.assertIn("voicePlayer.clear();", self.store)


if __name__ == "__main__":
    unittest.main()
