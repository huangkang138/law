"""数字人阶段 1 Runtime PostgreSQL 集成测试。"""

import unittest
import uuid

from core.database import Base, SessionLocal, engine
from legal_agent_system.facade import LegalAgentFacade
from legal_agent_system.runtime.errors import AgentRuntimeError
from models.db_models import AgentRun, Matter


class DigitalHumanStage1IntegrationTest(unittest.TestCase):
    """验证阶段 1 最小状态机在真实 PostgreSQL 中的完整闭环。"""

    @classmethod
    def setUpClass(cls):
        """只创建缺失表，不修改或删除现有业务数据。"""
        Base.metadata.create_all(bind=engine)

    def setUp(self):
        """每个测试使用独立匿名客户端，避免与真实会话冲突。"""
        token = uuid.uuid4().hex
        self.client_id = f"dhc_stage1_{token}"
        self.other_client_id = f"dhc_stage1_other_{token}"
        self.facade = LegalAgentFacade()
        self.run_id = None

    def tearDown(self):
        """按外键顺序清理本测试创建的运行和 Matter。"""
        if not self.run_id:
            return
        db = SessionLocal()
        try:
            run = db.get(AgentRun, self.run_id)
            if run:
                matter_id = run.matter_id
                db.delete(run)
                db.flush()
                matter = db.get(Matter, matter_id)
                if matter:
                    db.delete(matter)
                db.commit()
        finally:
            db.close()

    def test_retry_pause_resume_isolation_and_audit(self):
        """覆盖重试、暂停、跨实例恢复、隔离、完成和审计。"""
        started = self.facade.start_run("整理一起模拟劳动争议", self.client_id)
        self.run_id = started["run_id"]
        self.assertEqual(started["status"], "awaiting_approval")
        self.assertEqual(started["steps"][0]["status"], "awaiting_approval")
        self.assertIsNotNone(started["approval"])

        with self.assertRaises(AgentRuntimeError) as denied:
            self.facade.get_run(self.run_id, self.other_client_id)
        self.assertEqual(denied.exception.code, "FORBIDDEN")

        # 创建新 Facade 模拟服务重启，证明恢复不依赖进程内对象。
        restored_facade = LegalAgentFacade()
        completed = restored_facade.resume_run(self.run_id, self.client_id, True)
        self.assertEqual(completed["status"], "completed")
        self.assertEqual(completed["steps"][0]["status"], "completed")
        self.assertIn("summary", completed["final_output"]["mock_case_summary"])

        events = restored_facade.get_audit(self.run_id, self.client_id)
        event_types = [event["type"] for event in events]
        self.assertIn("run_paused_for_approval", event_types)
        self.assertIn("run_resumed", event_types)
        self.assertIn("step_verified", event_types)
        self.assertIn("run_completed", event_types)
        self.assertEqual(event_types.count("tool_called"), 1)


if __name__ == "__main__":
    unittest.main()
