"""受模板约束的确定性 Planner；每次变化生成新的不可变计划快照。"""

import hashlib
import json
from typing import Any, Dict

from .contracts import PlanRevision, PlanStep, PlanTemplate, TemplateStep


class TemplatePlanBuilder:
    def build(
        self,
        template: PlanTemplate,
        workflow: Dict[str, Any],
        *,
        requested_task_type: str,
        replan_reason: str | None = None,
        triggered_by: str = "runtime",
    ) -> PlanRevision:
        dispute_tags = self._validate_dispute_tags(template, workflow)
        steps = [
            self._instantiate_step(step, workflow, dispute_tags)
            for step in template.steps
        ]
        payload = {
            "template_id": template.template_id,
            "template_version": template.version,
            "facts": workflow.get("facts", {}),
            "dispute_tags": dispute_tags,
            "steps": [item.model_dump(mode="json") for item in steps],
        }
        fingerprint = hashlib.sha256(
            json.dumps(payload, ensure_ascii=False, sort_keys=True).encode()
        ).hexdigest()
        return PlanRevision(
            domain_id=template.domain_id,
            task_type=requested_task_type,
            template_id=template.template_id,
            template_version=template.version,
            input_fingerprint=fingerprint,
            replan_reason=replan_reason,
            triggered_by=triggered_by,
            dispute_tags=dispute_tags,
            steps=steps,
        )

    @staticmethod
    def _instantiate_step(
        step: TemplateStep,
        workflow: Dict[str, Any],
        dispute_tags: list[str],
    ) -> PlanStep:
        enabled = TemplatePlanBuilder._condition_matches(
            step.condition, workflow, dispute_tags,
        )
        condition = step.condition or {}
        condition_tags = list(dict.fromkeys([
            *condition.get("dispute_tag_any", []),
            *condition.get("dispute_tag_all", []),
        ]))
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
            triggered_by_tags=(
                [tag for tag in condition_tags if tag in dispute_tags]
                if enabled else []
            ),
        )

    @staticmethod
    def _condition_matches(
        condition: Dict[str, Any] | None,
        workflow: Dict[str, Any],
        dispute_tags: list[str],
    ) -> bool:
        if not condition:
            return True
        supported = {"fact_present", "enabled", "dispute_tag_any", "dispute_tag_all"}
        unknown_keys = set(condition) - supported
        if unknown_keys:
            raise ValueError(f"模板步骤包含不支持的条件: {sorted(unknown_keys)}")
        checks = []
        fact_name = condition.get("fact_present")
        if fact_name:
            checks.append(bool((workflow.get("facts") or {}).get(fact_name)))
        if "enabled" in condition:
            checks.append(bool(condition["enabled"]))
        any_tags = set(condition.get("dispute_tag_any", []))
        if any_tags:
            checks.append(bool(any_tags.intersection(dispute_tags)))
        all_tags = set(condition.get("dispute_tag_all", []))
        if all_tags:
            checks.append(all_tags.issubset(dispute_tags))
        return all(checks) if checks else False

    @staticmethod
    def _validate_dispute_tags(
        template: PlanTemplate, workflow: Dict[str, Any],
    ) -> list[str]:
        tags = list(dict.fromkeys(workflow.get("dispute_tags") or []))
        unknown = set(tags) - set(template.allowed_dispute_tags)
        if unknown:
            raise ValueError(f"模板不允许争议标签: {sorted(unknown)}")
        return tags
