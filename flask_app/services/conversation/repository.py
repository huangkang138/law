"""会话原始消息、记忆和请求幂等的数据访问。"""

import json
import uuid
from datetime import datetime, timedelta, timezone
from typing import Dict, List, Optional, Tuple

from core.database import SessionLocal
from models.db_models import (
    AgentRun,
    ConversationMemory,
    DigitalHumanMessage,
    DigitalHumanRequest,
    DigitalHumanSession,
    Matter,
)

from .cancel import CANCELLED_STATUSES, ConversationCancelled
from .schemas import MemorySnapshot
from .token_budget import TokenBudget


class RequestInProgress(RuntimeError):
    pass


class ConversationRepository:
    ACTIVE_STATUSES = {"processing", "action_running", "action_completed"}
    # cancelling 仍在解除过程中，会话级活跃冲突必须把它计入，防止并发重跑。
    IN_FLIGHT_STATUSES = ACTIVE_STATUSES | {"cancelling"}
    # complete_request 只允许从这两个状态落 completed：
    # cancelling/cancelled 说明取消已在完成窗口内到达，必须拒绝覆盖。
    ALLOWED_COMPLETE_STATUSES = {"processing", "action_completed"}
    LEASE_DURATION = timedelta(minutes=15)

    def __init__(self, token_budget: Optional[TokenBudget] = None) -> None:
        self.token_budget = token_budget or TokenBudget()

    def begin_request(
        self,
        request_id: str,
        client_id: str,
        session_id: str,
        question: str,
    ) -> Tuple[Optional[Dict], Optional[str], Optional[str]]:
        db = SessionLocal()
        try:
            now = datetime.now(timezone.utc)
            record = db.get(DigitalHumanRequest, request_id)
            if record is not None:
                if record.client_id != client_id:
                    raise PermissionError("无权访问该请求")
                if record.session_id != session_id:
                    raise PermissionError("请求不属于该会话")
                if record.status == "completed" and record.response_json:
                    return json.loads(record.response_json), None, None
                if (
                    record.lease_token is None
                    and record.status in self.ACTIVE_STATUSES
                    and not record.checkpoint_json
                ):
                    raise RequestInProgress("旧请求缺少恢复检查点，禁止自动重复执行")
                if (
                    record.status in self.ACTIVE_STATUSES
                    and record.lease_expires_at is not None
                    and record.lease_expires_at > now
                ):
                    raise RequestInProgress("该请求正在处理中")
                if (
                    record.status == "cancelling"
                    and record.lease_expires_at is not None
                    and record.lease_expires_at > now
                ):
                    raise ConversationCancelled("该请求正在停止")
                other_active = (
                    db.query(DigitalHumanRequest.request_id)
                    .filter(
                        DigitalHumanRequest.session_id == session_id,
                        DigitalHumanRequest.request_id != request_id,
                        DigitalHumanRequest.status.in_(self.IN_FLIGHT_STATUSES),
                        (
                            DigitalHumanRequest.lease_expires_at.is_(None)
                            | (DigitalHumanRequest.lease_expires_at > now)
                        ),
                    )
                    .first()
                )
                if other_active is not None:
                    raise RequestInProgress("该会话正在处理另一条消息，请稍后重试")
                if record.status in {"cancelling", "cancelled"}:
                    # 取消后的重试：动作阶段按检查点幂等恢复，LLM 阶段重新执行。
                    record.status = (
                        "action_running" if record.checkpoint_json else "processing"
                    )
                elif record.status == "retryable":
                    record.status = "processing"
                elif record.status == "action_retryable":
                    record.status = "action_running"
                lease_token = uuid.uuid4().hex
                record.lease_token = lease_token
                record.lease_expires_at = now + self.LEASE_DURATION
                message = (
                    db.query(DigitalHumanMessage)
                    .filter(
                        DigitalHumanMessage.request_id == request_id,
                        DigitalHumanMessage.role == "user",
                    )
                    .first()
                )
                if message is None:
                    raise LookupError("请求对应的用户消息不存在")
                if message.content != question:
                    raise ValueError("相同 request_id 不能对应不同问题")
                db.commit()
                return None, message.id, lease_token

            active = (
                db.query(DigitalHumanRequest.request_id)
                .filter(
                    DigitalHumanRequest.session_id == session_id,
                    DigitalHumanRequest.status.in_(self.IN_FLIGHT_STATUSES),
                    (
                        DigitalHumanRequest.lease_expires_at.is_(None)
                        | (DigitalHumanRequest.lease_expires_at > now)
                    ),
                )
                .first()
            )
            if active is not None:
                raise RequestInProgress("该会话正在处理另一条消息，请稍后重试")

            session = db.get(DigitalHumanSession, session_id)
            if session is None:
                session = DigitalHumanSession(
                    id=session_id,
                    user_id=client_id,
                    title=question[:30],
                    is_active=True,
                )
                db.add(session)
                db.flush()
            elif session.user_id != client_id:
                raise PermissionError("无权访问该数字人会话")
            else:
                session.is_active = True
                session.updated_at = now

            message_id = f"dhmsg_{uuid.uuid4().hex}"
            lease_token = uuid.uuid4().hex
            db.add(DigitalHumanRequest(
                request_id=request_id,
                client_id=client_id,
                session_id=session_id,
                status="processing",
                lease_token=lease_token,
                lease_expires_at=now + self.LEASE_DURATION,
            ))
            db.add(DigitalHumanMessage(
                id=message_id,
                session_id=session_id,
                request_id=request_id,
                role="user",
                content=question,
                estimated_tokens=self.token_budget.estimate(question),
                created_at=now,
            ))
            db.commit()
            return None, message_id, lease_token
        except Exception:
            db.rollback()
            raise
        finally:
            db.close()

    @staticmethod
    def load_request_checkpoint(request_id: str) -> Dict:
        db = SessionLocal()
        try:
            record = db.get(DigitalHumanRequest, request_id)
            if record is None:
                raise LookupError("数字人请求不存在")
            return {
                "status": record.status,
                "action_type": record.action_type,
                "resources": dict(record.action_resource_json or {}),
                "checkpoint": dict(record.checkpoint_json or {}),
            }
        finally:
            db.close()

    @staticmethod
    def mark_action_started(
        request_id: str,
        lease_token: str,
        action_type: str,
        resources: Dict,
        checkpoint: Dict,
    ) -> None:
        db = SessionLocal()
        try:
            record = db.get(DigitalHumanRequest, request_id)
            if record is None:
                raise LookupError("数字人请求不存在")
            ConversationRepository._assert_lease(record, lease_token)
            if record.status not in {"processing", "retryable", "action_running"}:
                raise RequestInProgress("请求状态不允许开始业务动作")
            record.status = "action_running"
            record.action_type = action_type
            record.action_resource_json = dict(resources)
            record.checkpoint_json = dict(checkpoint)
            record.lease_expires_at = (
                datetime.now(timezone.utc) + ConversationRepository.LEASE_DURATION
            )
            db.commit()
        except Exception:
            db.rollback()
            raise
        finally:
            db.close()

    @staticmethod
    def update_action_resource(
        request_id: str,
        lease_token: str,
        **resources,
    ) -> None:
        db = SessionLocal()
        try:
            record = db.get(DigitalHumanRequest, request_id)
            if record is None:
                raise LookupError("数字人请求不存在")
            ConversationRepository._assert_lease(record, lease_token)
            if record.status != "action_running":
                raise RequestInProgress("请求当前不在业务动作执行阶段")
            merged = dict(record.action_resource_json or {})
            merged.update({
                key: value for key, value in resources.items()
                if value is not None
            })
            record.action_resource_json = merged
            record.lease_expires_at = (
                datetime.now(timezone.utc) + ConversationRepository.LEASE_DURATION
            )
            db.commit()
        except Exception:
            db.rollback()
            raise
        finally:
            db.close()

    @staticmethod
    def mark_action_completed(
        request_id: str,
        lease_token: str,
        resources: Dict,
        checkpoint: Dict,
    ) -> None:
        db = SessionLocal()
        try:
            record = db.get(DigitalHumanRequest, request_id)
            if record is None:
                raise LookupError("数字人请求不存在")
            ConversationRepository._assert_lease(record, lease_token)
            if record.status not in {"action_running", "action_completed"}:
                raise RequestInProgress("请求状态不允许完成业务动作")
            record.status = "action_completed"
            record.action_resource_json = dict(resources)
            record.checkpoint_json = dict(checkpoint)
            record.lease_expires_at = (
                datetime.now(timezone.utc) + ConversationRepository.LEASE_DURATION
            )
            db.commit()
        except Exception:
            db.rollback()
            raise
        finally:
            db.close()

    @staticmethod
    def mark_retryable(request_id: str, lease_token: Optional[str] = None) -> None:
        db = SessionLocal()
        try:
            record = db.get(DigitalHumanRequest, request_id)
            if record is not None:
                if lease_token is not None:
                    ConversationRepository._assert_lease(record, lease_token)
                if record.status == "processing":
                    record.status = "retryable"
                elif record.status == "action_running":
                    record.status = "action_retryable"
                elif record.status == "action_completed":
                    pass
                else:
                    return
                record.lease_token = None
                record.lease_expires_at = None
                db.commit()
        except Exception:
            db.rollback()
            raise
        finally:
            db.close()

    @staticmethod
    def mark_cancelling(
        request_id: str,
        lease_token: Optional[str] = None,
    ) -> Optional[str]:
        """ACTIVE → cancelling，保留租约与检查点；返回最新 status。

        取消端点拿不到租约（租约不暴露给客户端），因此 lease_token 可选；
        传入时才执行租约断言。已 cancelling 幂等；终态不改。
        """
        db = SessionLocal()
        try:
            record = db.get(DigitalHumanRequest, request_id)
            if record is None:
                raise LookupError("数字人请求不存在")
            if lease_token is not None:
                ConversationRepository._assert_lease(record, lease_token)#防止“过期执行者”回来乱写状态
            if record.status in ConversationRepository.ACTIVE_STATUSES:
                record.status = "cancelling"
                db.commit()
            return record.status
        except Exception:
            db.rollback()
            raise
        finally:
            db.close()

    @staticmethod
    def mark_cancelled(request_id: str, lease_token: str) -> None:
        """取消终态：租约断言后置 cancelled、清租约，保留检查点与资源。

        检查点（含已 checkpoint 的 matter_id/run_id）保留，
        供同 request_id 重试按 begin_request 的恢复分支幂等续作。
        来源状态仅限 processing/action_running/action_completed/cancelling；
        其余状态（如 completed 竞态已赢）幂等返回。
        """
        db = SessionLocal()
        try:
            record = db.get(DigitalHumanRequest, request_id)
            if record is None:
                raise LookupError("数字人请求不存在")
            ConversationRepository._assert_lease(record, lease_token)
            if record.status not in {
                "processing", "action_running", "action_completed", "cancelling",
            }:
                return
            record.status = "cancelled"
            record.lease_token = None
            record.lease_expires_at = None
            db.commit()
        except Exception:
            db.rollback()
            raise
        finally:
            db.close()

    @staticmethod
    def _assert_lease(record: DigitalHumanRequest, lease_token: str) -> None:
        if not lease_token or record.lease_token != lease_token:
            raise RequestInProgress("请求执行租约已失效")

    def messages(
        self,
        session_id: str,
        client_id: str,
        exclude_request_id: Optional[str] = None,
        limit: int = 200,
    ) -> List[Dict]:
        db = SessionLocal()
        try:
            session = db.get(DigitalHumanSession, session_id)
            if session is not None and session.user_id != client_id:
                raise PermissionError("无权访问该数字人会话")
            query = db.query(DigitalHumanMessage).filter(
                DigitalHumanMessage.session_id == session_id,
            )
            if exclude_request_id:
                query = query.filter(
                    (DigitalHumanMessage.request_id.is_(None))
                    | (DigitalHumanMessage.request_id != exclude_request_id)
                )
            rows = (
                query.order_by(
                    DigitalHumanMessage.created_at.desc(),
                    DigitalHumanMessage.id.desc(),
                )
                .limit(limit)
                .all()
            )
            return [{
                "id": item.id,
                "role": item.role,
                "content": item.content,
                "estimated_tokens": item.estimated_tokens,
            } for item in reversed(rows)]
        finally:
            db.close()

    def load_memory(self, session_id: str) -> MemorySnapshot:
        db = SessionLocal()
        try:
            row = db.get(ConversationMemory, session_id)
            if row is None:
                return MemorySnapshot(session_id=session_id)
            return MemorySnapshot(
                session_id=session_id,
                revision=int(row.revision or 0),
                structured=dict(row.structured_json or {}),
                summary_text=row.summary_text or "",
                summary_items=list(row.summary_items or []),
                summary_through_message_id=row.summary_through_message_id,
            )
        finally:
            db.close()

    def matter_context(self, session_id: str, client_id: str) -> Dict:
        from .workspace import get_conversation_workspace_service

        matter_id = get_conversation_workspace_service().resolve_active_matter_id(
            session_id,
            client_id,
        )
        if matter_id is None:
            return {}
        db = SessionLocal()
        try:
            matter = db.get(Matter, matter_id)
            if (
                matter is None
                or matter.session_id != session_id
                or matter.client_id != client_id
                or matter.status != "active"
            ):
                return {}
            from legal_agent_system.models import MatterFactAssertion

            assertions = (
                db.query(MatterFactAssertion)
                .filter(
                    MatterFactAssertion.matter_id == matter.id,
                    MatterFactAssertion.client_id == client_id,
                    MatterFactAssertion.confirmed_by_user.is_(True),
                )
                .order_by(MatterFactAssertion.version, MatterFactAssertion.created_at)
                .all()
            )
            confirmed = {}
            for item in assertions:
                confirmed[item.fact_key] = item.value_json
            run = (
                db.query(AgentRun)
                .filter(
                    AgentRun.matter_id == matter.id,
                    AgentRun.client_id == client_id,
                )
                .order_by(AgentRun.updated_at.desc(), AgentRun.created_at.desc())
                .first()
            )
            return {
                "matter_id": matter.id,
                "matter_goal": matter.goal,
                "confirmed_facts": confirmed,
                "run_id": run.id if run else None,
                "run_status": run.status if run else None,
                "run_error_code": run.error_code if run else None,
            }
        finally:
            db.close()

    def complete_request(
        self,
        request_id: str,
        session_id: str,
        parsed: Dict,
        result: Dict,
        memory: MemorySnapshot,
        lease_token: Optional[str] = None,
    ) -> None:
        db = SessionLocal()
        try:
            record = db.get(DigitalHumanRequest, request_id)
            if record is None:
                raise LookupError("数字人请求不存在")
            if lease_token is not None:
                self._assert_lease(record, lease_token)
            if record.status in CANCELLED_STATUSES:
                # mark_cancelling 可从 action_completed 转 cancelling：
                # 取消恰好落在动作完成与请求完成之间时，
                # 绝不能把结果写成 completed，交由 orchestrator 落 cancelled 终态。
                raise ConversationCancelled("回复已停止，未写入完成结果")
            if record.status not in self.ALLOWED_COMPLETE_STATUSES:
                raise RequestInProgress("请求状态不允许完成")
            now = datetime.now(timezone.utc)
            assistant = (
                db.query(DigitalHumanMessage)
                .filter(
                    DigitalHumanMessage.session_id == session_id,
                    DigitalHumanMessage.request_id == request_id,
                    DigitalHumanMessage.role == "assistant",
                )
                .first()
            )
            if assistant is None:
                db.add(DigitalHumanMessage(
                    id=f"dhmsg_{uuid.uuid4().hex}",
                    session_id=session_id,
                    request_id=request_id,
                    role="assistant",
                    content=parsed["reply"],
                    intent=parsed["intent"],
                    emotion=parsed["emotion"],
                    confidence=parsed["confidence"],
                    estimated_tokens=self.token_budget.estimate(parsed["reply"]),
                    created_at=now + timedelta(microseconds=1),
                ))
            row = db.get(ConversationMemory, session_id)
            if row is None:
                row = ConversationMemory(session_id=session_id)
                db.add(row)
            row.schema_version = 1
            row.revision = memory.revision
            row.structured_json = memory.structured
            row.summary_text = memory.summary_text
            row.summary_items = memory.summary_items
            row.summary_through_message_id = memory.summary_through_message_id
            record.status = "completed"
            record.response_json = json.dumps(result, ensure_ascii=False)
            record.lease_token = None
            record.lease_expires_at = None
            db.commit()
        except Exception:
            db.rollback()
            raise
        finally:
            db.close()

    @staticmethod
    def discard_request(request_id: str) -> None:
        """兼容旧调用；失败请求保留消息并允许同 request_id 恢复。"""
        ConversationRepository.mark_retryable(request_id)
