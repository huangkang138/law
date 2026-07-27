"""方案 C 架构边界测试：防止通用 Runtime 再次退化成领域专用实现。"""

import ast
import unittest
from pathlib import Path


AGENT_ROOT = Path(__file__).resolve().parents[1] / "legal_agent_system"
RUNTIME_ROOT = AGENT_ROOT / "runtime"
PROJECT_ROOT = Path(__file__).resolve().parents[2]


class DigitalHumanArchitectureBoundaryTest(unittest.TestCase):
    def test_legacy_execution_kernels_are_removed(self):
        legacy_files = {
            "runtime.py", "graph.py", "labor_runtime.py", "labor_graph.py", "planner.py",
        }
        self.assertFalse(legacy_files.intersection(path.name for path in RUNTIME_ROOT.iterdir()))

    def test_generic_runtime_does_not_import_domain_services(self):
        forbidden_prefixes = (
            "legal_agent_system.domains",
            "legal_agent_system.labor_disputes",
            "legal_agent_system.matters",
            "legal_agent_system.jurisdictions",
        )
        for filename in ("capability_runtime.py", "capability_graph.py", "verifier.py"):
            tree = ast.parse((RUNTIME_ROOT / filename).read_text(encoding="utf-8"))
            imports = [
                node.module or ""
                for node in ast.walk(tree)
                if isinstance(node, ast.ImportFrom)
            ]
            self.assertFalse(
                any(name.startswith(forbidden_prefixes) for name in imports),
                f"{filename} 不得直接导入领域服务: {imports}",
            )

    def test_domain_adapter_contract_keeps_required_extension_points(self):
        source = (AGENT_ROOT / "capabilities" / "domain_adapter.py").read_text(encoding="utf-8")
        tree = ast.parse(source)
        protocol = next(
            node for node in tree.body
            if isinstance(node, ast.ClassDef) and node.name == "DomainRuntimeAdapter"
        )
        methods = {node.name for node in protocol.body if isinstance(node, ast.FunctionDef)}
        self.assertEqual(methods, {
            "prepare_start", "assess_context", "get_workflow", "customize_plan",
            "tool_arguments", "jurisdiction_code", "verification_reports",
            "provide_information", "confirm_jurisdiction",
        })

    def test_conversation_orchestrator_is_the_only_chat_triage_entry(self):
        chat_source = (
            PROJECT_ROOT
            / "frontend" / "src" / "components" / "DigitalHuman"
            / "DigitalHumanChat.tsx"
        ).read_text(encoding="utf-8")
        self.assertNotIn("isLaborQuestion", chat_source)
        self.assertNotIn("laborTriage.start(", chat_source)

        runtime_sources = "\n".join(
            path.read_text(encoding="utf-8")
            for path in RUNTIME_ROOT.glob("*.py")
        )
        self.assertNotIn("services.conversation", runtime_sources)


if __name__ == "__main__":
    unittest.main()
