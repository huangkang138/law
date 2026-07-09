"""
响应模型
"""

from typing import Optional, Dict, Any, List
from pydantic import BaseModel, Field


class HealthResponse(BaseModel):
    """健康检查响应"""
    status: str = Field(..., description="服务状态")
    version: str = Field(..., description="服务版本")
    llm_mode: str = Field(..., description="LLM 模式")
    llm_model: str = Field(..., description="LLM 模型")


class ChatResponse(BaseModel):
    """聊天响应"""
    success: bool = Field(..., description="是否成功")
    answer: str = Field(..., description="AI 回答")
    session_id: str = Field(..., description="会话ID")
    tokens: Optional[Dict[str, int]] = Field(None, description="Token 统计")


class ResetResponse(BaseModel):
    """重置响应"""
    success: bool = Field(..., description="是否成功")
    message: str = Field(..., description="响应消息")
    session_id: str = Field(..., description="会话ID")


class UploadResponse(BaseModel):
    """文档上传响应"""
    success: bool = Field(..., description="是否成功")
    message: str = Field(..., description="响应消息")
    contract_id: str = Field(..., description="合同唯一标识")
    chunk_count: int = Field(..., description="切片数量")
    text_length: int = Field(..., description="文本总长度")


class RetrieveResponse(BaseModel):
    """检索响应"""
    success: bool = Field(..., description="是否成功")
    query: str = Field(..., description="查询文本")
    results: list = Field(..., description="检索结果列表")
    result_count: int = Field(..., description="结果数量")


class ContractInfoResponse(BaseModel):
    """合同信息响应"""
    success: bool = Field(..., description="是否成功")
    contract_id: str = Field(..., description="合同ID")
    exists: bool = Field(..., description="是否存在")
    chunk_count: int = Field(..., description="切片数量")


class DeleteResponse(BaseModel):
    """删除响应"""
    success: bool = Field(..., description="是否成功")
    message: str = Field(..., description="响应消息")
    contract_id: str = Field(..., description="合同ID")
    deleted_count: int = Field(..., description="删除的切片数量")


class ContractListResponse(BaseModel):
    """合同列表响应"""
    success: bool = Field(..., description="是否成功")
    contracts: list = Field(..., description="合同ID列表")
    total_count: int = Field(..., description="合同总数")


class ContractReviewResponse(BaseModel):
    """合同审查响应"""
    success: bool = Field(..., description="是否成功")
    contract_id: str = Field(..., description="合同ID")
    review_result: Dict[str, Any] = Field(..., description="审查结果")
    risk_score: int = Field(..., description="风险评分")
    suggestions: List[str] = Field(..., description="修改建议")


class DebateResponse(BaseModel):
    """辩论响应"""
    success: bool = Field(..., description="是否成功")
    case_description: str = Field(..., description="案件描述")
    plaintiff_arguments: str = Field(..., description="原告论据")
    defendant_arguments: str = Field(..., description="被告论据")
    judge_opinion: str = Field(..., description="法官意见")
