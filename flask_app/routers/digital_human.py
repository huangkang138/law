"""数字人智能助手路由。"""

from flask import Blueprint, jsonify, request

from core.logger import app_logger
from services.digital_human_service import get_digital_human_service


router = Blueprint("digital_human", __name__)


def _get_custom_llm_config():
    api_key = request.headers.get("X-API-Key")
    if not api_key:
        return None
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

        result = get_digital_human_service().chat(
            question=question,
            session_id=session_id,
            custom_config=_get_custom_llm_config(),
        )
        return jsonify({"success": True, **result})
    except ValueError as exc:
        return jsonify({"success": False, "error": str(exc)}), 400
    except Exception as exc:
        app_logger.exception(f"数字人聊天接口错误: {str(exc)}")
        return jsonify({"success": False, "error": "数字人暂时无法回答，请稍后重试"}), 500


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

        get_digital_human_service().reset_session(session_id)
        return jsonify({
            "success": True,
            "message": "会话已重置",
            "session_id": session_id,
        })
    except Exception as exc:
        app_logger.exception(f"数字人重置会话接口错误: {str(exc)}")
        return jsonify({"success": False, "error": "会话重置失败"}), 500
