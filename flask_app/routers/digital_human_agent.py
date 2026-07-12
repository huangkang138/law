"""数字人 Agent Runtime API。"""

from flask import Blueprint, jsonify, request

from legal_agent_system import get_legal_agent_facade
from legal_agent_system.runtime.errors import AgentRuntimeError


router = Blueprint("digital_human_agent", __name__)


def _client_id() -> str:
    """读取并校验阶段 0 建立的浏览器匿名身份。"""
    value = request.headers.get("X-Digital-Human-Client-ID", "").strip()
    if not value.startswith("dhc_") or len(value) > 100:
        raise AgentRuntimeError("缺少或无效的数字人客户端标识", "INVALID_INPUT")
    return value


def _response(action):
    """统一成功结构，并把领域错误映射为稳定 HTTP 状态码。"""
    try:
        return jsonify({"success": True, **action()})
    except AgentRuntimeError as exc:
        status = 403 if exc.code == "FORBIDDEN" else 404 if exc.code == "RUN_NOT_FOUND" else 409 if exc.code == "INVALID_STATE" else 400
        return jsonify({"success": False, "error": str(exc), "code": exc.code}), status


@router.route("/digital-human/agent/runs", methods=["POST"])
def create_run():
    """创建模拟 Agent 任务，并执行到等待审批或终态。"""
    def action():
        data = request.get_json(silent=True) or {}
        return get_legal_agent_facade().start_run(data.get("goal"), _client_id(), data.get("session_id"))
    return _response(action)


@router.route("/digital-human/agent/runs/<run_id>", methods=["GET"])
def get_run(run_id):
    """查询当前客户端所属的任务快照。"""
    return _response(lambda: get_legal_agent_facade().get_run(run_id, _client_id()))


@router.route("/digital-human/agent/runs/<run_id>/resume", methods=["POST"])
def resume_run(run_id):
    """提交审批决定并恢复任务。"""
    def action():
        data = request.get_json(silent=True) or {}
        if not isinstance(data.get("approved"), bool):
            raise AgentRuntimeError("approved 必须是布尔值", "INVALID_INPUT")
        return get_legal_agent_facade().resume_run(run_id, _client_id(), data["approved"])
    return _response(action)


@router.route("/digital-human/agent/runs/<run_id>/cancel", methods=["POST"])
def cancel_run(run_id):
    """取消任务和当前步骤。"""
    return _response(lambda: get_legal_agent_facade().cancel_run(run_id, _client_id()))


@router.route("/digital-human/agent/runs/<run_id>/audit", methods=["GET"])
def get_audit(run_id):
    """查询任务的结构化审计事件。"""
    return _response(lambda: {"events": get_legal_agent_facade().get_audit(run_id, _client_id())})
