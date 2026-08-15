"""Qwen DashScope 语音合成 Provider（WebSocket 协议，CosyVoice v2 同族）。

qwen-audio-3.0-tts-flash 不走 multimodal-generation HTTP 接口，而是
DashScope SDK `dashscope.audio.tts_v2.SpeechSynthesizer` 的 WebSocket 协议；
单次调用 `synthesizer.call(text)` 返回完整音频 bytes。
API 密钥与所有参数只从 settings（环境变量）读取，禁止硬编码。

取消语义：WebSocket 单次调用无法在途中断，cancel 采用"迟到结果丢弃"——
取消后 synthesize 直接返回 None，编排器不再产出该请求的任何语音片段。
"""

from typing import Optional

from core.config import settings
from core.logger import app_logger

from ..tts_provider import TtsProvider
from ..voice_profile import VoiceProfile

class QwenDashScopeTtsProvider(TtsProvider):
    """阿里云百炼（DashScope）TTS；name 与 TTS_PROVIDER 环境变量对应。"""

    name = "qwen"

    def __init__(self) -> None:
        self._cancelled: set = set()

    def synthesize(
        self,
        text: str,
        request_id: str,
        profile: VoiceProfile,
    ) -> Optional[bytes]:
        if request_id in self._cancelled:
            return None
        api_key = settings.DASHSCOPE_API_KEY
        if not api_key:
            raise RuntimeError("缺少 DASHSCOPE_API_KEY，无法调用语音合成")

        try:
            import dashscope
            from dashscope.audio.tts_v2 import SpeechSynthesizer
            from dashscope.audio.tts_v2.speech_synthesizer import AudioFormat
        except ImportError as exc:
            raise RuntimeError("缺少 dashscope SDK，请安装 requirements 中的 dashscope") from exc

        dashscope.api_key = api_key
        synthesizer = SpeechSynthesizer(
            model=settings.TTS_MODEL,
            voice=settings.TTS_VOICE or profile.voice_id,
            format=self._resolve_audio_format(),
            volume=settings.TTS_VOLUME,
            speech_rate=settings.TTS_RATE if settings.TTS_RATE is not None else profile.speed,
            url=settings.TTS_WS_URL or None,
        )
        audio = synthesizer.call(text)
        if request_id in self._cancelled:
            # 合成完成但请求已被取消：迟到结果直接丢弃。
            return None
        if not audio:
            raise RuntimeError("语音合成返回空音频")
        return audio

    def cancel(self, request_id: str) -> None:
        self._cancelled.add(request_id)

    @staticmethod
    def _resolve_audio_format():
        """把 TTS_FORMAT + TTS_SAMPLE_RATE 映射到 SDK 的 AudioFormat 枚举。"""
        from dashscope.audio.tts_v2.speech_synthesizer import AudioFormat

        target = (settings.TTS_FORMAT.lower(), settings.TTS_SAMPLE_RATE)
        for member in AudioFormat.__members__.values():
            if member.value[0] == target[0] and member.value[1] == target[1]:
                return member
        return AudioFormat.DEFAULT
