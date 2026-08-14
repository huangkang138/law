"""Session、Matter、Triage与Run的服务端恢复投影。"""

import uuid
from datetime import datetime
from typing import Dict, Optional

from core.database import SessionLocal
from legal_agent_system import get_legal_agent_facade
from legal_agent_system.models import LaborCaseTriage
from models.db_models import (
    AgentRun,
    ConversationWorkspaceState,
    DigitalHumanSession,
    Matter,
)

from .presenter import present_conversation_state


def _activity_value(value: Optional[datetime]) -> float:
    return value.timestamp() if value is not None else 0.0


class ConversationWorkspaceService:
    """维护当前Matter指针，并生成不复制Runtime的恢复快照。"""

    def create_session(self, client_id: str, title: str = "新案件会话") -> Dict:
        """为尚未聊天的工作台创建可恢复Session，不触发LLM或业务Agent。"""
        session_id = f"dh_{uuid.uuid4().hex}"
        db = SessionLocal()
        try:
            db.add(DigitalHumanSession(
                id=session_id,
                user_id=client_id,
                title=title[:30],
                is_active=True,
            ))
            db.flush()
            db.add(ConversationWorkspaceState(
                session_id=session_id,
                version=0,
            ))
            db.commit()
        except Exception:
            db.rollback()
            raise
        finally:
            db.close()
        return self.get_context(session_id, client_id)

    def select_matter(
        self,
        session_id: str,
        matter_id: Optional[str],
        client_id: str,
        expected_version: Optional[int] = None,
    ) -> Dict:
        db = SessionLocal()
        try:
            session = self._owned_session(
                db,
                session_id,
                client_id,
                for_update=True,
            )
            matter = None
            if matter_id is not None:
                matter = (
                    db.query(Matter)
                    .filter(Matter.id == matter_id)
                    .with_for_update()
                    .first()
                )
                if matter is None or matter.status != "active":
                    raise LookupError("案件工作区不存在")
                if matter.client_id != client_id:
                    raise PermissionError("案件不属于当前数字人会话")
                if matter.session_id is None:
                    matter.session_id = session.id
                elif matter.session_id != session.id:
                    raise PermissionError("案件不属于当前数字人会话")
            state = db.get(ConversationWorkspaceState, session_id)
            if state is None:
                state = ConversationWorkspaceState(session_id=session_id, version=0)
                db.add(state)
            current_version = int(state.version or 0)
            selected_id = matter.id if matter is not None else None
            if state.active_matter_id != selected_id:
                if (
                    expected_version is not None
                    and expected_version != current_version
                ):
                    raise WorkspaceVersionConflict(current_version)
                state.active_matter_id = selected_id
                state.version = current_version + 1
            db.commit()
        except Exception:
            db.rollback()
            raise
        finally:
            db.close()
        return self.get_context(session_id, client_id)

    def get_version(self, session_id: str, client_id: str) -> int:
        """在线性化边界内读取当前Workspace版本。"""
        db = SessionLocal()
        try:
            self._owned_session(
                db,
                session_id,
                client_id,
                for_update=True,
            )
            state = db.get(ConversationWorkspaceState, session_id)
            return int(state.version or 0) if state is not None else 0
        finally:
            db.close()

    def resolve_active_matter_id(
        self,
        session_id: str,
        client_id: str,
    ) -> Optional[str]:
        db = SessionLocal()
        try:
            self._owned_session(
                db,
                session_id,
                client_id,
                for_update=True,
            )
            _, matter, changed = self._resolve_state_and_matter(
                db,
                session_id,
                client_id,
            )
            if changed:
                db.commit()
            return matter.id if matter is not None else None
        except Exception:
            db.rollback()
            raise
        finally:
            db.close()

    def get_context(self, session_id: str, client_id: str) -> Dict:
        matter_data = None
        triage_data = None
        run_id = None
        db = SessionLocal()
        try:
            self._owned_session(
                db,
                session_id,
                client_id,
                for_update=True,
            )
            state, matter, changed = self._resolve_state_and_matter(
                db,
                session_id,
                client_id,
            )
            state_version = int(state.version or 0)
            if matter is not None:
                matter_data = {
                    "matter_id": matter.id,
                    "session_id": matter.session_id,
                    "title": matter.title,
                    "goal": matter.goal,
                }
                triage = db.get(LaborCaseTriage, matter.id)
                if triage is not None:
                    if triage.client_id != client_id:
                        raise PermissionError("无权访问该劳动案件分流")
                    triage_data = {
                        "matter_id": triage.matter_id,
                        "facts": dict(triage.facts_json or {}),
                        "result": dict(triage.result_json or {}),
                        "version": int(triage.version or 0),
                    }
                run = (
                    db.query(AgentRun)
                    .filter(
                        AgentRun.matter_id == matter.id,
                        AgentRun.client_id == client_id,
                    )
                    .order_by(AgentRun.updated_at.desc(), AgentRun.created_at.desc())
                    .first()
                )
                run_id = run.id if run is not None else None
            if changed:
                db.commit()
        except Exception:
            db.rollback()
            raise
        finally:
            db.close()

        run_data = (
            get_legal_agent_facade().get_run(run_id, client_id)
            if run_id is not None
            else None
        )
        return {
            "session_id": session_id,
            "workspace_version": state_version,
            "matter": matter_data,
            "triage": triage_data,
            "run": run_data,
            "presentation": present_conversation_state(
                matter_data,
                triage_data,
                run_data,
            ),
        }

    def _resolve_state_and_matter(
        self,
        db,
        session_id: str,
        client_id: str,
    ):
        """在已锁定Session的事务内解析指针，保留显式清空语义。"""
        state = db.get(ConversationWorkspaceState, session_id)
        if state is not None and state.active_matter_id is None:
            return state, None, False
        if state is not None:
            matter = db.get(Matter, state.active_matter_id)
            if (
                matter is not None
                and matter.client_id == client_id
                and matter.session_id == session_id
                and matter.status == "active"
            ):
                return state, matter, False

        matter = self._latest_matter(db, session_id, client_id)
        if state is None:
            state = ConversationWorkspaceState(
                session_id=session_id,
                version=0,
            )
            db.add(state)
        selected_id = matter.id if matter is not None else None
        if state.active_matter_id != selected_id:
            state.active_matter_id = selected_id
            state.version = int(state.version or 0) + 1
        return state, matter, True

    def delete_matter(self, matter_id: str, client_id: str) -> Dict:
        """在同一事务中删除Matter并维护受影响Session的当前指针。"""
        db = SessionLocal()
        try:
            matter = db.get(Matter, matter_id)
            if matter is None:
                raise LookupError("Matter 不存在")
            if matter.client_id != client_id:
                raise PermissionError("无权访问该 Matter")
            if matter.session_id is not None:
                self._owned_session(
                    db,
                    matter.session_id,
                    client_id,
                    for_update=True,
                )
            matter = (
                db.query(Matter)
                .filter(Matter.id == matter_id)
                .populate_existing()
                .with_for_update()
                .first()
            )
            if matter is None:
                raise LookupError("Matter 不存在")
            states = (
                db.query(ConversationWorkspaceState)
                .join(
                    DigitalHumanSession,
                    DigitalHumanSession.id == ConversationWorkspaceState.session_id,
                )
                .filter(
                    ConversationWorkspaceState.active_matter_id == matter_id,
                    DigitalHumanSession.user_id == client_id,
                )
                .all()
            )
            for state in states:
                fallback = self._latest_matter(
                    db,
                    state.session_id,
                    client_id,
                    exclude_matter_id=matter_id,
                )
                state.active_matter_id = (
                    fallback.id if fallback is not None else None
                )
                state.version = int(state.version or 0) + 1
            db.delete(matter)
            db.commit()
            return {"matter_id": matter_id}
        except Exception:
            db.rollback()
            raise
        finally:
            db.close()

    @staticmethod
    def _owned_session(
        db,
        session_id: str,
        client_id: str,
        *,
        for_update: bool = False,
    ) -> DigitalHumanSession:
        query = db.query(DigitalHumanSession).filter(
            DigitalHumanSession.id == session_id
        )
        if for_update:
            query = query.with_for_update()
        session = query.first()
        if session is None or not session.is_active:
            raise LookupError("数字人会话不存在")
        if session.user_id != client_id:
            raise PermissionError("无权访问该数字人会话")
        return session

    @staticmethod
    def _latest_matter(
        db,
        session_id: str,
        client_id: str,
        *,
        exclude_matter_id: Optional[str] = None,
    ):
        query = db.query(Matter).filter(
            Matter.session_id == session_id,
            Matter.client_id == client_id,
            Matter.status == "active",
        )
        if exclude_matter_id is not None:
            query = query.filter(Matter.id != exclude_matter_id)
        matters = query.all()
        if not matters:
            return None
        ids = [item.id for item in matters]
        runs = db.query(AgentRun).filter(AgentRun.matter_id.in_(ids)).all()
        triages = db.query(LaborCaseTriage).filter(
            LaborCaseTriage.matter_id.in_(ids)
        ).all()
        activity = {
            item.id: max(_activity_value(item.updated_at), _activity_value(item.created_at))
            for item in matters
        }
        for item in runs:
            activity[item.matter_id] = max(
                activity.get(item.matter_id, 0.0),
                _activity_value(item.updated_at),
                _activity_value(item.created_at),
            )
        for item in triages:
            activity[item.matter_id] = max(
                activity.get(item.matter_id, 0.0),
                _activity_value(item.updated_at),
                _activity_value(item.created_at),
            )
        return max(matters, key=lambda item: (activity[item.id], item.id))


_workspace_service = ConversationWorkspaceService()


class WorkspaceVersionConflict(Exception):
    """客户端基于过期 Workspace 版本提交选择。"""

    def __init__(self, current_version: int):
        super().__init__("案件工作台已在其他位置更新，请刷新后重试")
        self.current_version = current_version


def get_conversation_workspace_service() -> ConversationWorkspaceService:
    return _workspace_service
