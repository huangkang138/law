"""阶段 2 法律来源登记与引用校验工具适配器。"""

from datetime import datetime, timezone

from legal_agent_system.runtime.schemas import AgentTool, ToolResult


def register_authority_verification_tools(registry, authorities) -> None:
    """只注册引用校验工具；来源写入不向 Agent Runtime 开放。"""

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
        name="verify_legal_citation", version="1.0.0", description="校验法律引用的法域、状态、日期和内容哈希",
        input_schema={"type": "object", "required": ["authority_id", "effective_at", "country_code"]},
        supported_jurisdictions=["CN"], risk_level="L1", max_retries=0,
    ), verify_citation)
