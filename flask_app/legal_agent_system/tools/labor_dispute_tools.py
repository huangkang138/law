"""阶段 3 劳动纠纷领域能力的 Runtime 工具适配器。"""

from legal_agent_system.runtime.schemas import AgentTool, ToolResult


def register_labor_dispute_tools(registry, service) -> None:
    """注册证据分析、法律校验和草稿工具，业务规则仍由领域 Service 维护。"""

    def analyze(call_id, arguments, _attempt):
        result = service.analyze(arguments["matter_id"], arguments["client_id"])
        if result["status"] == "blocked_authority":
            return ToolResult(
                tool_call_id=call_id, success=False, data=result,
                error_code="AUTHORITY_REQUIRED", retryable=False,
                warnings=[result["warning"]],
            )
        return ToolResult(
            tool_call_id=call_id, success=True, data=result,
            authority_refs=[item["authority_id"] for item in result.get("authorities", [])],
            assumptions=list(result.get("deadline", {}).get("assumptions", [])),
        )

    def analyze_readonly(mode):
        def handler(call_id, arguments, attempt):
            result = analyze(call_id, arguments, attempt)
            if result.success:
                result.data = {
                    **(result.data or {}),
                    "status": "completed_readonly",
                    "analysis_mode": mode,
                }
                result.data.pop("approval_prompt", None)
            return result
        return handler

    def draft(call_id, arguments, _attempt):
        result = service.create_draft(arguments["matter_id"], arguments["client_id"], True)
        return ToolResult(
            tool_call_id=call_id, success=True, data=result,
            authority_refs=result.get("authority_refs", []),
            warnings=["文书仅为待人工复核草稿，未执行提交或发送。"],
        )

    common = {
        "version": "1.0.0", "supported_jurisdictions": ["CN"],
        "max_retries": 0, "timeout_seconds": 30,
    }
    registry.register(AgentTool(
        name="analyze_labor_dispute", description="校验劳动纠纷事实、期限、证据和法律来源",
        input_schema={"type": "object", "required": ["matter_id", "client_id"]},
        risk_level="L1", **common,
    ), analyze)
    registry.register(AgentTool(
        name="analyze_labor_consultation", description="生成只读劳动法律咨询分析，不进入文书审批",
        input_schema={"type": "object", "required": ["matter_id", "client_id"]},
        risk_level="L1", **common,
    ), analyze_readonly("consultation"))
    registry.register(AgentTool(
        name="analyze_labor_case", description="生成只读劳动案件分析，不进入文书审批",
        input_schema={"type": "object", "required": ["matter_id", "client_id"]},
        risk_level="L1", **common,
    ), analyze_readonly("case_analysis"))
    registry.register(AgentTool(
        name="draft_labor_arbitration_application", description="基于已确认事实和有效来源生成仲裁申请书草稿",
        input_schema={"type": "object", "required": ["matter_id", "client_id"]},
        risk_level="L2", requires_approval=True, **common,
    ), draft)
