"""把Agent权威状态投影为面向用户的确定性会话文案。"""

from typing import Dict, Optional


_RUN_PRESENTATIONS = {
    "planning": ("preparing", "正在整理案件处理步骤", "系统正在准备下一步处理。", False, "open_workspace", "查看工作台"),
    "replanning": ("preparing", "正在重新整理处理步骤", "案件信息变化后，系统正在更新处理顺序。", False, "open_workspace", "查看工作台"),
    "executing": ("processing", "正在处理案件任务", "系统正在执行已确认的处理步骤。", False, "open_workspace", "查看进度"),
    "observing": ("processing", "正在整理处理结果", "系统正在读取并整理已完成步骤的结果。", False, "open_workspace", "查看进度"),
    "verifying": ("processing", "正在核对法律依据", "系统正在核对事实、法域和法律来源。", False, "open_workspace", "查看进度"),
    "deciding": ("processing", "正在形成处理结果", "系统正在基于已验证信息整理下一步。", False, "open_workspace", "查看进度"),
    "retrying": ("processing", "正在重新核对", "系统正在按安全规则重新尝试当前步骤。", False, "open_workspace", "查看进度"),
    "awaiting_jurisdiction": ("needs_jurisdiction", "需要确认适用法域", "请在工作台确认案件适用地区后继续。", True, "confirm_jurisdiction", "去确认法域"),
    "awaiting_information": ("needs_information", "还需要补充案件信息", "请在工作台完成缺失信息后继续。", True, "provide_information", "去补充信息"),
    "blocked_authority": ("blocked_authority", "缺少可靠法律依据", "系统已停止生成结论，请在工作台查看法源状态。", True, "review_authority", "查看法源状态"),
    "awaiting_approval": ("needs_approval", "草稿需要你的确认", "请在工作台审阅内容后作出明确确认。", True, "review_approval", "去审阅草稿"),
    "human_handoff": ("needs_human", "需要人工处理", "当前情况不适合自动继续，请查看人工处理提示。", True, "open_workspace", "查看处理提示"),
    "completed": ("completed", "本次案件分析已完成", "结果和可导出内容已保存在工作台。", False, "view_result", "查看结果"),
    "failed": ("stopped", "本次处理未能完成", "请在工作台查看原因，再决定是否重新开始。", True, "restart", "查看原因"),
    "cancelled": ("stopped", "本次处理已取消", "案件材料仍然保留，可以在工作台重新开始。", False, "restart", "返回工作台"),
}


def present_conversation_state(
    matter: Optional[Dict],
    triage: Optional[Dict],
    run: Optional[Dict],
) -> Dict:
    """只解释状态和下一步，不生成法律结论或替代审批。"""
    if run:
        values = _RUN_PRESENTATIONS.get(run.get("status"))
        if values is None:
            values = (
                "unknown",
                "暂时无法确认处理进度",
                "请在工作台刷新状态，系统不会自动继续高风险操作。",
                True,
                "open_workspace",
                "查看工作台",
            )
    elif triage:
        result = dict(triage.get("result") or {})
        if result.get("risk_level") == "high":
            values = (
                "needs_human",
                "当前情况需要人工处理",
                "系统不会自动推进高风险案件，请查看工作台提示。",
                True,
                "open_workspace",
                "查看处理提示",
            )
        elif result.get("missing_facts"):
            values = (
                "needs_information",
                "还需要补充案件信息",
                "请在工作台完成结构化信息后继续。",
                True,
                "provide_information",
                "去补充信息",
            )
        else:
            values = (
                "matter_ready",
                "案件已经建立",
                "可以进入工作台继续补充材料或启动分析。",
                False,
                "open_workspace",
                "打开工作台",
            )
    elif matter:
        values = (
            "matter_ready",
            "案件工作台已准备好",
            "可以继续确认法域、补充材料和案件事实。",
            False,
            "open_workspace",
            "打开工作台",
        )
    else:
        values = (
            "idle",
            "还没有当前案件",
            "先在对话中说明目标，或进入工作台新建案件。",
            False,
            "none",
            "暂无操作",
        )

    state_key, headline, summary, requires_action, action_type, action_label = values
    return {
        "version": "1.0",
        "state_key": state_key,
        "headline": headline,
        "summary": summary,
        "requires_user_action": requires_action,
        "next_action": {"type": action_type, "label": action_label},
    }
