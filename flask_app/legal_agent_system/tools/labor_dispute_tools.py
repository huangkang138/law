"""阶段 3 劳动纠纷领域能力的 Runtime 工具适配器。"""

from legal_agent_system.runtime.schemas import AgentTool, ToolResult
from legal_agent_system.labor_disputes.schemas import describe_missing_facts


def register_labor_dispute_tools(registry, service, issue_analysis) -> None:
    """注册证据分析、法律校验和草稿工具，业务规则仍由领域 Service 维护。"""

    def analyze(call_id, arguments, _attempt):
        result = service.analyze(arguments["matter_id"], arguments["client_id"])
        if result["status"] == "blocked_authority":
            return ToolResult(
                tool_call_id=call_id, success=False, data=result,
                error_code="AUTHORITY_REQUIRED", retryable=False,
                warnings=[result["warning"]],
            )
        if result["status"] == "awaiting_information":
            return ToolResult(
                tool_call_id=call_id, success=False, data=result,
                error_code="INFORMATION_REQUIRED", retryable=False,
                assumptions=[
                    assumption
                    for item in result.get("rule_decisions", [])
                    for assumption in item.get("assumptions", [])
                ],
                warnings=[result.get("warning", "实体规则关键事实不足")],
            )
        rule_authority_refs = [
            authority_id
            for item in result.get("rule_decisions", [])
            for authority_id in item.get("authority_refs", [])
        ]
        return ToolResult(
            tool_call_id=call_id, success=True, data=result,
            authority_refs=list(dict.fromkeys([
                *[item["authority_id"] for item in result.get("authorities", [])],
                *rule_authority_refs,
            ])),
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

    def issue_handler(method, *, require_complete=False):
        def handler(call_id, arguments, _attempt):
            data = method(arguments["matter_id"], arguments["client_id"])
            missing = list(data.get("missing_facts") or [])
            if data.get("status") == "authority_required":
                return ToolResult(
                    tool_call_id=call_id,
                    success=False,
                    data=data,
                    evidence_refs=list(data.get("evidence_refs") or []),
                    authority_refs=list(data.get("authority_refs") or []),
                    error_code="AUTHORITY_REQUIRED",
                    error_message="当前实体规则缺少已验证官方法源",
                    retryable=False,
                    assumptions=list(data.get("assumptions") or []),
                    warnings=list(data.get("warnings") or []),
                )
            if require_complete and missing:
                return ToolResult(
                    tool_call_id=call_id,
                    success=False,
                    data=data,
                    evidence_refs=list(data.get("evidence_refs") or []),
                    authority_refs=list(data.get("authority_refs") or []),
                    error_code="INFORMATION_REQUIRED",
                    error_message=f"当前问题步骤缺少事实：{describe_missing_facts(missing)}",
                    retryable=False,
                    warnings=list(data.get("warnings") or []),
                )
            return ToolResult(
                tool_call_id=call_id,
                success=True,
                data=data,
                evidence_refs=list(data.get("evidence_refs") or []),
                authority_refs=list(data.get("authority_refs") or []),
                assumptions=list(data.get("assumptions") or []),
                warnings=list(data.get("warnings") or []),
            )
        return handler

    issue_schema = {
        "type": "object",
        "required": ["matter_id", "client_id"],
    }
    registry.register(AgentTool(
        name="analyze_probation",
        description="核对试用期期限、工资和解除条件并返回可追溯结果",
        input_schema=issue_schema,
        risk_level="L1",
        **common,
    ), issue_handler(issue_analysis.probation, require_complete=True))
    registry.register(AgentTool(
        name="analyze_wage_arrears",
        description="在主劳动计划中整理欠薪期间、金额和待复核事实",
        input_schema=issue_schema,
        risk_level="L1",
        **common,
    ), issue_handler(issue_analysis.wage_arrears, require_complete=True))
    registry.register(AgentTool(
        name="analyze_labor_termination",
        description="在主劳动计划中整理解除事实、依据和程序缺口",
        input_schema=issue_schema,
        risk_level="L1",
        **common,
    ), issue_handler(issue_analysis.termination, require_complete=True))
    registry.register(AgentTool(
        name="analyze_economic_compensation",
        description="在主劳动计划中估算经济补偿并保留人工复核边界",
        input_schema=issue_schema,
        risk_level="L1",
        **common,
    ), issue_handler(issue_analysis.economic_compensation, require_complete=True))
    registry.register(AgentTool(
        name="analyze_overtime_pay",
        description="按工时类型核算加班费并保留工时制度、基数和证据复核边界",
        input_schema=issue_schema,
        risk_level="L1",
        **common,
    ), issue_handler(issue_analysis.overtime_pay, require_complete=True))

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
