"""数字人数据库故障不得伪装成参数错误或泄露驱动细节。"""

import ast

from pathlib import Path


APP_DIR = Path(__file__).resolve().parents[1]
CHAT_ROUTER = (APP_DIR / "routers" / "digital_human.py").read_text(encoding="utf-8")
AGENT_ROUTER = (APP_DIR / "routers" / "digital_human_agent.py").read_text(encoding="utf-8")
LOGGER_CONFIG = (APP_DIR / "core" / "logger.py").read_text(encoding="utf-8")
FRONTEND_DIR = APP_DIR.parent / "frontend" / "src"
CHAT_STORE = (FRONTEND_DIR / "store" / "digitalHumanStore.ts").read_text(encoding="utf-8")
CHAT_VIEW = (FRONTEND_DIR / "components" / "DigitalHuman" / "DigitalHumanChat.tsx").read_text(encoding="utf-8")
MATTER_VIEW = (FRONTEND_DIR / "components" / "DigitalHuman" / "DigitalHumanMatterWorkspace.tsx").read_text(encoding="utf-8")


def test_agent_database_failure_is_checked_before_value_error() -> None:
    database_handler = AGENT_ROUTER.index("except (UnicodeError, SQLAlchemyError)")
    input_handler = AGENT_ROUTER.index("except (TypeError, ValueError)")
    assert database_handler < input_handler
    assert '"code": "DATABASE_UNAVAILABLE"' in AGENT_ROUTER
    assert "), 503" in AGENT_ROUTER


def test_chat_database_failure_uses_safe_service_error() -> None:
    assert "except (UnicodeError, SQLAlchemyError)" in CHAT_ROUTER
    assert '"code": "DATABASE_UNAVAILABLE"' in CHAT_ROUTER
    assert "数据服务暂时不可用" in CHAT_ROUTER


def test_reset_database_failure_is_handled_inside_reset_route() -> None:
    module = ast.parse(CHAT_ROUTER)
    reset_route = next(
        node
        for node in module.body
        if isinstance(node, ast.FunctionDef) and node.name == "reset_session"
    )
    route_try = next(node for node in reset_route.body if isinstance(node, ast.Try))
    handled_names = {
        name.id
        for handler in route_try.handlers
        if isinstance(handler.type, ast.Tuple)
        for name in handler.type.elts
        if isinstance(name, ast.Name)
    }
    assert {"UnicodeError", "SQLAlchemyError"} <= handled_names


def test_production_tracebacks_do_not_dump_local_secrets() -> None:
    assert "diagnose=True" not in LOGGER_CONFIG
    assert LOGGER_CONFIG.count("diagnose=False") == 2


def test_history_failures_are_not_rendered_as_empty_records() -> None:
    assert "historyError" in CHAT_STORE
    assert "historyError" in CHAT_VIEW
    assert "历史会话读取失败" in CHAT_STORE
    assert "catch { /* 保留当前界面 */ }" not in CHAT_STORE


def test_matter_history_failure_is_visible() -> None:
    assert "mattersError" in MATTER_VIEW
    assert "案件记录读取失败" in MATTER_VIEW
