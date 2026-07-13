"""劳动纠纷动态计划构建器。"""
import hashlib
import json


class LaborPlanBuilder:
    def build(self, workflow: dict) -> tuple[list, str]:
        claims = workflow.get("facts", {}).get("claim_types", [])
        focus = "核对材料与证据缺口"
        if "欠薪" in claims:
            focus = "核对欠薪期间、金额与工资证据"
        elif "违法解除" in claims:
            focus = "核对解除原因、程序与通知证据"
        plan = [
            {"name": focus, "tool_name": "generate_evidence_checklist"},
            {"name": "计算期限并验证法律来源", "tool_name": "analyze_labor_dispute"},
            {"name": "经审批生成劳动仲裁申请书草稿", "tool_name": "draft_labor_arbitration_application"},
        ]
        fingerprint = hashlib.sha256(json.dumps({"facts": workflow.get("facts", {}), "plan": plan}, ensure_ascii=False, sort_keys=True).encode()).hexdigest()
        return plan, fingerprint
