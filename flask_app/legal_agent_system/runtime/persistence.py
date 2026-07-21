import hashlib
import json
import uuid
from datetime import datetime, timedelta, timezone
from typing import Dict, List, Optional

from core.database import SessionLocal
from sqlalchemy import text
from models.db_models import (
    AgentAuditEvent,
    AgentRun,
    AgentStep,
    ApprovalRequest,
    Matter,
    ToolCall,
)

from .enums import ErrorCode, RunStatus, StepStatus
from .errors import AgentRuntimeError
from .schemas import AgentState, ToolResult
from legal_agent_system.models import AgentEventOutbox, AgentPlan, AgentRunAction
from legal_agent_system.capabilities.contracts import PlanRevision

"""数据库仓储层。它让Agent能够暂停、恢复和审计。"""

def _id(prefix: str) -> str:
    """生成带业务前缀的可读主键。"""
    return f"{prefix}_{uuid.uuid4().hex}"


class AgentRepository:
    """集中管理运行状态、步骤、工具调用、审批和审计记录。"""

    def create_run(
        self, goal: str, client_id: str, session_id: Optional[str],
        task_type: str = "mock_case_summary",
    ) -> AgentState:
        """在同一事务中创建 Matter、AgentRun 和首条审计事件。"""
        db = SessionLocal()
        try:
            matter = Matter(id=_id("matter"), client_id=client_id, session_id=session_id, title=goal[:60], goal=goal)
            # 显式 flush 保证写入 AgentRun 前 Matter 外键已经存在。
            db.add(matter)
            db.flush()
            run = AgentRun(id=_id("run"), matter_id=matter.id, client_id=client_id, status=RunStatus.PLANNING.value)
            state = AgentState(
                run_id=run.id, matter_id=matter.id, client_id=client_id,
                session_id=session_id, goal=goal, task_type=task_type,
            )
            run.state_json = state.model_dump(mode="json")
            db.add(run)
            db.flush()
            self._audit(db, run.id, "run_created", {"goal": goal, "task_type": task_type})
            db.commit()
            return state
        except Exception:
            db.rollback()
            raise
        finally:
            db.close()

    def create_run_for_matter(self, matter_id: str, client_id: str, task_type: str) -> AgentState:
        """为已有 Matter 创建真实业务 Run，不重复创建案件工作区。"""
        db = SessionLocal()
        try:
            matter = db.get(Matter, matter_id)
            if matter is None:
                raise AgentRuntimeError("Matter 不存在", "MATTER_NOT_FOUND")
            if matter.client_id != client_id:
                raise AgentRuntimeError("无权访问该 Matter", ErrorCode.FORBIDDEN.value)
            run = AgentRun(id=_id("run"), matter_id=matter.id, client_id=client_id, status=RunStatus.PLANNING.value)
            state = AgentState(
                run_id=run.id, matter_id=matter.id, client_id=client_id,
                session_id=matter.session_id, goal=matter.goal, task_type=task_type,
            )
            run.state_json = state.model_dump(mode="json")
            db.add(run)
            db.flush()
            self._audit(db, run.id, "run_created", {"goal": matter.goal, "task_type": task_type})
            db.commit()
            return state
        except Exception:
            db.rollback()
            raise
        finally:
            db.close()

    def find_or_create_active_run(self, matter_id: str, client_id: str, task_type: str) -> AgentState:
        """在 PostgreSQL 事务锁内复用或创建 Run，避免并发双击生成两个活动任务。"""
        lock_key = int.from_bytes(
            hashlib.sha256(f"{matter_id}:{client_id}:{task_type}".encode()).digest()[:8],
            byteorder="big", signed=True,
        )
        terminal = {RunStatus.COMPLETED.value, RunStatus.FAILED.value, RunStatus.CANCELLED.value}
        db = SessionLocal()
        try:
            db.execute(text("SELECT pg_advisory_xact_lock(:lock_key)"), {"lock_key": lock_key})
            matter = db.get(Matter, matter_id)
            if matter is None:
                raise AgentRuntimeError("Matter 不存在", "MATTER_NOT_FOUND")
            if matter.client_id != client_id:
                raise AgentRuntimeError("无权访问该 Matter", ErrorCode.FORBIDDEN.value)
            runs = db.query(AgentRun).filter(
                AgentRun.matter_id == matter_id, AgentRun.client_id == client_id,
            ).order_by(AgentRun.created_at.desc()).all()
            for run in runs:
                raw = run.state_json or {}
                if raw.get("task_type") == task_type and run.status not in terminal:
                    return AgentState.model_validate(raw)
            run = AgentRun(id=_id("run"), matter_id=matter.id, client_id=client_id, status=RunStatus.PLANNING.value)
            state = AgentState(
                run_id=run.id, matter_id=matter.id, client_id=client_id,
                session_id=matter.session_id, goal=matter.goal, task_type=task_type,
            )
            run.state_json = state.model_dump(mode="json")
            db.add(run)
            db.flush()
            self._audit(db, run.id, "run_created", {"goal": matter.goal, "task_type": task_type})
            db.commit()
            return state
        except Exception:
            db.rollback()
            raise
        finally:
            db.close()

    def find_active_run(self, matter_id: str, client_id: str, task_type: str) -> Optional[AgentState]:
        """复用同一案件尚未结束的 Run，避免重复点击产生多个任务。"""
        terminal = {RunStatus.COMPLETED.value, RunStatus.FAILED.value, RunStatus.CANCELLED.value}
        db = SessionLocal()
        try:
            runs = db.query(AgentRun).filter(
                AgentRun.matter_id == matter_id, AgentRun.client_id == client_id,
            ).order_by(AgentRun.created_at.desc()).all()
            for run in runs:
                raw = run.state_json or {}
                if raw.get("task_type") == task_type and run.status not in terminal:
                    return AgentState.model_validate(raw)
            return None
        finally:
            db.close()

    def load_state(self, run_id: str, client_id: str) -> AgentState:
        """按运行 ID 恢复状态，并强制校验匿名客户端归属。"""
        db = SessionLocal()
        try:
            run = db.get(AgentRun, run_id)
            if run is None:
                raise AgentRuntimeError("Agent 任务不存在", ErrorCode.RUN_NOT_FOUND.value)
            if run.client_id != client_id:
                raise AgentRuntimeError("无权访问该 Agent 任务", ErrorCode.FORBIDDEN.value)
            return AgentState.model_validate(run.state_json)
        finally:
            db.close()

    def save_state(self, state: AgentState, event_type: str, detail: Optional[Dict] = None) -> None:
        """原子保存运行快照和对应审计事件。"""
        db = SessionLocal()
        try:
            run = db.get(AgentRun, state.run_id)
            run.status = state.status.value if hasattr(state.status, "value") else state.status
            run.current_step_id = state.current_step_id
            run.pending_approval_id = state.pending_approval_id
            run.error_code = state.error_code
            run.state_json = state.model_dump(mode="json")
            self._audit(db, state.run_id, event_type, detail or {})
            db.commit()
        except Exception:
            db.rollback()
            raise
        finally:
            db.close()

    def create_step(self, state: AgentState) -> str:
        """创建阶段 1 的模拟计划步骤。"""
        db = SessionLocal()
        try:
            step_id = _id("step")
            db.add(AgentStep(
                id=step_id, run_id=state.run_id, sequence=1, name="生成模拟案件摘要",
                status=StepStatus.PENDING.value, tool_name="mock_case_summary",
            ))
            self._audit(db, state.run_id, "plan_created", {"step_id": step_id})
            db.commit()
            return step_id
        finally:
            db.close()

    def create_plan_steps(self, state: AgentState, steps: List[Dict], input_fingerprint: str) -> List[str]:
        """把不可变计划版本与对应步骤写入数据库。"""
        db = SessionLocal()
        try:
            existing = db.query(AgentPlan).filter(AgentPlan.run_id == state.run_id, AgentPlan.input_fingerprint == input_fingerprint).order_by(AgentPlan.version.desc()).first()
            if existing:
                return [row.id for row in db.query(AgentStep).filter(
                    AgentStep.run_id == state.run_id, AgentStep.plan_id == existing.id,
                ).order_by(AgentStep.sequence).all()]
            state.plan_version = (db.query(AgentPlan).filter(AgentPlan.run_id == state.run_id).count() + 1)
            plan_id = _id("plan")
            db.add(AgentPlan(id=plan_id, run_id=state.run_id, version=state.plan_version, task_type=state.task_type, input_fingerprint=input_fingerprint, plan_json=steps))
            ids = []
            for sequence, item in enumerate(steps, start=1):
                step_id = _id("step")
                ids.append(step_id)
                db.add(AgentStep(
                    id=step_id, run_id=state.run_id, sequence=sequence,
                    name=item["name"], status=StepStatus.PENDING.value,
                    tool_name=item.get("tool_name"), plan_id=plan_id, plan_version=state.plan_version,
                ))
            self._audit(db, state.run_id, "plan_created", {
                "plan_version": state.plan_version, "step_ids": ids,
            })
            db.commit()
            return ids
        except Exception:
            db.rollback()
            raise
        finally:
            db.close()

    def persist_plan_revision(self, state: AgentState, revision: PlanRevision) -> List[str]:
        """保存不可变 Plan revision；同输入重复调用只复用，不覆盖旧记录。"""
        db = SessionLocal()
        try:
            existing = db.query(AgentPlan).filter(
                AgentPlan.run_id == state.run_id,
                AgentPlan.template_id == revision.template_id,
                AgentPlan.template_version == revision.template_version,
                AgentPlan.input_fingerprint == revision.input_fingerprint,
            ).order_by(AgentPlan.version.desc()).first()
            if existing:
                state.plan_id = existing.id
                state.plan_version = existing.version
                state.plan_revision = existing.version
                state.domain_id = existing.domain_id
                state.template_id = existing.template_id
                state.template_version = existing.template_version
                return [row.id for row in db.query(AgentStep).filter(
                    AgentStep.run_id == state.run_id,
                    AgentStep.plan_id == existing.id,
                ).order_by(AgentStep.sequence).all()]

            latest = db.query(AgentPlan).filter(AgentPlan.run_id == state.run_id).order_by(AgentPlan.version.desc()).first()
            version = (latest.version + 1) if latest else 1
            plan_id = _id("plan")
            revision.plan_id = plan_id
            revision.plan_revision = version
            revision.parent_plan_id = latest.id if latest else None
            db.add(AgentPlan(
                id=plan_id,
                run_id=state.run_id,
                version=version,
                task_type=state.task_type,
                domain_id=revision.domain_id,
                template_id=revision.template_id,
                template_version=revision.template_version,
                replan_reason=revision.replan_reason,
                triggered_by=revision.triggered_by,
                parent_plan_id=revision.parent_plan_id,
                input_fingerprint=revision.input_fingerprint,
                plan_json=revision.model_dump(mode="json"),
            ))
            ids: List[str] = []
            for sequence, item in enumerate(revision.steps, start=1):
                step_id = _id("step")
                ids.append(step_id)
                db.add(AgentStep(
                    id=step_id,
                    run_id=state.run_id,
                    sequence=sequence,
                    name=item.name,
                    status=item.status,
                    tool_name=item.tool_name,
                    plan_id=plan_id,
                    plan_version=version,
                    template_step_id=item.step_id,
                    step_type=item.step_type,
                    requires_approval=item.requires_approval,
                    verification_policy_ids=item.verification_policy_ids,
                    skip_reason=item.skip_reason,
                ))
            state.plan_id = plan_id
            state.plan_version = version
            state.plan_revision = version
            state.domain_id = revision.domain_id
            state.template_id = revision.template_id
            state.template_version = revision.template_version
            state.replan_reason = revision.replan_reason
            self._audit(db, state.run_id, "plan_revision_created", {
                "plan_id": plan_id,
                "plan_revision": version,
                "template_id": revision.template_id,
                "template_version": revision.template_version,
                "replan_reason": revision.replan_reason,
                "step_ids": ids,
            })
            db.commit()
            return ids
        except Exception:
            db.rollback()
            raise
        finally:
            db.close()

    def get_step(self, run_id: str, sequence: int, plan_version: Optional[int] = None) -> AgentStep:
        """按稳定序号读取当前计划步骤。"""
        db = SessionLocal()
        try:
            query = db.query(AgentStep).filter(AgentStep.run_id == run_id, AgentStep.sequence == sequence)
            step = query.filter(AgentStep.plan_version == plan_version).first() if plan_version else query.order_by(AgentStep.plan_version.desc()).first()
            if step is None:
                raise AgentRuntimeError("Agent 计划步骤不存在", ErrorCode.INVALID_STATE.value)
            db.expunge(step)
            return step
        finally:
            db.close()

    def set_step_status(self, run_id: str, step_id: str, status: StepStatus, error_code: Optional[str] = None) -> None:
        """更新步骤状态，并维护开始/结束时间。"""
        db = SessionLocal()
        try:
            step = db.get(AgentStep, step_id)
            step.status = status.value
            step.error_code = error_code
            now = datetime.now(timezone.utc)
            if status == StepStatus.RUNNING:
                step.started_at = now
            if status in {StepStatus.COMPLETED, StepStatus.FAILED, StepStatus.CANCELLED, StepStatus.SKIPPED}:
                step.completed_at = now
            self._audit(db, run_id, "step_status_changed", {"step_id": step_id, "status": status.value})
            db.commit()
        finally:
            db.close()

    def save_step_runtime(self, run_id: str, step_id: str, *, observation=None, verification=None, decision=None) -> None:
        """分别保存观察、验证和决策，避免 Verifier 直接修改 Run 状态。"""
        db = SessionLocal()
        try:
            step = db.get(AgentStep, step_id)
            if step is None or step.run_id != run_id:
                raise AgentRuntimeError("Agent 计划步骤不存在", ErrorCode.INVALID_STATE.value)
            if observation is not None:
                step.observation_json = observation
            if verification is not None:
                step.verification_json = verification
            if decision is not None:
                step.decision_json = decision
            self._audit(db, run_id, "step_runtime_recorded", {
                "step_id": step_id,
                "has_observation": observation is not None,
                "has_verification": verification is not None,
                "decision": (decision or {}).get("action"),
            })
            db.commit()
        except Exception:
            db.rollback()
            raise
        finally:
            db.close()

    def save_tool_call(self, state: AgentState, attempt: int, arguments: Dict, result: ToolResult, tool_name: str = "mock_case_summary") -> None:
        """保存每一次工具尝试；失败重试不会覆盖前一次记录。"""
        db = SessionLocal()
        try:
            db.add(ToolCall(
                id=result.tool_call_id, run_id=state.run_id, step_id=state.current_step_id,
                tool_name=tool_name, status="completed" if result.success else "failed",
                attempt=attempt, input_json=arguments, result_json=result.model_dump(mode="json"),
                error_code=result.error_code, error_message=result.error_message,
                completed_at=datetime.now(timezone.utc),
            ))
            self._audit(db, state.run_id, "tool_called", {
                "tool_call_id": result.tool_call_id, "tool_name": tool_name,
                "attempt": attempt, "success": result.success,
                "error_code": result.error_code,
            })
            db.commit()
        finally:
            db.close()

    def create_approval(self, state: AgentState, prompt: str = "模拟案件摘要已生成，是否确认完成该任务？") -> str:
        """创建有效期 24 小时的待审批记录。"""
        db = SessionLocal()
        try:
            approval_id = _id("approval")
            db.add(ApprovalRequest(
                id=approval_id, run_id=state.run_id, client_id=state.client_id,
                prompt=prompt,
                expires_at=datetime.now(timezone.utc) + timedelta(hours=24),
            ))
            self._audit(db, state.run_id, "approval_requested", {"approval_id": approval_id})
            db.commit()
            return approval_id
        finally:
            db.close()

    def decide_approval(self, state: AgentState, approved: bool) -> None:
        """校验归属、状态和有效期后记录用户决定。"""
        db = SessionLocal()
        try:
            approval = db.get(ApprovalRequest, state.pending_approval_id)
            if approval is None or approval.run_id != state.run_id or approval.client_id != state.client_id:
                raise AgentRuntimeError("审批不存在或无权操作", ErrorCode.FORBIDDEN.value)
            now = datetime.now(timezone.utc)
            if approval.status != "pending":
                raise AgentRuntimeError("审批已经处理", ErrorCode.INVALID_STATE.value)
            # 过期审批不得继续驱动状态机，必须由用户重新发起任务。
            if approval.expires_at < now:
                approval.status = "expired"
                db.commit()
                raise AgentRuntimeError("审批已过期", ErrorCode.APPROVAL_EXPIRED.value)
            approval.status = "approved" if approved else "rejected"
            approval.decision = approval.status
            approval.decided_at = now
            self._audit(db, state.run_id, "approval_decided", {"approved": approved})
            db.commit()
        finally:
            db.close()

    def cancel(self, state: AgentState) -> AgentState:
        """将运行及当前步骤统一标记为取消。"""
        state.status = RunStatus.CANCELLED
        state.error_code = ErrorCode.RUN_CANCELLED.value
        if state.current_step_id:
            db = SessionLocal()
            try:
                step = db.get(AgentStep, state.current_step_id)
                should_cancel = step is not None and step.status not in {
                    StepStatus.COMPLETED.value, StepStatus.FAILED.value, StepStatus.CANCELLED.value,
                }
            finally:
                db.close()
            # 劳动纠纷审批发生在分析步骤完成后，拒绝草稿不能回写污染已完成步骤。
            if should_cancel:
                self.set_step_status(state.run_id, state.current_step_id, StepStatus.CANCELLED)
        self.save_state(state, "run_cancelled")
        return state

    def snapshot(self, run_id: str, client_id: str) -> Dict:
        """组装前端需要的运行、步骤、审批和结果快照。"""
        db = SessionLocal()
        try:
            run = db.get(AgentRun, run_id)
            if run is None:
                raise AgentRuntimeError("Agent 任务不存在", ErrorCode.RUN_NOT_FOUND.value)
            if run.client_id != client_id:
                raise AgentRuntimeError("无权访问该 Agent 任务", ErrorCode.FORBIDDEN.value)
            plan_version = (run.state_json or {}).get("plan_version", 0)
            step_query = db.query(AgentStep).filter(AgentStep.run_id == run_id)
            if plan_version:
                step_query = step_query.filter(AgentStep.plan_version == plan_version)
            steps = step_query.order_by(AgentStep.sequence).all()
            plan_id = (run.state_json or {}).get("plan_id")
            current_plan = db.get(AgentPlan, plan_id) if plan_id else None
            raw_plan_payload = current_plan.plan_json if current_plan else None
            plan_payload = dict(raw_plan_payload) if isinstance(raw_plan_payload, dict) else {}
            planned_steps = list(plan_payload.get("steps") or [])
            approval = db.get(ApprovalRequest, run.pending_approval_id) if run.pending_approval_id else None
            return {
                "run_id": run.id, "matter_id": run.matter_id, "status": run.status,
                "current_step_id": run.current_step_id,
                "steps": [{
                    "id": s.id, "name": s.name, "status": s.status, "tool_name": s.tool_name,
                    "step_type": s.step_type, "skip_reason": s.skip_reason,
                    "triggered_by_tags": (
                        planned_steps[index].get("triggered_by_tags", [])
                        if index < len(planned_steps) else []
                    ),
                    "requires_approval": bool(s.requires_approval),
                    "verification_policy_ids": list(s.verification_policy_ids or []),
                    "observation": s.observation_json, "verification": s.verification_json,
                    "decision": s.decision_json,
                } for index, s in enumerate(steps)],
                "approval": ({"id": approval.id, "prompt": approval.prompt, "status": approval.status} if approval else None),
                "task_type": (run.state_json or {}).get("task_type", "mock_case_summary"),
                "domain_id": (run.state_json or {}).get("domain_id"),
                "template_id": (run.state_json or {}).get("template_id"),
                "template_version": (run.state_json or {}).get("template_version"),
                "plan_id": plan_id,
                "plan_revision": (run.state_json or {}).get("plan_revision", plan_version),
                "replan_reason": (run.state_json or {}).get("replan_reason"),
                "dispute_tags": list(plan_payload.get("dispute_tags") or []),
                "composition_version": plan_payload.get("composition_version"),
                "plan_version": (run.state_json or {}).get("plan_version", 0),
                "missing_facts": (run.state_json or {}).get("missing_facts", []),
                "questions": (run.state_json or {}).get("questions", []),
                "blocked_reason": (run.state_json or {}).get("blocked_reason"),
                "final_artifact_ids": (run.state_json or {}).get("final_artifact_ids", []),
                "max_steps": (run.state_json or {}).get("max_steps", 6),
                "max_tool_calls": (run.state_json or {}).get("max_tool_calls", 8),
                "tool_call_count": (run.state_json or {}).get("tool_call_count", 0),
                "budget_wallclock_seconds": (run.state_json or {}).get("budget_wallclock_seconds", 300),
                "budget_tokens": (run.state_json or {}).get("budget_tokens", 12000),
                "token_usage": (run.state_json or {}).get("token_usage", 0),
                "budget_cost_cents": (run.state_json or {}).get("budget_cost_cents", 100),
                "cost_cents": (run.state_json or {}).get("cost_cents", 0),
                "final_output": (run.state_json or {}).get("final_output"), "error_code": run.error_code,
            }
        finally:
            db.close()

    def audit_events(self, run_id: str, client_id: str):
        """按发生顺序读取审计事件，读取前先复用归属校验。"""
        self.load_state(run_id, client_id)
        db = SessionLocal()
        try:
            events = db.query(AgentAuditEvent).filter(AgentAuditEvent.run_id == run_id).order_by(AgentAuditEvent.created_at, AgentAuditEvent.id).all()
            return [{"id": e.id, "type": e.event_type, "detail": e.detail_json, "created_at": e.created_at.isoformat() if e.created_at else None} for e in events]
        finally:
            db.close()

    def begin_action(self, run_id: str, key: str, action: str, payload: Dict):
        payload_hash = hashlib.sha256(json.dumps(payload, ensure_ascii=False, sort_keys=True).encode()).hexdigest()
        db = SessionLocal()
        try:
            existing = db.query(AgentRunAction).filter(AgentRunAction.run_id == run_id, AgentRunAction.idempotency_key == key).first()
            if existing:
                if existing.payload_hash != payload_hash or existing.action != action:
                    raise AgentRuntimeError("幂等键已用于不同请求", "IDEMPOTENCY_CONFLICT")
                if existing.response_json is None:
                    raise AgentRuntimeError("同一请求正在处理中", "ACTION_IN_PROGRESS")
                return existing.response_json
            db.add(AgentRunAction(id=_id("action"), run_id=run_id, idempotency_key=key, action=action, payload_hash=payload_hash))
            db.commit()
            return None
        finally:
            db.close()

    def finish_action(self, run_id: str, key: str, response: Dict):
        db = SessionLocal()
        try:
            row = db.query(AgentRunAction).filter(AgentRunAction.run_id == run_id, AgentRunAction.idempotency_key == key).one()
            row.response_json = response
            db.commit()
        finally:
            db.close()

    @staticmethod
    def _audit(db, run_id: str, event_type: str, detail: Dict) -> None:
        """在调用方事务中追加审计事件，保证业务状态与日志一致提交。"""
        db.add(AgentAuditEvent(id=_id("audit"), run_id=run_id, event_type=event_type, detail_json=detail))
        db.add(AgentEventOutbox(id=_id("event"), run_id=run_id, event_type=event_type, payload_json=detail))
"""Agent Runtime 的 PostgreSQL 持久化仓储。

所有公开方法自行管理短事务，避免在 LangGraph 节点之间长期持有数据库连接。
"""
