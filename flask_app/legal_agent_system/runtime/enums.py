"""Agent Runtime 使用的稳定状态值和错误码。"""

from enum import Enum


class RunStatus(str, Enum):
    """一次 Agent 运行的生命周期状态。"""
    PLANNING = "planning"
    EXECUTING = "executing"
    AWAITING_APPROVAL = "awaiting_approval"
    RETRYING = "retrying"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


class StepStatus(str, Enum):
    """计划步骤状态；与运行状态分开存储，便于审计每一步。"""
    PENDING = "pending"
    RUNNING = "running"
    AWAITING_APPROVAL = "awaiting_approval"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


class ErrorCode(str, Enum):
    """前后端可稳定识别的错误码，避免依赖中文错误文案。"""
    INVALID_INPUT = "INVALID_INPUT"
    TOOL_NOT_FOUND = "TOOL_NOT_FOUND"
    TOOL_RETRY_EXHAUSTED = "TOOL_RETRY_EXHAUSTED"
    APPROVAL_REQUIRED = "APPROVAL_REQUIRED"
    APPROVAL_EXPIRED = "APPROVAL_EXPIRED"
    RUN_NOT_FOUND = "RUN_NOT_FOUND"
    FORBIDDEN = "FORBIDDEN"
    INVALID_STATE = "INVALID_STATE"
    RUN_CANCELLED = "RUN_CANCELLED"
