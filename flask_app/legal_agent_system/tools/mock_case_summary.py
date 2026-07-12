from typing import Any, Dict

from legal_agent_system.runtime.schemas import AgentTool, ToolResult


def _mock_case_summary(tool_call_id: str, arguments: Dict[str, Any], attempt: int) -> ToolResult:
    """第一次返回可重试错误，第二次生成固定结构的模拟结果。"""
    # 该故障仅用于集成测试状态机，不代表真实法律工具的重试策略。
    if arguments.get("fail_first_attempt", True) and attempt == 1:
        return ToolResult(
            tool_call_id=tool_call_id,
            success=False,
            error_code="MOCK_TEMPORARY_FAILURE",
            error_message="模拟临时故障",
            retryable=True,
        )
    return ToolResult(
        tool_call_id=tool_call_id,
        success=True,
        data={
            "summary": f"已完成模拟案件摘要：{arguments['goal']}",
            "notice": "该结果仅用于验证 Agent Runtime，不构成法律意见。",
        },
    )


def register_mock_tools(registry) -> None:
    """向受控注册中心登记模拟工具及其安全声明。"""
    registry.register(
        AgentTool(
            name="mock_case_summary",
            description="生成用于验证状态机的模拟案件摘要",
            input_schema={"type": "object", "required": ["goal"]},
            requires_approval=True,
            max_retries=1,
        ),
        _mock_case_summary,
    )
"""用于验证重试、审批和恢复流程的模拟工具。"""
