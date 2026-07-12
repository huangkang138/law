"""Agent Runtime 领域异常。"""

class AgentRuntimeError(Exception):
    """包含稳定错误码、可安全映射为 API 响应的异常。"""
    def __init__(self, message: str, code: str):
        super().__init__(message)
        self.code = code


class RetryableToolError(AgentRuntimeError):
    """预留给工具适配器标记可重试异常。"""
    pass
