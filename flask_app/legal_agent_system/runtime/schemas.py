from typing import Any, Dict, List, Optional

from pydantic import BaseModel, ConfigDict, Field

from .enums import RunStatus


class AgentTool(BaseModel):
    """工具能力声明；Runtime 根据声明控制审批和重试。"""
    name: str = Field(min_length=1, max_length=100)
    description: str = Field(min_length=1, max_length=500)
    input_schema: Dict[str, Any]
    requires_approval: bool = False
    max_retries: int = Field(default=1, ge=0, le=3)


class ToolResult(BaseModel):
    """所有工具必须返回的统一结果，禁止直接向 Runtime 返回任意对象。"""
    tool_call_id: str
    success: bool
    data: Optional[Dict[str, Any]] = None
    evidence_refs: List[str] = Field(default_factory=list)
    authority_refs: List[str] = Field(default_factory=list)
    error_code: Optional[str] = None
    error_message: Optional[str] = None
    retryable: bool = False


class AgentState(BaseModel):
    """LangGraph 节点之间传递、并同步持久化的最小状态。"""

    # 序列化时使用字符串枚举，保证 JSON 和数据库状态稳定可读。
    model_config = ConfigDict(use_enum_values=True)

    run_id: str
    session_id: Optional[str] = None
    matter_id: str
    client_id: str
    goal: str
    status: RunStatus = RunStatus.PLANNING
    current_step_id: Optional[str] = None
    pending_approval_id: Optional[str] = None
    tool_result_ids: List[str] = Field(default_factory=list)
    retry_count: int = 0
    approved: Optional[bool] = None
    final_output: Optional[Dict[str, Any]] = None
    error_code: Optional[str] = None
"""Agent、工具和运行状态的 Pydantic 数据契约。"""
