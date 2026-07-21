"""劳动案件分流工具适配器。"""

from legal_agent_system.runtime.schemas import AgentTool, ToolResult


def register_labor_triage_tools(registry, service) -> None:
    """注册只读、无外部动作的劳动关系初筛工具。"""

    def assess(call_id, arguments, _attempt):
        result = service.assess(arguments["matter_id"], arguments["client_id"])
        return ToolResult(
            tool_call_id=call_id,
            success=True,
            data=result,
            warnings=[result["notice"]],
            assumptions=list(result.get("basis", [])),
        )

    registry.register(AgentTool(
        name="assess_labor_relationship",
        description="基于已确认的实习、兼职和用工事实进行劳动关系初步判断与案件分流",
        input_schema={"type": "object", "required": ["matter_id", "client_id"]},
        version="1.0.0",
        supported_jurisdictions=["CN"],
        risk_level="L1",
        max_retries=0,
        timeout_seconds=10,
    ), assess)
