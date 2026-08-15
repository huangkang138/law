"""TTS 供应商统一接口与注册表。

业务代码只依赖 TtsProvider 抽象，禁止直接 import 任何供应商 SDK。
当前项目未配置第三方 TTS Provider：get_active_provider() 返回 None，
语音层以 tts_mode="fallback" 明确降级（前端浏览器语音），不静默混用。

接入新 Provider 的步骤：
1. 在 provider/ 下实现 TtsProvider 子类（synthesize/cancel）；
2. 在 provider/__init__.py 注册：register_provider(实现类())；
3. 配置环境变量 TTS_PROVIDER=<注册名> 及对应密钥（仅环境变量，禁止硬编码）。
"""

from abc import ABC, abstractmethod
from typing import Dict, Optional

from core.config import settings

from .voice_profile import VoiceProfile


class TtsProvider(ABC):
    """语音合成供应商抽象。"""

    name: str = "abstract"

    @abstractmethod
    def synthesize(
        self,
        text: str,
        request_id: str,
        profile: VoiceProfile,
    ) -> Optional[bytes]:
        """合成一段完整句，返回音频 bytes；失败返回 None（上层走 fallback）。"""

    @abstractmethod
    def cancel(self, request_id: str) -> None:
        """取消该请求仍在进行的合成任务；幂等，不抛异常。"""


_registry: Dict[str, TtsProvider] = {}


def register_provider(provider: TtsProvider) -> None:
    """注册供应商实现；重名直接覆盖并保持单一事实。"""
    _registry[provider.name] = provider


def get_active_provider() -> Optional[TtsProvider]:
    """按 TTS_PROVIDER 环境变量返回当前启用的供应商；未配置返回 None（fallback）。"""
    name = (settings.TTS_PROVIDER or "").strip()
    if not name:
        return None
    return _registry.get(name)
