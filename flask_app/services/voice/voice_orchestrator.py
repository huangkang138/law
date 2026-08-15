"""句级语音编排：句缓冲 → 归一化 → TTS → 有序音频事件。

按 request_id 维护独立缓冲与序号；取消后该请求不再产出任何事件，
并同步取消仍在进行的供应商合成。TTS 失败只影响语音（fallback），
不影响聊天、Agent 或工作台。
"""

import base64
import threading
from dataclasses import dataclass
from typing import Dict, List, Optional

from core.logger import app_logger

from .sentence_segmenter import SentenceSegmenter
from .speech_text_normalizer import SpeechTextNormalizer
from .tts_provider import TtsProvider
from .voice_profile import VoiceProfile

TTsMode = str  # "primary" | "fallback"


@dataclass(frozen=True)
class VoiceChunk:
    """一条可播放语音片段（对应一个完整句）。"""

    seq: int
    request_id: str
    text: str
    tts_mode: TTsMode
    audio_b64: Optional[str] = None
    mime_type: str = "audio/mp3"


class VoiceOrchestrator:
    def __init__(
        self,
        provider: Optional[TtsProvider] = None,
        profile: Optional[VoiceProfile] = None,
        normalizer: Optional[SpeechTextNormalizer] = None,
    ) -> None:
        self.provider = provider
        self.profile = profile or VoiceProfile.from_env()
        self.normalizer = normalizer or SpeechTextNormalizer()
        self._buffers: Dict[str, SentenceSegmenter] = {}
        self._seqs: Dict[str, int] = {}
        self._cancelled: set = set()
        # Provider 已失败的请求：其余句子直接 fallback，不再反复调用/刷日志。
        self._provider_failed: set = set()
        self._lock = threading.Lock()

    @property
    def has_provider(self) -> bool:
        return self.provider is not None

    def push_text(self, request_id: str, text: str) -> List[VoiceChunk]:
        """喂入增量展示文本，返回新完成的句子对应的语音片段。"""
        if request_id in self._cancelled:
            return []
        with self._lock:
            segmenter = self._buffers.setdefault(request_id, SentenceSegmenter())
        sentences = segmenter.push(text)
        chunks = []
        for sentence in sentences:
            # 取消可发生在多句合成之间：发现即停，不继续为已取消请求合成。
            if request_id in self._cancelled:
                break
            chunk = self._synthesize(request_id, sentence)
            if chunk is not None:
                chunks.append(chunk)
        return chunks

    def finish(self, request_id: str) -> List[VoiceChunk]:
        """请求展示结束时取回无句末标点的尾部文本。"""
        if request_id in self._cancelled:
            return []
        with self._lock:
            segmenter = self._buffers.pop(request_id, None)
            self._seqs.pop(request_id, None)
        if segmenter is None:
            return []
        return [
            chunk
            for sentence in segmenter.flush()
            if (chunk := self._synthesize(request_id, sentence)) is not None
        ]

    def cancel(self, request_id: str) -> None:
        """取消该请求的语音：丢弃句缓冲与序号，并取消供应商合成。"""
        with self._lock:
            self._cancelled.add(request_id)
            self._buffers.pop(request_id, None)
            self._seqs.pop(request_id, None)
            self._provider_failed.discard(request_id)
        if self.provider is not None:
            try:
                self.provider.cancel(request_id)
            except Exception:  # 取消失败不影响主链路
                app_logger.exception("语音供应商取消失败: %s", request_id)

    def _synthesize(self, request_id: str, sentence: str) -> Optional[VoiceChunk]:
        speak_text = self.normalizer.normalize(sentence)
        if not speak_text:
            return None
        with self._lock:
            seq = self._seqs.get(request_id, 0) + 1
            self._seqs[request_id] = seq
        audio = None
        mode: TTsMode = "fallback"
        if self.provider is not None and request_id not in self._provider_failed:
            try:
                data = self.provider.synthesize(speak_text, request_id, self.profile)
                if data:
                    audio = base64.b64encode(data).decode("ascii")
                    mode = "primary"
            except Exception:
                # 神经 TTS 失败 → 该请求锁存为 fallback，聊天不受影响。
                self._provider_failed.add(request_id)
                app_logger.exception("语音合成失败，本次回复降级浏览器语音: %s", request_id)
        return VoiceChunk(
            seq=seq,
            request_id=request_id,
            text=speak_text,
            tts_mode=mode,
            audio_b64=audio,
        )
