"""受模板约束的确定性 Planner；每次变化生成新的不可变计划快照。"""

import hashlib
import json
from typing import Any, Dict

from .contracts import PlanRevision, PlanStep, PlanTemplate, TemplateStep


class TemplatePlanBuilder:
    def build(
        self,
        template: PlanTemplate,  # 计划模板对象，包含构建计划所需的基本结构信息
        workflow: Dict[str, Any],  # 工作流字典，包含执行流程中的各种数据
        *,
        requested_task_type: str,  # 请求的任务类型，指定计划执行的具体任务类别
        replan_reason: str | None = None,  # 重新计划的原因，可选参数，用于说明重新计划的原因
        triggered_by: str = "runtime",  # 触发者，默认为"runtime"，表示由运行时触发
    ) -> PlanRevision:  # 返回一个计划修订对象，包含构建完成的计划信息
        # 根据模板步骤和工作流实例化各个步骤
        steps = [self._instantiate_step(step, workflow) for step in template.steps]
        # 构建有效载荷字典，包含模板ID、版本、事实和步骤信息
        payload = {
            "template_id": template.template_id,
            "template_version": template.version,
            "facts": workflow.get("facts", {}),
            "steps": [item.model_dump(mode="json") for item in steps],
        }
        # 计算有效载荷的指纹，用于唯一标识这个特定的计划配置
        fingerprint = hashlib.sha256(
            json.dumps(payload, ensure_ascii=False, sort_keys=True).encode()
        ).hexdigest()
        # 创建并返回一个计划修订对象，包含所有构建的计划信息和元数据
        return PlanRevision(
            domain_id=template.domain_id,
            task_type=requested_task_type,
            template_id=template.template_id,
            template_version=template.version,
            input_fingerprint=fingerprint,
            replan_reason=replan_reason,
            triggered_by=triggered_by,
            steps=steps,
        )

    @staticmethod
    def _instantiate_step(step: TemplateStep, workflow: Dict[str, Any]) -> PlanStep:
        enabled = TemplatePlanBuilder._condition_matches(step.condition, workflow)
        return PlanStep(
            step_id=step.step_id,
            name=step.name,
            step_type=step.step_type,
            tool_name=step.tool_name,
            depends_on=step.depends_on,
            status="pending" if enabled else "skipped",
            skip_reason=None if enabled else step.skip_reason,
            requires_approval=step.requires_approval,
            verification_policy_ids=step.verification_policy_ids,
            on_failure=step.on_failure,
            arguments=step.arguments,
        )

    @staticmethod
    def _condition_matches(condition: Dict[str, Any] | None, workflow: Dict[str, Any]) -> bool:
        if not condition:
            return True
        fact_name = condition.get("fact_present")
        if fact_name:
            return bool((workflow.get("facts") or {}).get(fact_name))
        return bool(condition.get("enabled", False))
