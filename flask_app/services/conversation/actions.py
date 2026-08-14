"""Conversation Orchestrator可调用的受控业务动作。"""

import re
from typing import Callable, Dict, Optional

from legal_agent_system import get_legal_agent_facade
from legal_agent_system.runtime.errors import AgentRuntimeError

from .schemas import ConversationAction, RouterDecision
from .workspace import (
    WorkspaceVersionConflict,
    get_conversation_workspace_service,
)


CLAIM_MAPPINGS = (
    ("欠薪", "欠薪"), ("工资", "欠薪"), ("试用期", "试用期"),
    ("加班费", "加班费"), ("加班", "加班费"),
    ("辞退", "违法解除"), ("解雇", "违法解除"),
    ("经济补偿", "经济补偿"), ("赔偿", "赔偿金"),
)


class ConversationActions:
    """只通过现有Facade创建Matter、分流和启动任务。"""

    def execute(
        self,
        decision: RouterDecision,
        question: str,
        client_id: str,
        session_id: str,
        context,
        resources: Optional[Dict] = None,
        checkpoint_resource: Optional[Callable[..., None]] = None,
        recovering: bool = False,
        expected_workspace_version: Optional[int] = None,
    ) -> ConversationAction:
        if decision.route in {"normal_chat", "labor_consultation"}:
            return ConversationAction("reply_only")
        if decision.route == "high_risk_handoff":
            return ConversationAction("stop_for_risk", status="blocked")
        if decision.route in {"matter_interaction", "workspace_guidance"}:
            return ConversationAction(
                "guide_to_workspace",
                matter_id=context.matter_id,
                run_id=context.run_id,
            )
        if decision.route == "agent_continue":
            # 会话层不能猜测审批、补信息或重试动作。
            return ConversationAction(
                "guide_to_workspace",
                matter_id=context.matter_id,
                run_id=context.run_id,
                question="请在案件工作台选择明确的继续操作。",
            )
        if decision.route == "labor_triage":
            if not decision.side_effect_authorized:
                return ConversationAction("reply_only")
            return self._create_labor_case(
                question,
                client_id,
                session_id,
                resources or {},
                checkpoint_resource,
                recovering,
                expected_workspace_version,
            )
        return ConversationAction("reply_only")

    def _create_labor_case(
        self,
        question: str,
        client_id: str,
        session_id: str,
        resources: Dict,
        checkpoint_resource: Optional[Callable[..., None]],
        recovering: bool,
        expected_workspace_version: Optional[int],
    ) -> ConversationAction:
        facade = get_legal_agent_facade()
        matter = None
        planned_matter_id = resources.get("matter_id")
        if planned_matter_id:
            try:
                matter = facade.get_matter(planned_matter_id, client_id)
            except AgentRuntimeError as exc:
                if exc.code != "MATTER_NOT_FOUND":
                    raise
        if matter is None:
            matter = next((
                item for item in facade.list_matters(client_id)
                if item.get("session_id") == session_id
            ), None)
        if matter is None:
            matter = facade.create_matter(
                client_id,
                question,
                session_id,
                matter_id=planned_matter_id,
            )
        if expected_workspace_version is not None:
            try:
                get_conversation_workspace_service().select_matter(
                    session_id,
                    matter["matter_id"],
                    client_id,
                    expected_workspace_version,
                )
            except WorkspaceVersionConflict:
                # 用户已在请求执行期间切换案件；后台动作不得抢回指针。
                pass
        if checkpoint_resource is not None:
            checkpoint_resource(matter_id=matter["matter_id"])
        snapshot = facade.update_labor_case_triage(
            matter["matter_id"],
            client_id,
            self._infer_labor_facts(question),
        )
        result = snapshot["result"]
        missing = list(result.get("missing_facts") or [])
        if missing:
            questions = list(result.get("questions") or [])
            return ConversationAction(
                "ask_one_key_question",
                status="awaiting_information",
                matter_id=matter["matter_id"],
                question=questions[0] if questions else "请先在案件工作台补充关键情况。",
            )

        task_type = self._validated_task_type(result)
        if not task_type:
            return ConversationAction(
                "stop_for_risk" if result.get("risk_level") == "high" else "guide_to_workspace",
                status="blocked" if result.get("risk_level") == "high" else "completed",
                matter_id=matter["matter_id"],
            )
        planned_run_id = resources.get("run_id")
        if recovering and planned_run_id:
            try:
                recovered_run = facade.get_run(planned_run_id, client_id)
            except AgentRuntimeError as exc:
                if exc.code != "RUN_NOT_FOUND":
                    raise
            else:
                if recovered_run.get("status") not in {
                    "planning", "executing", "observing", "verifying",
                    "deciding", "replanning", "retrying",
                }:
                    return ConversationAction(
                        "start_agent",
                        matter_id=matter["matter_id"],
                        run_id=planned_run_id,
                        status=recovered_run.get("status", "completed"),
                    )

        def record_reserved(state) -> None:
            if checkpoint_resource is not None:
                checkpoint_resource(run_id=state.run_id)

        run = facade.start_task(
            matter["matter_id"],
            client_id,
            task_type,
            snapshot["facts"],
            run_id=planned_run_id,
            on_reserved=record_reserved,
        )
        return ConversationAction(
            "start_agent",
            matter_id=matter["matter_id"],
            run_id=run.get("run_id"),
            status=run.get("status", "completed"),
        )

    @staticmethod
    def _validated_task_type(result: Dict):
        expected = {
            "simple_labor_consultation": "labor_consultation",
            "labor_relationship_assessment": "labor_relationship_assessment",
            "formal_labor_dispute": "labor_case_analysis",
        }
        value = expected.get(result.get("triage_type"))
        return value if result.get("recommended_task_type") == value else None

    @staticmethod
    def _infer_labor_facts(question: str) -> Dict:
        facts: Dict = {"issue_domain": "labor"}
        if re.search(r"学校.{0,6}(安排|组织).{0,6}实习", question):
            facts["scenario_type"] = "school_arranged_internship"
        elif "勤工助学" in question:
            facts["scenario_type"] = "work_study"
        elif "实习" in question:
            facts["scenario_type"] = "independent_internship"
        elif "兼职" in question:
            facts["scenario_type"] = "part_time"
        elif re.search(r"(应届|毕业).{0,8}(入职|工作|就业)", question):
            facts["scenario_type"] = "graduate_employment"
        elif re.search(r"入职|正式员工|劳动合同|公司", question):
            facts["scenario_type"] = "regular_employment"

        if re.search(r"在校生|在校学生|大[一二三四]|研究生在读", question):
            facts["student_status"] = "current_student"
        elif re.search(r"应届|即将毕业|临近毕业", question):
            facts["student_status"] = "graduating"
        elif re.search(r"已经毕业|已毕业", question):
            facts["student_status"] = "graduated"

        claims = []
        for term, claim in CLAIM_MAPPINGS:
            if term in question and claim not in claims:
                claims.append(claim)
        if claims:
            facts["claim_types"] = claims
        return facts
