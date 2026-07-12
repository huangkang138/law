"""受控工具注册中心。"""

from typing import Any, Callable, Dict, Tuple

from .enums import ErrorCode
from .errors import AgentRuntimeError
from .schemas import AgentTool, ToolResult

ToolHandler = Callable[[str, Dict[str, Any], int], ToolResult]


class ToolRegistry:
    """保存工具声明与处理器，阻止 Agent 任意调用内部函数。"""

    def __init__(self) -> None:
        self._tools: Dict[str, Tuple[AgentTool, ToolHandler]] = {}

    def register(self, definition: AgentTool, handler: ToolHandler) -> None:
        """注册工具；重复名称直接失败，避免实现被静默覆盖。"""
        if definition.name in self._tools:
            raise ValueError(f"工具已注册: {definition.name}")
        self._tools[definition.name] = (definition, handler)

    def get(self, name: str) -> Tuple[AgentTool, ToolHandler]:
        """按白名单名称获取工具声明和执行函数。"""
        try:
            return self._tools[name]
        except KeyError as exc:
            raise AgentRuntimeError(f"工具不存在: {name}", ErrorCode.TOOL_NOT_FOUND.value) from exc
