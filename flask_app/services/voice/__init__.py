"""数字人语音层：展示文本 → 句级切分 → 归一化 → TTS → 有序音频事件。

阶段 Phase 1 只覆盖"AI 回复 → 高质量 TTS → 前端连续播放"一条链路：
语音只消费最终要展示给用户的回答文本，不改变聊天、Agent 或工作台逻辑。
本层不依赖任何具体 TTS 供应商 SDK；供应商通过 TtsProvider 接口注册。
"""

from .sentence_segmenter import SentenceSegmenter
from .speech_text_normalizer import SpeechTextNormalizer
from .tts_provider import (
    TtsProvider,
    get_active_provider,
    register_provider,
)
from .voice_orchestrator import VoiceChunk, VoiceOrchestrator
from .voice_profile import VoiceProfile

# 导入即注册已接入的 Provider 实现（qwen 等），由 TTS_PROVIDER 环境变量决定启用。
from . import provider  # noqa: F401,E402

__all__ = [
    "SentenceSegmenter",
    "SpeechTextNormalizer",
    "TtsProvider",
    "VoiceChunk",
    "VoiceOrchestrator",
    "VoiceProfile",
    "get_active_provider",
    "register_provider",
]
