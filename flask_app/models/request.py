"""
请求模型
"""

from typing import Optional
from pydantic import BaseModel, Field


class ChatRequest(BaseModel):
    """聊天请求模型"""
    question: str = Field(..., description="用户问题", min_length=1)
    session_id: str = Field("default", description="会话ID")
    jurisdiction: str = Field("中国", description="法律辖区")


class ResetRequest(BaseModel):
    """重置会话请求模型"""
    session_id: str = Field("default", description="会话ID")


class RetrieveRequest(BaseModel):
    """检索请求"""
    query: str = Field(..., description="查询文本", min_length=1)
    contract_id: Optional[str] = Field(None, description="指定合同ID（可选）")
    top_k: int = Field(3, description="返回结果数量", ge=1, le=10)


class DebateRequest(BaseModel):
    """辩论请求"""
    case_description: str = Field(..., description="案件描述", min_length=20)
    plaintiff_arguments: Optional[str] = Field(None, description="原告论据")
    defendant_arguments: Optional[str] = Field(None, description="被告论据")
