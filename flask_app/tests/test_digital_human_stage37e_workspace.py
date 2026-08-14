"""阶段3.7E会话与工作台协同专项测试。"""

import hashlib
import threading
import unittest
import uuid
from pathlib import Path
from unittest.mock import patch

from flask import Flask, jsonify
from sqlalchemy.exc import SQLAlchemyError

from core.database import Base, SessionLocal, engine
from legal_agent_system.models import LaborCaseTriage
from models.db_models import (
    AgentRun,
    ConversationWorkspaceState,
    DigitalHumanSession,
    Matter,
)
from services.conversation.presenter import present_conversation_state
from services.conversation.actions import ConversationActions
from services.conversation.repository import ConversationRepository
from services.conversation.workspace import (
    ConversationWorkspaceService,
    WorkspaceVersionConflict,
)
from services.digital_human_identity import (
    COOKIE_NAME,
    get_digital_human_client_id,
    persist_digital_human_identity,
)


class _FakeFacade:
    def __init__(self, snapshots):
        self.snapshots = snapshots

    def get_run(self, run_id, _client_id):
        return self.snapshots[run_id]


class _FakeTriageFacade:
    def __init__(self, matter_id, session_id):
        self.matter = {
            "matter_id": matter_id,
            "session_id": session_id,
        }

    def get_matter(self, _matter_id, _client_id):
        return self.matter

    def update_labor_case_triage(self, matter_id, _client_id, _facts):
        return {
            "matter_id": matter_id,
            "result": {
                "missing_facts": ["monthly_salary"],
                "questions": ["月工资是多少？"],
            },
        }


class ConversationWorkspaceTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        Base.metadata.create_all(bind=engine)

    def setUp(self):
        token = uuid.uuid4().hex
        self.client_id = f"dhc_37e_{token}"
        self.other_client_id = f"dhc_37e_other_{token}"
        self.session_id = f"dh_37e_{token}"
        self.other_session_id = f"dh_37e_other_{token}"
        self.matter_one = f"matter_37e_one_{token}"
        self.matter_two = f"matter_37e_two_{token}"
        self.run_id = f"run_37e_{token}"
        self.service = ConversationWorkspaceService()
        db = SessionLocal()
        try:
            db.add_all([
                DigitalHumanSession(
                    id=self.session_id,
                    user_id=self.client_id,
                    title="阶段3.7E测试",
                    is_active=True,
                ),
                DigitalHumanSession(
                    id=self.other_session_id,
                    user_id=self.other_client_id,
                    title="其他用户",
                    is_active=True,
                ),
                Matter(
                    id=self.matter_one,
                    client_id=self.client_id,
                    session_id=self.session_id,
                    title="案件一",
                    goal="测试案件一",
                    status="active",
                ),
                Matter(
                    id=self.matter_two,
                    client_id=self.client_id,
                    session_id=self.session_id,
                    title="案件二",
                    goal="测试案件二",
                    status="active",
                ),
            ])
            db.commit()
        finally:
            db.close()

    def tearDown(self):
        db = SessionLocal()
        try:
            db.query(ConversationWorkspaceState).filter(
                ConversationWorkspaceState.session_id.in_([
                    self.session_id,
                    self.other_session_id,
                ])
            ).delete(synchronize_session=False)
            db.query(AgentRun).filter(
                AgentRun.id == self.run_id
            ).delete(synchronize_session=False)
            db.query(LaborCaseTriage).filter(
                LaborCaseTriage.matter_id.in_([self.matter_one, self.matter_two])
            ).delete(synchronize_session=False)
            db.query(Matter).filter(
                Matter.id.in_([self.matter_one, self.matter_two])
            ).delete(synchronize_session=False)
            db.query(DigitalHumanSession).filter(
                DigitalHumanSession.id.in_([
                    self.session_id,
                    self.other_session_id,
                ])
            ).delete(synchronize_session=False)
            db.commit()
        finally:
            db.close()

    def test_select_and_restore_matter_triage_run(self):
        db = SessionLocal()
        try:
            db.add(LaborCaseTriage(
                matter_id=self.matter_one,
                client_id=self.client_id,
                facts_json={"issue_domain": "labor"},
                result_json={"missing_facts": ["monthly_salary"], "risk_level": "low"},
                version=1,
            ))
            db.add(AgentRun(
                id=self.run_id,
                matter_id=self.matter_one,
                client_id=self.client_id,
                status="awaiting_information",
                state_json={},
            ))
            db.commit()
        finally:
            db.close()

        snapshot = {
            "success": True,
            "run_id": self.run_id,
            "matter_id": self.matter_one,
            "status": "awaiting_information",
        }
        with patch(
            "services.conversation.workspace.get_legal_agent_facade",
            return_value=_FakeFacade({self.run_id: snapshot}),
        ):
            restored = self.service.select_matter(
                self.session_id,
                self.matter_one,
                self.client_id,
            )

        self.assertEqual(restored["matter"]["matter_id"], self.matter_one)
        self.assertEqual(restored["triage"]["version"], 1)
        self.assertEqual(restored["run"]["run_id"], self.run_id)
        self.assertEqual(restored["presentation"]["state_key"], "needs_information")
        self.assertNotIn("template_id", restored["presentation"])

    def test_selected_pointer_drives_conversation_context(self):
        self.service.select_matter(
            self.session_id,
            self.matter_one,
            self.client_id,
        )
        context = ConversationRepository().matter_context(
            self.session_id,
            self.client_id,
        )
        self.assertEqual(context["matter_id"], self.matter_one)

    def test_explicit_clear_does_not_guess_an_old_matter(self):
        self.service.select_matter(
            self.session_id,
            self.matter_one,
            self.client_id,
        )
        cleared = self.service.select_matter(
            self.session_id,
            None,
            self.client_id,
        )
        self.assertIsNone(cleared["matter"])
        self.assertIsNone(
            self.service.resolve_active_matter_id(
                self.session_id,
                self.client_id,
            )
        )

    def test_workspace_version_rejects_stale_selection(self):
        selected = self.service.select_matter(
            self.session_id,
            self.matter_one,
            self.client_id,
            expected_version=0,
        )
        self.assertEqual(selected["workspace_version"], 1)

        repeated = self.service.select_matter(
            self.session_id,
            self.matter_one,
            self.client_id,
            expected_version=1,
        )
        self.assertEqual(repeated["workspace_version"], 1)

        with self.assertRaises(WorkspaceVersionConflict):
            self.service.select_matter(
                self.session_id,
                self.matter_two,
                self.client_id,
                expected_version=0,
            )
        restored = self.service.get_context(self.session_id, self.client_id)
        self.assertEqual(restored["matter"]["matter_id"], self.matter_one)

    def test_background_action_does_not_override_newer_selection(self):
        selected = self.service.select_matter(
            self.session_id,
            self.matter_two,
            self.client_id,
            expected_version=0,
        )
        self.assertEqual(selected["workspace_version"], 1)

        with patch(
            "services.conversation.actions.get_legal_agent_facade",
            return_value=_FakeTriageFacade(
                self.matter_one,
                self.session_id,
            ),
        ):
            action = ConversationActions()._create_labor_case(
                "公司欠薪，我要申请劳动仲裁",
                self.client_id,
                self.session_id,
                {"matter_id": self.matter_one},
                None,
                False,
                0,
            )

        self.assertEqual(action.matter_id, self.matter_one)
        restored = self.service.get_context(self.session_id, self.client_id)
        self.assertEqual(restored["workspace_version"], 1)
        self.assertEqual(restored["matter"]["matter_id"], self.matter_two)

    def test_context_snapshot_serializes_with_concurrent_selection(self):
        self.service.select_matter(
            self.session_id,
            self.matter_one,
            self.client_id,
            expected_version=0,
        )
        entered = threading.Event()
        release = threading.Event()
        original_resolve = self.service._resolve_state_and_matter
        results = {}

        def blocked_resolve(db, session_id, client_id):
            resolved = original_resolve(db, session_id, client_id)
            entered.set()
            release.wait(timeout=5)
            return resolved

        self.service._resolve_state_and_matter = blocked_resolve

        snapshot_thread = threading.Thread(
            target=lambda: results.update(
                snapshot=self.service.get_context(
                    self.session_id,
                    self.client_id,
                )
            )
        )
        select_thread = threading.Thread(
            target=lambda: results.update(
                selected=self.service.select_matter(
                    self.session_id,
                    self.matter_two,
                    self.client_id,
                    expected_version=1,
                )
            )
        )
        snapshot_thread.start()
        self.assertTrue(entered.wait(timeout=5))
        select_thread.start()
        select_thread.join(timeout=0.2)
        self.assertTrue(select_thread.is_alive())
        release.set()
        snapshot_thread.join(timeout=5)
        select_thread.join(timeout=5)

        self.assertFalse(snapshot_thread.is_alive())
        self.assertFalse(select_thread.is_alive())
        self.assertEqual(results["snapshot"]["workspace_version"], 1)
        self.assertEqual(
            results["snapshot"]["matter"]["matter_id"],
            self.matter_one,
        )
        self.assertEqual(results["selected"]["workspace_version"], 2)
        self.assertEqual(
            results["selected"]["matter"]["matter_id"],
            self.matter_two,
        )

    def test_workspace_can_create_session_before_first_chat(self):
        created = self.service.create_session(self.client_id)
        created_session_id = created["session_id"]
        try:
            self.assertTrue(created_session_id.startswith("dh_"))
            self.assertIsNone(created["matter"])
            self.assertEqual(created["workspace_version"], 0)
            self.assertEqual(created["presentation"]["state_key"], "idle")
        finally:
            db = SessionLocal()
            try:
                db.query(ConversationWorkspaceState).filter(
                    ConversationWorkspaceState.session_id == created_session_id
                ).delete(synchronize_session=False)
                db.query(DigitalHumanSession).filter(
                    DigitalHumanSession.id == created_session_id
                ).delete(synchronize_session=False)
                db.commit()
            finally:
                db.close()

    def test_delete_current_matter_selects_remaining_fallback_atomically(self):
        self.service.select_matter(
            self.session_id,
            self.matter_one,
            self.client_id,
        )
        deleted = self.service.delete_matter(
            self.matter_one,
            self.client_id,
        )
        restored = self.service.get_context(
            self.session_id,
            self.client_id,
        )
        self.assertEqual(deleted["matter_id"], self.matter_one)
        self.assertEqual(restored["matter"]["matter_id"], self.matter_two)
        db = SessionLocal()
        try:
            self.assertIsNone(db.get(Matter, self.matter_one))
        finally:
            db.close()

    def test_cross_client_session_and_matter_are_rejected(self):
        with self.assertRaises(PermissionError):
            self.service.get_context(
                self.session_id,
                self.other_client_id,
            )
        with self.assertRaises(PermissionError):
            self.service.select_matter(
                self.other_session_id,
                self.matter_one,
                self.other_client_id,
            )

    def test_presenter_maps_all_runtime_states_without_raw_fallback(self):
        statuses = {
            "planning", "replanning", "executing", "observing", "verifying",
            "deciding", "retrying", "awaiting_jurisdiction",
            "awaiting_information", "blocked_authority", "awaiting_approval",
            "human_handoff", "completed", "failed", "cancelled",
        }
        for status in statuses:
            result = present_conversation_state(
                {"matter_id": self.matter_one},
                None,
                {"status": status},
            )
            self.assertNotEqual(result["state_key"], "unknown", status)
            self.assertNotIn(status, result["headline"])
        unknown = present_conversation_state(
            {"matter_id": self.matter_one},
            None,
            {"status": "future_internal_state"},
        )
        self.assertEqual(unknown["state_key"], "unknown")
        self.assertNotIn("future_internal_state", str(unknown))


class DigitalHumanIdentityTest(unittest.TestCase):
    def test_cookie_restores_identity_after_header_changes(self):
        app = Flask(__name__)

        @app.after_request
        def persist(response):
            return persist_digital_human_identity(response)

        @app.get("/api/digital-human/identity-test")
        def identity_test():
            return jsonify({"client_id": get_digital_human_client_id()})

        client = app.test_client()
        first_id = f"dhc_cookie_{uuid.uuid4().hex}"
        second_id = f"dhc_new_local_{uuid.uuid4().hex}"
        first = client.get(
            "/api/digital-human/identity-test",
            headers={"X-Digital-Human-Client-ID": first_id},
        )
        self.assertEqual(first.status_code, 200)
        self.assertIn(f"{COOKIE_NAME}=", first.headers.get("Set-Cookie", ""))

        restored = client.get(
            "/api/digital-human/identity-test",
            headers={"X-Digital-Human-Client-ID": second_id},
        )
        self.assertEqual(restored.get_json()["client_id"], first_id)


class DigitalHumanWorkspaceRouteTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        Base.metadata.create_all(bind=engine)

    def test_create_retry_reuses_matter_after_workspace_failure(self):
        from routers import digital_human_agent

        token = uuid.uuid4().hex
        client_id = f"dhc_37e_route_{token}"
        session_id = f"dh_37e_route_{token}"
        key = f"dhm_{token}"
        matter_id = "matter_" + hashlib.sha256(
            f"{client_id}:{key}".encode("utf-8")
        ).hexdigest()[:32]
        db = SessionLocal()
        try:
            db.add(DigitalHumanSession(
                id=session_id,
                user_id=client_id,
                title="幂等创建测试",
                is_active=True,
            ))
            db.commit()
        finally:
            db.close()

        service = ConversationWorkspaceService()

        class FailOnceWorkspace:
            calls = 0

            def select_matter(self, *args, **kwargs):
                self.calls += 1
                if self.calls == 1:
                    raise SQLAlchemyError("模拟指针提交失败")
                return service.select_matter(*args, **kwargs)

        app = Flask(__name__)
        app.register_blueprint(digital_human_agent.router, url_prefix="/api")
        client = app.test_client()
        workspace = FailOnceWorkspace()
        payload = {
            "goal": "幂等案件",
            "session_id": session_id,
            "expected_version": 0,
        }
        headers = {
            "X-Digital-Human-Client-ID": client_id,
            "Idempotency-Key": key,
        }
        try:
            with patch.object(
                digital_human_agent,
                "get_conversation_workspace_service",
                return_value=workspace,
            ):
                failed = client.post(
                    "/api/digital-human/agent/matters",
                    json=payload,
                    headers=headers,
                )
                retried = client.post(
                    "/api/digital-human/agent/matters",
                    json=payload,
                    headers=headers,
                )
            self.assertEqual(failed.status_code, 503)
            self.assertEqual(retried.status_code, 200)
            self.assertEqual(retried.get_json()["matter_id"], matter_id)
            self.assertEqual(
                retried.get_json()["workspace"]["matter"]["matter_id"],
                matter_id,
            )
            db = SessionLocal()
            try:
                count = db.query(Matter).filter(
                    Matter.id == matter_id
                ).count()
            finally:
                db.close()
            self.assertEqual(count, 1)
        finally:
            db = SessionLocal()
            try:
                db.query(ConversationWorkspaceState).filter(
                    ConversationWorkspaceState.session_id == session_id
                ).delete(synchronize_session=False)
                db.query(Matter).filter(
                    Matter.id == matter_id
                ).delete(synchronize_session=False)
                db.query(DigitalHumanSession).filter(
                    DigitalHumanSession.id == session_id
                ).delete(synchronize_session=False)
                db.commit()
            finally:
                db.close()

    def test_frontend_has_chat_and_workspace_ordering_guards(self):
        root = Path(__file__).resolve().parents[2]
        store = (
            root / "frontend/src/store/digitalHumanStore.ts"
        ).read_text(encoding="utf-8")
        workspace = (
            root
            / "frontend/src/components/DigitalHuman/DigitalHumanMatterWorkspace.tsx"
        ).read_text(encoding="utf-8")
        self.assertIn(
            "operation !== conversationOperationSequence",
            store,
        )
        self.assertIn("workspaceSelectionTail.then(select, select)", store)
        self.assertIn(
            "selectCurrentMatter: (matterId) => {\n"
            "        invalidateConversationRequest();",
            store,
        )
        self.assertIn("workspaceVersion", store)
        self.assertIn("await selectCurrentMatter(detail.matter_id)", workspace)


if __name__ == "__main__":
    unittest.main()
