"""阶段 2 法律来源登记与引用校验工具适配器。"""

from datetime import datetime, timezone

from legal_agent_system.runtime.schemas import AgentTool, ToolResult


def register_authority_tools(registry, authorities) -> None:
    """注册来源登记和引用校验工具；未知来源必须返回警告。"""

    def register_source(call_id, arguments, _attempt):
        authority = authorities.register(arguments)
        return ToolResult(tool_call_id=call_id, success=True, data=authority, authority_refs=[authority["authority_id"]])

    def verify_citation(call_id, arguments, _attempt):
        effective_at = datetime.fromisoformat(arguments["effective_at"].replace("Z", "+00:00"))
        if effective_at.tzinfo is None:
            effective_at = effective_at.replace(tzinfo=timezone.utc)
        verified = authorities.verify(arguments["authority_id"], effective_at, arguments["country_code"])
        return ToolResult(
            tool_call_id=call_id, success=verified["valid"], data=verified,
            authority_refs=[arguments["authority_id"]], warnings=verified["warnings"],
            error_code=None if verified["valid"] else "AUTHORITY_UNVERIFIED",
        )

    registry.register(AgentTool(
        name="register_legal_authority", version="1.0.0", description="登记结构化法律来源",
        input_schema={"type": "object", "required": ["country_code", "authority_type", "title", "text", "source_url", "issuing_body"]},
        supported_jurisdictions=["CN"], risk_level="L1", max_retries=0,
    ), register_source)
    registry.register(AgentTool(
        name="verify_legal_citation", version="1.0.0", description="校验法律引用的法域、状态、日期和内容哈希",
        input_schema={"type": "object", "required": ["authority_id", "effective_at", "country_code"]},
        supported_jurisdictions=["CN"], risk_level="L1", max_retries=0,
    ), verify_citation)
