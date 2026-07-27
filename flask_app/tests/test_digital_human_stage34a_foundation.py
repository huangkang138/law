"""阶段 3.4A 来源边界、迁移基线与离线评测测试。"""

import unittest
from pathlib import Path

from evals.labor_disputes import load_cases, run_dataset
from legal_agent_system.jurisdictions.authorities import LegalAuthorityService
from legal_agent_system.runtime.errors import AgentRuntimeError
from legal_agent_system.runtime.registry import ToolRegistry
from legal_agent_system.tools.authority_tools import register_authority_verification_tools


class DigitalHumanStage34AFoundationTest(unittest.TestCase):
    def test_public_authority_registration_route_is_removed(self):
        router_source = (Path(__file__).resolve().parents[1] / "routers" / "digital_human_agent.py").read_text(encoding="utf-8")
        self.assertNotIn('@router.route("/digital-human/agent/legal-authorities", methods=["POST"])', router_source)

    def test_test_authority_rejects_real_domains(self):
        with self.assertRaises(AgentRuntimeError) as denied:
            LegalAuthorityService().register_test({"source_url": "https://example.com/not-allowed"})
        self.assertEqual(denied.exception.code, "TEST_AUTHORITY_ONLY")

    def test_agent_registry_cannot_register_authorities(self):
        registry = ToolRegistry()
        register_authority_verification_tools(registry, LegalAuthorityService())
        with self.assertRaises(AgentRuntimeError):
            registry.get("register_legal_authority")
        self.assertEqual(registry.get("verify_legal_citation")[0].risk_level, "L1")

    def test_alembic_baseline_and_labor_eval_dataset(self):
        flask_root = Path(__file__).resolve().parents[1]
        self.assertTrue((flask_root / "alembic.ini").is_file())
        self.assertTrue((flask_root / "migrations" / "versions" / "20260713_0001_existing_schema_baseline.py").is_file())
        cases = load_cases()
        self.assertEqual(len(cases), 30)
        report = run_dataset(cases)
        self.assertEqual(report.failed, 0)
        self.assertEqual(report.passed, 30)


if __name__ == "__main__":
    unittest.main()
