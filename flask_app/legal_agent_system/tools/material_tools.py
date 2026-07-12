"""阶段 2 材料、事实、时间线和证据清单工具适配器。"""

from legal_agent_system.matters import MaterialService
from legal_agent_system.runtime.schemas import AgentTool, ToolResult


def register_material_tools(registry, materials: MaterialService) -> None:
    """将材料能力包装为统一 ToolResult，供后续 Runtime 计划节点调用。"""

    def parse_document(call_id, arguments, _attempt):
        document = materials.ingest_text(
            arguments["matter_id"], arguments["client_id"], arguments.get("filename"),
            arguments["text"], arguments.get("media_type", "text/plain"),
        )
        return ToolResult(tool_call_id=call_id, success=True, data=document)

    def extract_facts(call_id, arguments, _attempt):
        facts = materials.extract_facts(arguments["matter_id"], arguments["client_id"], arguments["document_id"])
        return ToolResult(
            tool_call_id=call_id, success=True, data={"facts": facts},
            evidence_refs=[fact["material_ref"]["fragment_id"] for fact in facts],
        )

    def build_timeline(call_id, arguments, _attempt):
        timeline = materials.build_timeline(arguments["matter_id"], arguments["client_id"])
        return ToolResult(tool_call_id=call_id, success=True, data={"timeline": timeline})

    def evidence_checklist(call_id, arguments, _attempt):
        checklist = materials.evidence_checklist(arguments["matter_id"], arguments["client_id"])
        return ToolResult(tool_call_id=call_id, success=True, data=checklist, warnings=[checklist["warning"]])

    common = {"version": "1.0.0", "risk_level": "L1", "supported_jurisdictions": ["CN"], "max_retries": 0}
    registry.register(AgentTool(
        name="parse_document", description="解析并持久化已授权文本材料，建立位置分片",
        input_schema={"type": "object", "required": ["matter_id", "client_id", "text"]}, **common,
    ), parse_document)
    registry.register(AgentTool(
        name="extract_legal_facts", description="提取带材料位置引用的候选事实",
        input_schema={"type": "object", "required": ["matter_id", "client_id", "document_id"]}, **common,
    ), extract_facts)
    registry.register(AgentTool(
        name="build_case_timeline", description="从已定位事实构建案件时间线",
        input_schema={"type": "object", "required": ["matter_id", "client_id"]}, **common,
    ), build_timeline)
    registry.register(AgentTool(
        name="generate_evidence_checklist", description="生成当前材料和证据缺口概览",
        input_schema={"type": "object", "required": ["matter_id", "client_id"]}, **common,
    ), evidence_checklist)
