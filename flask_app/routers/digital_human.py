"""数字人智能助手路由。"""

from flask import Blueprint, Response, jsonify, request, stream_with_context
from sqlalchemy.exc import SQLAlchemyError

from core.logger import app_logger
from services.conversation import (
    WorkspaceVersionConflict,
    get_conversation_workspace_service,
)
from services.conversation.cancel import ConversationCancelled
from services.digital_human_identity import (
    get_digital_human_client_id,
    persist_digital_human_identity,
)
from services.digital_human_service import get_digital_human_service


router = Blueprint("digital_human", __name__)


@router.after_request
def _persist_identity(response):
    return persist_digital_human_identity(response)


def _database_unavailable(operation: str):
    """统一隐藏数据库驱动细节，避免连接故障被误报为参数错误。"""
    app_logger.exception(f"数字人{operation}数据库不可用")
    return jsonify({
        "success": False,
        "error": "数字人数据服务暂时不可用，请稍后重试",
        "code": "DATABASE_UNAVAILABLE",
    }), 503


def _get_client_id():
    """
    从请求头中获取并验证数字人客户端标识
    Returns:
        str: 验证通过的客户端标识
    Raises:
        ValueError: 当缺少或无效的客户端标识时抛出异常
    """
    return get_digital_human_client_id()


def _get_custom_llm_config():
    """
    从请求头中获取自定义大语言模型配置信息
    Returns:
        dict or None: 包含API配置的字典，如果缺少API密钥则返回None
    """
    # 从请求头中获取API密钥
    api_key = request.headers.get("X-API-Key")
    # 如果没有提供API密钥，则返回None
    if not api_key:
        return None
    # 返回包含API密钥、基础URL和模型名称的配置字典
    return {
        "api_key": api_key,
        "base_url": request.headers.get("X-API-Base-URL"),
        "model": request.headers.get("X-API-Model"),
    }


@router.route("/digital-human/chat", methods=["POST"])
def chat():
    """接收用户消息，返回数字人的回答、意图和表情。"""
    try:
        data = request.get_json(silent=True)
        if not isinstance(data, dict):
            return jsonify({"success": False, "error": "请求体必须是 JSON 对象"}), 400

        question = data.get("question")
        if not isinstance(question, str) or not question.strip():
            return jsonify({"success": False, "error": "缺少必要参数 question"}), 400

        session_id = data.get("session_id")
        if session_id is not None and not isinstance(session_id, str):
            return jsonify({"success": False, "error": "session_id 必须是字符串"}), 400
        request_id = data.get("request_id")
        if not isinstance(request_id, str) or not request_id.startswith("dhr_"):
            return jsonify({"success": False, "error": "缺少或无效的 request_id"}), 400

        result = get_digital_human_service().chat(
            question=question,
            client_id=_get_client_id(),
            request_id=request_id,
            session_id=session_id,
            custom_config=_get_custom_llm_config(),
        )
        return jsonify({"success": True, **result})
    except (UnicodeError, SQLAlchemyError):
        return _database_unavailable("聊天")
    except (ValueError, LookupError) as exc:
        return jsonify({"success": False, "error": str(exc)}), 400
    except PermissionError as exc:
        return jsonify({"success": False, "error": str(exc), "code": "FORBIDDEN"}), 403
    except ConversationCancelled as exc:
        return jsonify({
            "success": False,
            "error": str(exc),
            "code": "CANCELLED",
            "retryable": True,
        }), 409
    except RuntimeError as exc:
        return jsonify({"success": False, "error": str(exc), "code": "REQUEST_IN_PROGRESS"}), 409
    except Exception as exc:
        app_logger.exception(f"数字人聊天接口错误: {str(exc)}")
        return jsonify({"success": False, "error": "数字人暂时无法回答，请稍后重试"}), 500


@router.route("/digital-human/chat/stream", methods=["POST"])
def chat_stream():
    """接收用户消息，以SSE增量呈现已验证回复；完整响应与 /chat 一致。

    事件顺序：accepted → thinking → delta* → completed，
    处理异常时以 error 事件收尾；所有事件携带 request_id。
    回复在服务端完成解析、路由、安全校验和持久化后才分块下发。
    """
    try:
        data = request.get_json(silent=True)
        if not isinstance(data, dict):
            return jsonify({"success": False, "error": "请求体必须是 JSON 对象"}), 400

        question = data.get("question")
        if not isinstance(question, str) or not question.strip():
            return jsonify({"success": False, "error": "缺少必要参数 question"}), 400

        session_id = data.get("session_id")
        if session_id is not None and not isinstance(session_id, str):
            return jsonify({"success": False, "error": "session_id 必须是字符串"}), 400
        request_id = data.get("request_id")
        if not isinstance(request_id, str) or not request_id.startswith("dhr_"):
            return jsonify({"success": False, "error": "缺少或无效的 request_id"}), 400
        voice = data.get("voice")
        if voice is not None and not isinstance(voice, bool):
            return jsonify({"success": False, "error": "voice 必须是布尔值"}), 400

        stream = get_digital_human_service().chat_stream(
            question=question,
            client_id=_get_client_id(),
            request_id=request_id,
            session_id=session_id,
            custom_config=_get_custom_llm_config(),
            voice=voice is True,
        )
    except (UnicodeError, SQLAlchemyError):
        return _database_unavailable("流式聊天")
    except (ValueError, LookupError) as exc:
        return jsonify({"success": False, "error": str(exc)}), 400
    except PermissionError as exc:
        return jsonify({"success": False, "error": str(exc), "code": "FORBIDDEN"}), 403

    response = Response(
        stream_with_context(stream),
        mimetype="text/event-stream; charset=utf-8",
    )
    response.headers["Cache-Control"] = "no-cache, no-transform"
    response.headers["X-Accel-Buffering"] = "no"
    return response


@router.route("/digital-human/chat/cancel", methods=["POST"])
def cancel_chat():
    """停止指定数字人请求的服务端处理（幂等）。

    活跃请求标记为 cancelling，在途 LLM 分块循环发现后中断
    底层模型请求并落 cancelled 终态；已完成请求取消为 no-op。
    """
    try:
        data = request.get_json(silent=True)
        if not isinstance(data, dict):
            return jsonify({"success": False, "error": "请求体必须是 JSON 对象"}), 400
        request_id = data.get("request_id")
        if not isinstance(request_id, str) or not request_id.startswith("dhr_"):
            return jsonify({"success": False, "error": "缺少或无效的 request_id"}), 400
        result = get_digital_human_service().cancel_request(
            request_id,
            _get_client_id(),
        )
        return jsonify({"success": True, **result})
    except (UnicodeError, SQLAlchemyError):
        return _database_unavailable("停止回复")
    except LookupError as exc:
        return jsonify({"success": False, "error": str(exc), "code": "NOT_FOUND"}), 404
    except PermissionError as exc:
        return jsonify({"success": False, "error": str(exc), "code": "FORBIDDEN"}), 403
    except ValueError as exc:
        return jsonify({"success": False, "error": str(exc)}), 400


@router.route("/digital-human/reset", methods=["POST"])
def reset_session():
    """清空指定数字人会话的内存上下文。"""
    try:
        data = request.get_json(silent=True)
        if not isinstance(data, dict):
            return jsonify({"success": False, "error": "请求体必须是 JSON 对象"}), 400

        session_id = data.get("session_id")
        if not isinstance(session_id, str) or not session_id.strip():
            return jsonify({"success": False, "error": "缺少必要参数 session_id"}), 400
        if not session_id.startswith("dh_"):
            return jsonify({"success": False, "error": "数字人会话 ID 必须以 dh_ 开头"}), 400

        get_digital_human_service().reset_session(session_id, _get_client_id())
        return jsonify({
            "success": True,
            "message": "会话已重置",
            "session_id": session_id,
        })
    except (UnicodeError, SQLAlchemyError):
        return _database_unavailable("重置会话")
    except PermissionError as exc:
        return jsonify({"success": False, "error": str(exc), "code": "FORBIDDEN"}), 403
    except ValueError as exc:
        return jsonify({"success": False, "error": str(exc)}), 400
    except Exception as exc:
        app_logger.exception(f"数字人重置会话接口错误: {str(exc)}")
        return jsonify({"success": False, "error": "会话重置失败"}), 500


@router.route("/digital-human/sessions", methods=["GET"])
def list_sessions():
    try:
        sessions = get_digital_human_service().list_sessions(_get_client_id())
        return jsonify({"success": True, "sessions": sessions})
    except (UnicodeError, SQLAlchemyError):
        return _database_unavailable("读取历史会话")
    except ValueError as exc:
        return jsonify({"success": False, "error": str(exc)}), 400
    except Exception:
        app_logger.exception("数字人读取历史会话失败")
        return jsonify({"success": False, "error": "历史会话读取失败"}), 500


@router.route("/digital-human/sessions", methods=["POST"])
def create_workspace_session():
    """为先进入工作台的用户创建空会话，不调用LLM。"""
    try:
        result = get_conversation_workspace_service().create_session(
            _get_client_id(),
        )
        return jsonify({"success": True, **result}), 201
    except (UnicodeError, SQLAlchemyError):
        return _database_unavailable("创建案件会话")
    except ValueError as exc:
        return jsonify({"success": False, "error": str(exc)}), 400


@router.route("/digital-human/sessions/<session_id>/messages", methods=["GET"])
def get_messages(session_id):
    try:
        messages = get_digital_human_service().get_messages(session_id, _get_client_id())
        return jsonify({"success": True, "messages": messages})
    except (UnicodeError, SQLAlchemyError):
        return _database_unavailable("读取会话消息")
    except LookupError as exc:
        return jsonify({"success": False, "error": str(exc)}), 404
    except PermissionError as exc:
        return jsonify({"success": False, "error": str(exc), "code": "FORBIDDEN"}), 403
    except ValueError as exc:
        return jsonify({"success": False, "error": str(exc)}), 400


@router.route("/digital-human/sessions/<session_id>/workspace", methods=["GET"])
def get_workspace(session_id):
    """一次恢复当前Matter、Triage、Run及确定性会话投影。"""
    try:
        result = get_conversation_workspace_service().get_context(
            session_id,
            _get_client_id(),
        )
        return jsonify({"success": True, **result})
    except (UnicodeError, SQLAlchemyError):
        return _database_unavailable("恢复案件工作台")
    except LookupError as exc:
        return jsonify({"success": False, "error": str(exc)}), 404
    except PermissionError as exc:
        return jsonify({"success": False, "error": str(exc), "code": "FORBIDDEN"}), 403
    except ValueError as exc:
        return jsonify({"success": False, "error": str(exc)}), 400


@router.route("/digital-human/sessions/<session_id>/workspace", methods=["PUT"])
def select_workspace_matter(session_id):
    """幂等选择当前会话的工作台Matter；null表示显式清空。"""
    try:
        data = request.get_json(silent=True)
        if not isinstance(data, dict):
            return jsonify({"success": False, "error": "请求体必须是 JSON 对象"}), 400
        matter_id = data.get("matter_id")
        if matter_id is not None and not isinstance(matter_id, str):
            return jsonify({"success": False, "error": "matter_id 必须是字符串或null"}), 400
        expected_version = data.get("expected_version")
        if (
            not isinstance(expected_version, int)
            or isinstance(expected_version, bool)
            or expected_version < 0
        ):
            return jsonify({
                "success": False,
                "error": "expected_version 必须是非负整数",
                "code": "INVALID_INPUT",
            }), 400
        result = get_conversation_workspace_service().select_matter(
            session_id,
            matter_id,
            _get_client_id(),
            expected_version,
        )
        return jsonify({"success": True, **result})
    except (UnicodeError, SQLAlchemyError):
        return _database_unavailable("切换案件工作台")
    except LookupError as exc:
        return jsonify({"success": False, "error": str(exc)}), 404
    except PermissionError as exc:
        return jsonify({"success": False, "error": str(exc), "code": "FORBIDDEN"}), 403
    except WorkspaceVersionConflict as exc:
        return jsonify({
            "success": False,
            "error": str(exc),
            "code": "WORKSPACE_VERSION_CONFLICT",
            "current_version": exc.current_version,
        }), 409
    except ValueError as exc:
        return jsonify({"success": False, "error": str(exc)}), 400


@router.route("/digital-human/sessions/<session_id>", methods=["DELETE"])
def delete_session(session_id):
    try:
        deleted = get_digital_human_service().reset_session(session_id, _get_client_id())
        if not deleted:
            return jsonify({"success": False, "error": "会话不存在"}), 404
        return jsonify({"success": True, "message": "会话删除成功"})
    except (UnicodeError, SQLAlchemyError):
        return _database_unavailable("删除会话")
    except PermissionError as exc:
        return jsonify({"success": False, "error": str(exc), "code": "FORBIDDEN"}), 403
    except ValueError as exc:
        return jsonify({"success": False, "error": str(exc)}), 400
