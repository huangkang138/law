"""数字人 Agent Runtime、材料和法律来源 API。"""

from datetime import datetime, timezone

from flask import Blueprint, jsonify, request
from sqlalchemy.exc import SQLAlchemyError

from core.logger import app_logger
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
    except (UnicodeError, SQLAlchemyError):
        app_logger.exception("数字人 Agent 数据库不可用")
        return jsonify({
            "success": False,
            "error": "数字人数据服务暂时不可用，请稍后重试",
            "code": "DATABASE_UNAVAILABLE",
        }), 503
    except (TypeError, ValueError):
        return jsonify({"success": False, "error": "请求参数格式错误", "code": "INVALID_INPUT"}), 400
    except Exception:
        app_logger.exception("数字人 Agent 接口执行失败")
        return jsonify({
            "success": False,
            "error": "数字人 Agent 服务暂时不可用",
            "code": "INTERNAL_ERROR",
        }), 500


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


@router.route("/digital-human/agent/matters/<matter_id>/materials", methods=["POST"])
def add_material(matter_id):
    """保存当前 Matter 已授权的文本材料并建立位置分片。"""
    def action():
        data = request.get_json(silent=True) or {}
        return get_legal_agent_facade().add_material(
            matter_id, _client_id(), data.get("filename"), data.get("text"), data.get("media_type", "text/plain"),
        )
    return _response(action)


@router.route("/digital-human/agent/matters", methods=["POST"])
def create_matter():
    """创建阶段 2 材料工作区。"""
    data = request.get_json(silent=True) or {}
    return _response(lambda: get_legal_agent_facade().create_matter(
        _client_id(), data.get("goal"), data.get("session_id"),
    ))


@router.route("/digital-human/agent/matters", methods=["GET"])
def list_matters():
    """列出当前客户端的案件工作区。"""
    return _response(lambda: {"matters": get_legal_agent_facade().list_matters(_client_id())})


@router.route("/digital-human/agent/matters/<matter_id>", methods=["DELETE"])
def delete_matter(matter_id):
    """删除 Matter 及其全部阶段 2 衍生数据。"""
    return _response(lambda: get_legal_agent_facade().delete_matter(matter_id, _client_id()))


@router.route("/digital-human/agent/matters/<matter_id>", methods=["GET"])
def get_matter(matter_id):
    """读取 Matter 详情和已确认法域。"""
    return _response(lambda: get_legal_agent_facade().get_matter(matter_id, _client_id()))


@router.route("/digital-human/agent/matters/<matter_id>/tools/labor-compensation", methods=["POST"])
def calculate_matter_labor_compensation(matter_id):
    """通过 Agent 工具注册中心执行劳动补偿估算。"""
    return _response(lambda: get_legal_agent_facade().calculate_labor_compensation(
        matter_id, _client_id(), request.get_json(silent=True) or {},
    ))


@router.route("/digital-human/agent/matters/<matter_id>/labor-dispute", methods=["GET"])
def get_labor_dispute_workflow(matter_id):
    """恢复劳动纠纷动态计划及缺失事实。"""
    return _response(lambda: get_legal_agent_facade().get_labor_dispute_workflow(matter_id, _client_id()))


@router.route("/digital-human/agent/matters/<matter_id>/labor/triage", methods=["GET"])
def get_labor_case_triage(matter_id):
    """恢复青年就业劳动案件分流与关系初筛结果。"""
    return _response(lambda: get_legal_agent_facade().get_labor_case_triage(
        matter_id, _client_id(),
    ))


@router.route("/digital-human/agent/matters/<matter_id>/labor/triage", methods=["POST"])
def update_labor_case_triage(matter_id):
    """保存结构化分流事实；不会自动启动仲裁或生成文书。"""
    return _response(lambda: get_legal_agent_facade().update_labor_case_triage(
        matter_id, _client_id(), request.get_json(silent=True) or {},
    ))


@router.route("/digital-human/agent/matters/<matter_id>/labor-dispute/run", methods=["POST"])
def start_labor_dispute_run(matter_id):
    """兼容入口：可选 task_type 选择三类劳动模板，缺省仍为仲裁申请。"""
    data = request.get_json(silent=True) or {}
    return _response(lambda: get_legal_agent_facade().start_task(
        matter_id, _client_id(), data.get("task_type", "cn_labor_dispute"), data.get("facts"),
    ))


@router.route("/digital-human/agent/capabilities", methods=["GET"])
def list_agent_capabilities():
    """查询当前已注册领域和计划模板。"""
    return _response(lambda: get_legal_agent_facade().list_agent_capabilities())


@router.route("/digital-human/agent/matters/<matter_id>/labor-dispute/suggestions", methods=["GET"])
def suggest_labor_dispute_facts(matter_id):
    """读取材料候选值供用户采用或编辑，不直接写入确认事实。"""
    return _response(lambda: get_legal_agent_facade().suggest_labor_dispute_facts(
        matter_id, _client_id(),
    ))


@router.route("/digital-human/agent/runs/<run_id>/continue", methods=["POST"])
def continue_labor_dispute_run(run_id):
    """使用结构化动作继续劳动纠纷任务，不再把恢复限制为布尔审批。"""
    def action():
        data = request.get_json(silent=True) or {}
        action_name = str(data.get("action", "")).strip()
        if not action_name:
            raise AgentRuntimeError("缺少继续动作", "INVALID_INPUT")
        return get_legal_agent_facade().continue_task(
            run_id, _client_id(), action_name, data.get("payload") or {},
            request.headers.get("Idempotency-Key") or data.get("idempotency_key"),
        )
    return _response(action)


@router.route("/digital-human/agent/matters/<matter_id>/labor-dispute/facts", methods=["PATCH"])
def update_labor_dispute_facts(matter_id):
    """合并用户确认事实并生成下一轮追问。"""
    return _response(lambda: get_legal_agent_facade().update_labor_dispute_facts(
        matter_id, _client_id(), request.get_json(silent=True) or {},
    ))


@router.route("/digital-human/agent/matters/<matter_id>/labor-dispute/analyze", methods=["POST"])
def analyze_labor_dispute(matter_id):
    """运行期限、证据和来源验证，前置条件不足时保持暂停。"""
    return _response(lambda: get_legal_agent_facade().analyze_labor_dispute(matter_id, _client_id()))


@router.route("/digital-human/agent/matters/<matter_id>/labor-dispute/draft", methods=["POST"])
def create_labor_dispute_draft(matter_id):
    """仅在用户明确审批后生成仲裁申请书草稿。"""
    def action():
        data = request.get_json(silent=True) or {}
        if not isinstance(data.get("approved"), bool):
            raise AgentRuntimeError("approved 必须是布尔值", "INVALID_INPUT")
        return get_legal_agent_facade().create_labor_dispute_draft(
            matter_id, _client_id(), data["approved"],
        )
    return _response(action)


@router.route("/digital-human/agent/matters/<matter_id>/materials/<document_id>/facts", methods=["POST"])
def extract_material_facts(matter_id, document_id):
    """从材料中提取带字符偏移引用的候选事实。"""
    return _response(lambda: {"facts": get_legal_agent_facade().extract_material_facts(matter_id, _client_id(), document_id)})


@router.route("/digital-human/agent/matters/<matter_id>/timeline", methods=["GET"])
def get_timeline(matter_id):
    """读取当前 Matter 的可追溯时间线。"""
    return _response(lambda: {"timeline": get_legal_agent_facade().build_matter_timeline(matter_id, _client_id())})


@router.route("/digital-human/agent/matters/<matter_id>/evidence-checklist", methods=["GET"])
def get_evidence_checklist(matter_id):
    """读取已有材料、事实数量和显式证据缺口。"""
    return _response(lambda: get_legal_agent_facade().get_evidence_checklist(matter_id, _client_id()))


@router.route("/digital-human/agent/jurisdictions", methods=["GET"])
def list_jurisdictions():
    """列出 Runtime 当前支持的法域包。"""
    return _response(lambda: {"jurisdictions": get_legal_agent_facade().list_jurisdictions()})


@router.route("/digital-human/agent/matters/<matter_id>/jurisdiction", methods=["POST"])
def confirm_jurisdiction(matter_id):
    """保存用户明确确认的 Matter 法域上下文。"""
    return _response(lambda: get_legal_agent_facade().confirm_jurisdiction(
        matter_id, _client_id(), request.get_json(silent=True) or {},
    ))


@router.route("/digital-human/agent/legal-authorities/<authority_id>/verify", methods=["POST"])
def verify_authority(authority_id):
    """按法域和适用日期验证法律引用。"""
    def action():
        data = request.get_json(silent=True) or {}
        effective_at = datetime.fromisoformat(str(data.get("effective_at", "")).replace("Z", "+00:00"))
        if effective_at.tzinfo is None:
            effective_at = effective_at.replace(tzinfo=timezone.utc)
        return get_legal_agent_facade().verify_authority(authority_id, effective_at, str(data.get("country_code", "")).upper())
    return _response(action)


@router.route("/digital-human/agent/legal-authorities/labor", methods=["GET"])
def list_labor_authorities():
    """只读返回劳动纠纷闭环当前可用的官方来源及同步状态。"""
    _client_id()
    return _response(lambda: get_legal_agent_facade().get_labor_authority_catalog())
