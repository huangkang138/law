"""青年就业劳动关系的确定性初筛规则。
    、_missing_facts、_result执行五类分流、劳动关系倾向判断、缺失事实和人工复核决策
    负责到底分到哪一类
"""

from typing import Dict, List, Optional

from .triage_schemas import LaborTriageFacts, TRIAGE_QUESTIONS


TRIAGE_RULE_VERSION = "cn-labor-triage-1"


class LaborTriageDecisionEngine:
    """按主体、劳动管理、有偿劳动和业务组成进行确定性初筛。"""

    def assess(self, facts: LaborTriageFacts) -> Dict:#按顺序做判断
        dispute_tags = list(dict.fromkeys(item.strip() for item in facts.claim_types if item.strip()))
        if facts.urgent_risks:
            return self._result(
                triage_type="high_risk_handoff", relationship_status="not_assessed",
                facts=facts, dispute_tags=dispute_tags, risk_level="high",
                basis=["存在需要优先保护人身、期限或群体权益的高风险信号"],
                recommended_task_type=None,
                recommended_next_step="停止自动确定性判断，尽快由法律专业人员或有关机构处理。",
                manual_review_required=True,
            )
        if facts.issue_domain == "non_labor":
            return self._result(
                triage_type="non_labor_dispute", relationship_status="not_assessed",
                facts=facts, dispute_tags=dispute_tags, risk_level="low",
                basis=["用户确认当前问题不属于劳动用工场景"],
                recommended_task_type=None,
                recommended_next_step="转入对应民事、消费、校园或其他领域入口。",
                manual_review_required=False,
            )

        missing = self._missing_facts(facts)
        if missing:
            return self._result(
                triage_type="labor_relationship_assessment", relationship_status="uncertain",
                facts=facts, dispute_tags=dispute_tags, risk_level="medium",
                basis=["劳动关系判断的关键事实仍不完整"], missing_facts=missing,
                recommended_task_type="labor_relationship_assessment",
                recommended_next_step="补充关键事实后再判断，不直接进入劳动仲裁。",
                manual_review_required=True,
            )

        student_training = (
            facts.student_status == "current_student"
            and facts.scenario_type in {"school_arranged_internship", "work_study"}
            and facts.school_arranged is True
            and facts.employment_intent is False
        )
        if student_training:
            return self._result(
                triage_type="labor_relationship_assessment",
                relationship_status="likely_not_established",
                facts=facts, dispute_tags=dispute_tags, risk_level="medium",
                basis=[
                    "当前事实更接近学校教学安排或勤工助学",
                    "双方没有以建立正式用工关系为目的",
                    "协议名称不能单独决定关系性质，仍需核对实际履行",
                ],
                recommended_task_type="labor_relationship_assessment",
                recommended_next_step="保留协议、学校安排、工作记录和报酬凭证，人工复核实际履行关系。",
                manual_review_required=True,
            )

        core = {
            "用工主体具备主体资格": facts.employer_qualified,
            "实际提供有报酬劳动": facts.paid_labor,
            "接受单位劳动管理": facts.management_control,
            "工作属于单位业务组成部分": facts.business_integrated,
        }
        positive = [label for label, value in core.items() if value is True]
        negative = [label for label, value in core.items() if value is False]
        if len(positive) == len(core) and facts.employment_intent is True:
            triage_type = "formal_labor_dispute" if dispute_tags else "simple_labor_consultation"
            return self._result(
                triage_type=triage_type, relationship_status="likely_established",
                facts=facts, dispute_tags=dispute_tags,
                risk_level="medium" if facts.student_status in {"current_student", "graduating"} else "low",
                basis=positive + ["双方具有建立持续用工关系的目的"],
                recommended_task_type="labor_case_analysis" if dispute_tags else "labor_consultation",
                recommended_next_step="继续核对合同、考勤、工资、工作安排等证据，再进入对应劳动任务。",
                manual_review_required=facts.student_status in {"current_student", "graduating"},
            )
        if len(negative) >= 2:
            return self._result(
                triage_type="labor_relationship_assessment",
                relationship_status="likely_not_established",
                facts=facts, dispute_tags=dispute_tags, risk_level="medium",
                basis=[f"不具备或证据不支持：{item}" for item in negative],
                recommended_task_type="labor_relationship_assessment",
                recommended_next_step="先按实际合同和履行情况确认可能的劳务、实习或其他关系。",
                manual_review_required=True,
            )
        return self._result(
            triage_type="labor_relationship_assessment", relationship_status="uncertain",
            facts=facts, dispute_tags=dispute_tags, risk_level="medium",
            basis=positive + [f"证据不支持：{item}" for item in negative],
            recommended_task_type="labor_relationship_assessment",
            recommended_next_step="补充书面协议、考勤、报酬、管理和工作内容证据后人工复核。",
            manual_review_required=True,
        )

    @staticmethod
    def _missing_facts(facts: LaborTriageFacts) -> List[str]:#检查哪些问题还没有问
        missing = []
        if facts.issue_domain == "unknown":
            missing.append("issue_domain")
        if facts.scenario_type == "unknown":
            missing.append("scenario_type")
        if facts.student_status == "unknown":
            missing.append("student_status")
        if (
            facts.student_status in {"current_student", "graduating"}
            or facts.scenario_type in {
                "school_arranged_internship", "independent_internship", "work_study",
            }
        ) and facts.school_arranged is None:
            missing.append("school_arranged")
        for name in (
            "employment_intent", "employer_qualified", "paid_labor",
            "management_control", "business_integrated",
        ):
            if getattr(facts, name) is None:
                missing.append(name)
        return missing

    @staticmethod
    def _result(
        *, triage_type: str, relationship_status: str, facts: LaborTriageFacts,
        dispute_tags: List[str], risk_level: str, basis: List[str],
        recommended_task_type: Optional[str], recommended_next_step: str,
        manual_review_required: bool, missing_facts: Optional[List[str]] = None,
    ) -> Dict:
        missing = missing_facts or []
        return {
            "triage_type": triage_type,
            "relationship_status": relationship_status,
            "dispute_tags": dispute_tags,
            "basis": basis,
            "missing_facts": missing,
            "questions": [TRIAGE_QUESTIONS[name] for name in missing],
            "risk_level": risk_level,
            "recommended_task_type": recommended_task_type,
            "recommended_next_step": recommended_next_step,
            "manual_review_required": manual_review_required,
            "rule_version": TRIAGE_RULE_VERSION,
            "legal_conclusion": False,
            "notice": "本结果是基于已确认事实的初步分流，不替代劳动仲裁、法院或法律专业人员的最终认定。",
            "scenario_type": facts.scenario_type,
            "student_status": facts.student_status,
        }
