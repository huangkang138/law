"""TTS Provider 实现目录。

接入新供应商时在此实现 TtsProvider 子类并调用 register_provider() 注册，
再通过环境变量 TTS_PROVIDER=<name> 启用。当前已接入：
- qwen：阿里云百炼 DashScope（需 DASHSCOPE_API_KEY；一次性合成接口）。
"""

from ..tts_provider import register_provider
from .qwen_provider import QwenDashScopeTtsProvider

register_provider(QwenDashScopeTtsProvider())
