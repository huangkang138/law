"""现有劳动补偿能力的 Agent 工具适配器。"""

from services.labor_compensation_service import get_labor_compensation_service

from legal_agent_system.runtime.schemas import AgentTool, ToolResult


def register_labor_tools(registry) -> None:
    """注册第一个真实业务工具，不在适配器中复制计算公式。"""

    def calculate(call_id, arguments, _attempt):
        result = get_labor_compensation_service().calculate(
            arguments["monthly_salary"], arguments["years"], arguments.get("months", 0),
        )
        return ToolResult(
            tool_call_id=call_id, success=True, data=result,
            warnings=[result["warning"]], assumptions=["使用项目当前既有劳动补偿估算公式"],
        )

    registry.register(AgentTool(
        name="calculate_labor_compensation", version="1.0.0",
        description="按月工资、工作年限和额外月份估算劳动经济补偿",
        input_schema={
            "type": "object",
            "required": ["monthly_salary", "years"],
            "properties": {
                "monthly_salary": {"type": "number", "exclusiveMinimum": 0},
                "years": {"type": "integer", "minimum": 0},
                "months": {"type": "integer", "minimum": 0, "maximum": 11},
            },
        },
        supported_jurisdictions=["CN"], risk_level="L1", max_retries=0,
    ), calculate)
