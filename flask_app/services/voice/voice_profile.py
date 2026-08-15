"""法小助固定语音配置。

配置只从环境变量读取（VOICE_PROFILE_JSON），禁止把 API_KEY、SECRET、
VOICE_ID 硬编码进代码或前端。
"""

import json
import os
from dataclasses import dataclass


@dataclass(frozen=True)
class VoiceProfile:
    """一次语音合成使用的发声配置；Provider 不支持的字段自行忽略。"""

    voice_id: str = "faxiaozhu"
    speed: float = 1.0
    volume: float = 1.0
    style: str = "chat"

    @staticmethod
    def from_env() -> "VoiceProfile":
        raw = os.environ.get("VOICE_PROFILE_JSON", "")
        if not raw:
            return VoiceProfile()
        try:
            data = json.loads(raw)
            if not isinstance(data, dict):
                return VoiceProfile()
            return VoiceProfile(
                voice_id=str(data.get("voice_id", "faxiaozhu")),
                speed=float(data.get("speed", 1.0)),
                volume=float(data.get("volume", 1.0)),
                style=str(data.get("style", "chat")),
            )
        except (json.JSONDecodeError, TypeError, ValueError):
            # 配置损坏时回退默认档，不让语音配置拖垮聊天。
            return VoiceProfile()
