"""
核心配置模块
"""

import os
from typing import Literal, Optional
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """应用配置类"""
    
    # 应用基础配置
    APP_NAME: str = "YYS-Law"
    APP_VERSION: str = "2.0.0"
    DEBUG: bool = False
    LOG_LEVEL: str = "INFO"
    
    # LLM 模式配置（仅支持云端模式）
    LLM_MODE: Literal["cloud"] = "cloud"
    
    # 云端模式配置（DeepSeek API）
    OPENAI_API_KEY: Optional[str] = None
    OPENAI_BASE_URL: str = "https://api.deepseek.com/v1"
    OPENAI_MODEL: str = "deepseek-chat"
    OPENAI_TEMPERATURE: float = 0.3
    OPENAI_MAX_TOKENS: int = 2048

    # 语音 TTS 配置（数字人语音 Phase 1；密钥只从环境读取，禁止硬编码）
    DASHSCOPE_API_KEY: Optional[str] = None
    DASHSCOPE_WORKSPACE_ID: Optional[str] = None
    TTS_PROVIDER: Optional[str] = None
    TTS_MODEL: str = "qwen-audio-3.0-tts-flash"
    TTS_VOICE: str = "longanhuan_v3.6"
    TTS_FORMAT: str = "mp3"
    TTS_SAMPLE_RATE: int = 22050
    TTS_RATE: float = 1.0
    TTS_VOLUME: int = 50
    # 可选：自定义 DashScope WebSocket 地址；默认走 SDK 全局地址
    TTS_WS_URL: Optional[str] = None
    
    # Agent 配置
    AGENT_MAX_ITERATIONS: int = 5
    AGENT_VERBOSE: bool = True
    
    # 工具配置
    ENABLE_WEB_SEARCH: bool = True
    ENABLE_CALCULATOR: bool = False
    
    # 法律辖区配置
    DEFAULT_JURISDICTION: str = "中国"
    
    # API 配置
    API_PREFIX: str = "/api"
    CORS_ORIGINS: list[str] = [
        "http://localhost:3000",
        "http://127.0.0.1:3000",
        "http://localhost:3001",
        "http://127.0.0.1:3001",
        "http://localhost:3002",
        "http://127.0.0.1:3002",
        
    ]
    
    # 日志配置
    LOG_FILE: str = "logs/app.log"
    LOG_ROTATION: str = "500 MB"
    LOG_RETENTION: str = "10 days"

    # 数据库配置。生产环境必须通过环境变量提供凭据，源码不保存密码。
    DATABASE_URL: str = "postgresql://postgres@localhost:5432/sparklaw"
    AUTO_CREATE_DB_TABLES: bool = False
    
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=True,
        extra="ignore"
    )
    
    def get_llm_config(self) -> dict:
        """获取当前 LLM 配置（仅支持云端 DeepSeek 模式）"""
        return {
            "mode": "cloud",
            "api_key": self.OPENAI_API_KEY,
            "base_url": self.OPENAI_BASE_URL,
            "model": self.OPENAI_MODEL,
            "temperature": self.OPENAI_TEMPERATURE,
            "max_tokens": self.OPENAI_MAX_TOKENS,
        }


# 创建全局配置实例
settings = Settings()
