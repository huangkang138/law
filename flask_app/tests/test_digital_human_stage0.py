"""数字人阶段 0 数据库集成测试。"""

import json
import unittest
import uuid

from core.database import Base, SessionLocal, engine
from models.db_models import DigitalHumanRequest, DigitalHumanSession
from services.digital_human_service import DigitalHumanService


class _Chunk:
    content = json.dumps({
        "reply": "测试回复",
        "intent": "general_chat",
        "emotion": "talk_normal",
        "confidence": 0.9,
    }, ensure_ascii=False)


class _FakeLlm:
    @staticmethod
    def stream(_messages):
        yield _Chunk()


class DigitalHumanStage0IntegrationTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        Base.metadata.create_all(bind=engine)

    def setUp(self):
        token = uuid.uuid4().hex
        self.client_id = f"dhc_test_{token}"
        self.other_client_id = f"dhc_test_other_{token}"
        self.session_id = f"dh_test_{token}"
        self.request_id = f"dhr_test_{token}"
        self.service = DigitalHumanService.__new__(DigitalHumanService)
        self.service.llm = _FakeLlm()
        self.service.system_prompt = "测试系统提示词"

    def tearDown(self):
        db = SessionLocal()
        try:
            db.query(DigitalHumanRequest).filter(
                DigitalHumanRequest.request_id == self.request_id
            ).delete(synchronize_session=False)
            db.query(DigitalHumanSession).filter(
                DigitalHumanSession.id == self.session_id
            ).delete(synchronize_session=False)
            db.commit()
        finally:
            db.close()

    def test_isolation_history_idempotency_and_delete(self):
        first = self.service.chat(
            question="测试问题",
            client_id=self.client_id,
            request_id=self.request_id,
            session_id=self.session_id,
        )
        repeated = self.service.chat(
            question="测试问题",
            client_id=self.client_id,
            request_id=self.request_id,
            session_id=self.session_id,
        )

        self.assertEqual(first, repeated)
        self.assertEqual(len(self.service.get_messages(self.session_id, self.client_id)), 2)
        self.assertEqual(len(self.service.list_sessions(self.client_id)), 1)
        with self.assertRaises(PermissionError):
            self.service.get_messages(self.session_id, self.other_client_id)
        self.assertTrue(self.service.reset_session(self.session_id, self.client_id))
        self.assertEqual(self.service.list_sessions(self.client_id), [])


if __name__ == "__main__":
    unittest.main()
