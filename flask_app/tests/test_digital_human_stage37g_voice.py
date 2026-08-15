"""阶段3.7G：基础语音闭环前端源码守卫测试。

3.7G 是纯前端语音闭环（浏览器 STT/TTS 作为同一 Conversation Orchestrator
的输入输出方式），后端零改动。本套测试按项目惯例以源码守卫方式验证：
控制器降级守卫与打断语义、Store 集成点、Composer 与气泡 UI 入口、
Avatar speaking 状态映射与 Float 样式追加（只增不改）。
"""

import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
FRONTEND = ROOT / "frontend" / "src"


def _read(rel):
    return (FRONTEND / rel).read_text(encoding="utf-8")


def _slice_of(source, start_marker, end_marker):
    start = source.find(start_marker)
    self_assert = start >= 0
    assert self_assert, f"未找到标记: {start_marker}"
    end = source.find(end_marker, start) if end_marker else len(source)
    assert end > start, f"未找到结束标记: {end_marker}"
    return source[start:end]


class VoiceControllersTest(unittest.TestCase):
    """STT/TTS 独立控制器：降级、参数、打断与清洗语义。"""

    def setUp(self):
        self.tts = _read("lib/voice/ttsController.ts")
        self.stt = _read("lib/voice/sttController.ts")

    def test_controller_files_exist(self):
        self.assertTrue(self.tts.strip(), "ttsController.ts 为空")
        self.assertTrue(self.stt.strip(), "sttController.ts 为空")

    def test_ssr_guards(self):
        # 两个控制器都必须在 window 不存在时直接降级（Next.js SSR 安全）。
        for name, source in (("tts", self.tts), ("stt", self.stt)):
            self.assertIn(
                "typeof window === 'undefined'", source,
                f"{name} 控制器缺少 SSR 守卫",
            )

    def test_stt_continuous_chinese_params(self):
        self.assertIn("recognition.continuous = true;", self.stt)
        self.assertIn("recognition.interimResults = true;", self.stt)
        self.assertIn("recognition.lang = 'zh-CN';", self.stt)
        self.assertIn("recognition.maxAlternatives = 1;", self.stt)

    def test_stt_auto_restart_on_end(self):
        # Chrome 连续识别约 60s 自动结束，onend 时仍在录音则自动重启。
        self.assertIn("recognition.onend", self.stt)
        self.assertGreaterEqual(
            self.stt.count("recognition.start();"), 2,
            "onend 自动重启（第二次 start）缺失",
        )
        self.assertIn("this.recording &&", self.stt)

    def test_stt_error_degradation(self):
        # 主动停止/未检测到语音静默返回；权限与网络错误给出轻量提示。
        self.assertIn("'aborted' || error === 'no-speech'", self.stt)
        self.assertIn("未获得麦克风权限", self.stt)
        self.assertIn("语音识别暂不可用", self.stt)

    def test_stt_final_dedupe_and_interim_clear(self):
        # 停止录音时 Chrome 会重放已确认的最终结果：按结果下标去重，
        # 同一段话只上报一次（防"我要仲裁我要仲裁"式重复）。
        self.assertIn("lastFinalIndex", self.stt, "缺少最终结果去重游标")
        self.assertIn("i <= this.lastFinalIndex", self.stt, "缺少已处理下标跳过")
        self.assertIn(
            "this.callbacks.onInterim(interim);", self.stt,
            "中间结果必须无条件上报（空值清空预览），否则停止时会重复并入",
        )
        # 开始识别与 60s 自动重启（新识别会话）时游标必须复位。
        self.assertGreaterEqual(
            self.stt.count("this.lastFinalIndex = -1;"), 2,
            "开始/重启时未复位去重游标",
        )

    def test_tts_speak_cancels_previous_first(self):
        # 新朗读先取消旧朗读（打断语义）。
        speak_body = _slice_of(self.tts, "speak(text: string", "cancel(): void")
        cancel_at = speak_body.find("window.speechSynthesis.cancel();")
        speak_at = speak_body.find("window.speechSynthesis.speak(utterance);")
        self.assertGreaterEqual(cancel_at, 0, "speak 缺少先 cancel")
        self.assertGreaterEqual(speak_at, 0, "speak 缺少 speak 调用")
        self.assertLess(cancel_at, speak_at, "cancel 必须先于 speak")

    def test_filter_speakable_text_rules(self):
        # 朗读文本清洗：注释块、Markdown 符号、emoji、多余空白。
        for fragment in (
            ".replace(/【[^】]*】/g, '')",
            ".replace(/\\[[^\\]]*\\]/g, '')",
            ".replace(/[*+#@]/g, '')",
            ".replace(/[•·]/g, '')",
            "\\uD83C",
            ".replace(/\\s+/g, ' ')",
        ):
            self.assertIn(fragment, self.tts, f"filterSpeakableText 缺少规则: {fragment}")

    def test_chinese_voice_preference(self):
        self.assertIn("lang.toLowerCase().includes('zh')", self.tts)
        for keyword in ("xiaoxiao", "xiaoyi", "huihui", "xia"):
            self.assertIn(keyword, self.tts, f"中文女声关键词缺失: {keyword}")
        self.assertIn("return zh[0];", self.tts)


class StoreVoiceIntegrationTest(unittest.TestCase):
    """Store 语音状态与动作、TTS 取消集成点。"""

    def setUp(self):
        self.store = _read("store/digitalHumanStore.ts")

    def test_voice_state_fields_declared(self):
        self.assertIn("voiceEnabled: boolean;", self.store)
        self.assertIn("voiceSpeaking: boolean;", self.store)
        self.assertIn("speakingMessageId: string | null;", self.store)

    def test_voice_state_initial_values(self):
        self.assertIn("voiceEnabled: false,", self.store)
        self.assertIn("voiceSpeaking: false,", self.store)
        self.assertIn("speakingMessageId: null,", self.store)

    def test_partialize_persists_voice_enabled(self):
        # 用户偏好持久化；朗读瞬时状态不持久化。
        partialize = _slice_of(self.store, "partialize: (state) => ({", "}),")
        self.assertIn("voiceEnabled: state.voiceEnabled", partialize)
        self.assertNotIn("voiceSpeaking: state.voiceSpeaking", partialize)

    def test_send_message_starts_by_cancelling_tts(self):
        # 新输入（语音与键盘一致）打断旧朗读。
        body = _slice_of(self.store, "sendMessage: async", "reset: async")
        cancel_at = body.find("ttsController.cancel();")
        stream_at = body.find("sendDigitalHumanMessageStream(")
        self.assertGreaterEqual(cancel_at, 0, "sendMessage 开头缺少 tts cancel")
        self.assertGreaterEqual(stream_at, 0)
        self.assertLess(cancel_at, stream_at, "cancel 必须先于发起请求")

    def test_success_path_speaks_only_when_enabled(self):
        # Phase 1 起朗读走句级 voice 事件（不再整条 reply 朗读）：
        # onVoice 只按发送时与当前开关双重守卫入队，且位于成功路径。
        body = _slice_of(self.store, "sendMessage: async", "reset: async")
        self.assertIn("onVoice: (payload) => {", body)
        self.assertIn("if (!voiceRequested || !get().voiceEnabled) return;", body)
        self.assertIn("voicePlayer.enqueue({", body)
        self.assertLess(
            body.find("onVoice: (payload) => {"),
            body.find("} catch (error) {"),
            "voice 入队必须位于成功路径",
        )

    def test_cancel_request_stops_tts(self):
        body = _slice_of(self.store, "cancelRequest: () => {", "toggleVoice: () => {")
        self.assertIn("ttsController.cancel();", body, "停止按钮未取消 TTS")
        self.assertIn("voiceSpeaking: false,", body)
        self.assertIn("speakingMessageId: null,", body)

    def test_lifecycle_actions_stop_tts(self):
        # 关闭/切会话/新对话/重置/删除当前会话都必须停止旧朗读。
        for marker, end in (
            ("close: () => {", "toggle: () => {"),
            ("loadSession: async (sessionId) => {", "refreshWorkspace: async"),
            ("startNewConversation: () => {", "cancelRequest: () => {"),
            ("reset: async () => {", "loadSessions: async () => {"),
            ("deleteSession: async (sessionId) => {", "refreshHistory: async () => {"),
        ):
            body = _slice_of(self.store, marker, end)
            has_cancel = (
                "ttsController.cancel();" in body or "get().stopSpeaking();" in body
            )
            self.assertTrue(has_cancel, f"{marker.strip()} 未停止旧朗读")

    def test_toggle_voice_stops_when_disabling(self):
        body = _slice_of(self.store, "toggleVoice: () => {", "speakMessage:")
        self.assertIn("if (!enabled) get().stopSpeaking();", body)

    def test_speak_message_toggle_and_guard(self):
        body = _slice_of(self.store, "speakMessage: (messageId, content) => {", "stopSpeaking:")
        self.assertIn("get().stopSpeaking();", body, "同气泡再点 = 停止朗读")
        self.assertIn("get().speakingMessageId === messageId", body,
                      "onEnd 必须按 messageId 守卫，避免清掉新朗读状态")


class ComposerVoiceUiTest(unittest.TestCase):
    """Composer 麦克风与播报开关：守卫、打断与转写确认。"""

    def setUp(self):
        self.composer = _read("components/DigitalHuman/ConversationComposer.tsx")

    def test_hydration_guard(self):
        # 语音能力水合后判定，SSR 首帧按不支持渲染。
        self.assertIn("useVoiceReady()", self.composer)

    def test_mic_button_guarded_by_support(self):
        self.assertIn("dh-mic-button", self.composer)
        self.assertIn("sttSupported && (", self.composer, "麦克风按钮缺少支持守卫")

    def test_voice_toggle_button_guarded_by_support(self):
        self.assertIn("dh-voice-toggle", self.composer)
        self.assertIn("ttsSupported && (", self.composer, "播报开关缺少支持守卫")

    def test_stt_start_stops_tts_first(self):
        # 说话打断旧朗读。
        body = _slice_of(self.composer, "const startStt = () => {", "const toggleStt")
        self.assertIn("stopSpeaking();", body)
        stop_at = body.find("stopSpeaking();")
        controller_at = body.find("new SttController()")
        self.assertLess(stop_at, controller_at, "先停朗读再开始识别")

    def test_finish_stt_merges_interim(self):
        # 停止时并入最后一段中间结果，已确认文本不丢。
        body = _slice_of(self.composer, "const finishStt = (): string => {", "const startStt")
        self.assertIn("sttBaseRef.current + sttInterimRef.current", body)

    def test_submit_finalizes_stt_first(self):
        # 识别中点击发送：先停识别、并入已确认文本，转写文本须用户确认。
        body = _slice_of(self.composer, "const submit = async", "const handleKeyDown")
        self.assertIn("sttActive ? finishStt() : question", body)

    def test_stt_error_hint_rendered(self):
        self.assertIn("dh-stt-error-hint", self.composer)


class BubbleAndAvatarTest(unittest.TestCase):
    """气泡朗读按钮与 Avatar speaking 状态映射。"""

    def test_chat_speak_button_on_assistant(self):
        chat = _read("components/DigitalHuman/DigitalHumanChat.tsx")
        self.assertIn("dh-speak-button", chat)
        self.assertIn("speakMessage(message.id, message.content)", chat)
        self.assertIn("speakingMessageId === message.id", chat, "停止态切换缺失")

    def test_chat_avatar_talk_normal_mapping(self):
        chat = _read("components/DigitalHuman/DigitalHumanChat.tsx")
        self.assertIn("voiceSpeaking ? 'talk_normal' : emotion", chat)

    def test_companion_speak_button_skips_streaming(self):
        companion = _read("components/DigitalHuman/DigitalHumanCompanion.tsx")
        self.assertIn("dh-companion-speak", companion)
        self.assertIn("streamingMessage?.id !== message.id", companion,
                      "流式临时消息不得显示朗读按钮")

    def test_companion_avatar_talk_normal_mapping(self):
        companion = _read("components/DigitalHuman/DigitalHumanCompanion.tsx")
        self.assertIn("voiceSpeaking ? 'talk_normal' : emotion", companion)


class FloatStyleAppendTest(unittest.TestCase):
    """Float styled-jsx：只追加语音 class，不改动既有 class。"""

    def setUp(self):
        self.float = _read("components/DigitalHuman/DigitalHumanFloat.tsx")

    def test_new_voice_classes_appended(self):
        for cls in (
            ".dh-mic-button",
            ".dh-voice-toggle",
            ".dh-stt-error-hint",
            ".dh-speak-button",
            ".dh-companion-message-head",
            ".dh-companion-speak",
        ):
            self.assertIn(cls, self.float, f"缺少新增样式 class: {cls}")

    def test_existing_classes_preserved(self):
        for cls in (".dh-send-button {", ".dh-route-button {", ".dh-companion-composer {"):
            self.assertIn(cls, self.float, f"既有样式 class 被破坏: {cls}")


if __name__ == "__main__":
    unittest.main()
