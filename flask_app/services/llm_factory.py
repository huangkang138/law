"""
LLM 工厂模式实现
"""

from typing import Union
from langchain_openai import ChatOpenAI
from core.config import settings
from core.logger import app_logger
import httpx


class LLMFactory:
    """
    LLM 工厂类
    负责创建 LLM 实例，仅支持云端 DeepSeek API 模式。
    """
    
    @staticmethod
    def create_llm(
        api_key: str = None,
        base_url: str = None,
        model: str = None
    ) -> ChatOpenAI:
        """
        根据配置创建 LLM 实例

        使用云端 API（DeepSeek）。

        Args:
            api_key: 自定义 API Key（可选）
            base_url: 自定义 Base URL（可选）
            model: 自定义模型名称（可选）

        Returns:
            ChatOpenAI: LLM 实例

        Raises:
            Exception: 当云端模式无法创建时抛出异常
        """
        try:
            # 获取配置
            final_api_key = api_key or settings.OPENAI_API_KEY
            final_base_url = base_url or settings.OPENAI_BASE_URL
            final_model = model or settings.OPENAI_MODEL
            
            # 创建自定义的httpx客户端，配置超时和连接参数
            timeout = httpx.Timeout(
                connect=30.0,  # 连接超时30秒
                read=120.0,    # 读取超时120秒
                write=30.0,    # 写入超时30秒
                pool=30.0      # 连接池超时30秒
            )
            
            # 创建同步和异步httpx客户端
            http_client = httpx.Client(
                timeout=timeout,
                limits=httpx.Limits(
                    max_connections=10,
                    max_keepalive_connections=5
                )
            )
            
            http_async_client = httpx.AsyncClient(
                timeout=timeout,
                limits=httpx.Limits(
                    max_connections=10,
                    max_keepalive_connections=5
                )
            )
            
            # 通用配置
            llm_config = {
                "api_key": final_api_key,
                "base_url": final_base_url,
                "model": final_model,
                "temperature": settings.OPENAI_TEMPERATURE,
                "max_tokens": settings.OPENAI_MAX_TOKENS,
                "timeout": 120,  # 增加超时时间到120秒
                "max_retries": 3,  # 减少重试次数，避免长时间等待
                "request_timeout": 120,  # 请求超时到120秒
                "http_client": http_client,  # 显式传递httpx客户端
                "http_async_client": http_async_client,  # 显式传递异步httpx客户端
            }
            
            # 如果提供了自定义配置，直接使用
            if api_key:
                app_logger.info(f"✅ 使用自定义配置创建 LLM: model={llm_config['model']}")
            else:
                app_logger.info(f"✅ 创建云端 LLM 实例: {llm_config['model']}")
            
            app_logger.info(f"LLM配置: base_url={llm_config['base_url']}, timeout={llm_config['timeout']}s")
            app_logger.info(f"HTTP客户端已配置: connect_timeout=30s, read_timeout=120s")
            
            return ChatOpenAI(**llm_config)

        except Exception as e:
            app_logger.error(f"❌ 创建 LLM 失败: {str(e)}")
            import traceback
            traceback.print_exc()
            raise Exception(
                "无法创建 LLM 实例。请检查：\n"
                "1. OPENAI_API_KEY 是否正确配置\n"
                "2. OPENAI_BASE_URL 是否可访问"
            )
    
    @staticmethod
    def get_llm_info() -> dict:
        """
        获取当前 LLM 配置信息
        
        用于健康检查和调试，会自动隐藏敏感的 API Key 信息。
        
        Returns:
            dict: LLM 配置信息字典，包含模式、模型名称等信息
        """
        llm_config = settings.get_llm_config()
        
        # 隐藏敏感信息（只显示前8位和后4位）
        if "api_key" in llm_config and llm_config["api_key"]:
            key = llm_config["api_key"]
            if len(key) > 12:
                llm_config["api_key"] = key[:8] + "..." + key[-4:]
            else:
                llm_config["api_key"] = "***"
        
        return llm_config
