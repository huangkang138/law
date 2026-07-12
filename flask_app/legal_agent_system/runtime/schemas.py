"""Agent、工具和运行状态的 Pydantic 数据契约。（AgentState、AgentTool、ToolResult）"""

from datetime import date, datetime
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
    version: str = "1.0.0"
    supported_jurisdictions: List[str] = Field(default_factory=list)
    risk_level: str = "L1"
    timeout_seconds: int = Field(default=30, ge=1, le=300)


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
    assumptions: List[str] = Field(default_factory=list)
    warnings: List[str] = Field(default_factory=list)


class JurisdictionContext(BaseModel):
    """显式法域上下文；法域不明确时不得静默回退到中国法。"""

    country_code: str = Field(pattern=r"^[A-Z]{2}$")
    subdivision_code: Optional[str] = None
    legal_system: str
    governing_law: Optional[str] = None
    forum: Optional[str] = None
    language: str = "zh-CN"
    effective_at: date
    confidence: float = Field(ge=0, le=1)
    confirmed_by_user: bool = False


class MaterialRef(BaseModel):
    """事实指向材料原文位置的最小引用。"""

    document_id: str
    fragment_id: str
    start_offset: int = Field(ge=0)
    end_offset: int = Field(gt=0)
    page_number: Optional[int] = Field(default=None, ge=1)
    quote: str


class LegalAuthorityRecord(BaseModel):
    """可验证法律来源的结构化契约。"""

    authority_id: str
    jurisdiction: JurisdictionContext
    authority_type: str
    title: str
    provision: Optional[str] = None
    text: str
    source_url: str
    issuing_body: str
    published_at: Optional[date] = None
    effective_from: Optional[date] = None
    effective_to: Optional[date] = None
    status: str
    retrieved_at: datetime
    content_hash: str


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
