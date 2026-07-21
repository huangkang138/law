"""Agent Runtime 使用的稳定状态值和错误码。"""

from enum import Enum


class RunStatus(str, Enum):
    """一次 Agent 运行的生命周期状态。"""
    PLANNING = "planning"
    AWAITING_JURISDICTION = "awaiting_jurisdiction"
    AWAITING_INFORMATION = "awaiting_information"
    EXECUTING = "executing"
    OBSERVING = "observing"
    VERIFYING = "verifying"
    DECIDING = "deciding"
    AWAITING_APPROVAL = "awaiting_approval"
    BLOCKED_AUTHORITY = "blocked_authority"
    REPLANNING = "replanning"
    HUMAN_HANDOFF = "human_handoff"
    RETRYING = "retrying"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"
    SKIPPED = "skipped"


class StepStatus(str, Enum):
    """计划步骤状态；与运行状态分开存储，便于审计每一步。"""
    PENDING = "pending"
    RUNNING = "running"
    AWAITING_APPROVAL = "awaiting_approval"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"
    SKIPPED = "skipped"


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
    JURISDICTION_CONFIRMATION_REQUIRED = "JURISDICTION_CONFIRMATION_REQUIRED"
    INFORMATION_REQUIRED = "INFORMATION_REQUIRED"
    AUTHORITY_REQUIRED = "AUTHORITY_REQUIRED"
    UNSUPPORTED_ACTION = "UNSUPPORTED_ACTION"
    VERIFICATION_FAILED = "VERIFICATION_FAILED"
    BUDGET_EXCEEDED = "BUDGET_EXCEEDED"
    INVALID_PLAN_COMPOSITION = "INVALID_PLAN_COMPOSITION"
