"""
法律咨询路由
"""

from flask import Blueprint, request, jsonify
from models.request import ChatRequest, ResetRequest
from services.legal_agent import get_legal_agent
from core.logger import app_logger

router = Blueprint('legal', __name__)


@router.route('/legal/chat', methods=['POST'])
def chat():
    """
    法律咨询接口
    
    接收用户问题，返回 AI 回答
    
    - **question**: 用户问题（必填）
    - **session_id**: 会话ID（可选，默认为 "default"）
    - **jurisdiction**: 法律辖区（可选，默认为 "中国"）
    
    请求头（可选）：
    - **X-API-Key**: 自定义 API Key
    - **X-API-Base-URL**: 自定义 API Base URL
    - **X-API-Model**: 自定义模型名称
    """
    try:
        # 解析请求数据
        data = request.json
        if not data or 'question' not in data:
            return jsonify({"error": "缺少必要参数 question"}), 400
        
        # 构建请求对象
        chat_request = ChatRequest(
            question=data.get('question'),
            session_id=data.get('session_id', 'default'),
            jurisdiction=data.get('jurisdiction', '中国')
        )
        
        # 获取自定义配置
        x_api_key = request.headers.get('X-API-Key')
        x_api_base_url = request.headers.get('X-API-Base-URL')
        x_api_model = request.headers.get('X-API-Model')
        
        custom_config = None
        if x_api_key:
            custom_config = {
                "api_key": x_api_key,
                "base_url": x_api_base_url,
                "model": x_api_model
            }
            app_logger.info(f"使用自定义 LLM 配置: model={x_api_model}, base_url={x_api_base_url}")
        
        # 调用法律代理
        result = get_legal_agent().chat(
            question=chat_request.question,
            session_id=chat_request.session_id,
            custom_config=custom_config
        )
        
        return jsonify({
            "success": True,
            "answer": result["answer"],
            "session_id": result["session_id"],
            "tokens": result.get("tokens")
        })
        
    except Exception as e:
        app_logger.error(f"聊天接口错误: {str(e)}")
        return jsonify({"error": str(e)}), 500


@router.route('/legal/reset', methods=['POST'])
def reset_session():
    """
    重置会话接口
    
    重置指定会话的上下文
    
    - **session_id**: 会话ID（可选，默认为 "default"）
    """
    try:
        # 解析请求数据
        data = request.json
        reset_request = ResetRequest(
            session_id=data.get('session_id', 'default') if data else 'default'
        )
        
        # 调用法律代理重置会话
        get_legal_agent().reset_session(reset_request.session_id)
        
        return jsonify({
            "success": True,
            "message": "会话重置成功",
            "session_id": reset_request.session_id
        })
        
    except Exception as e:
        app_logger.error(f"重置会话错误: {str(e)}")
        return jsonify({"error": str(e)}), 500


@router.route('/legal/sessions', methods=['GET'])
def get_sessions():
    """
    获取所有普法问答会话列表
    
    返回所有会话的基本信息，包括标题、创建时间、最后消息等
    """
    try:
        sessions = get_legal_agent().get_all_sessions()
        return jsonify({
            "success": True,
            "sessions": sessions
        })
    except Exception as e:
        app_logger.error(f"获取会话列表错误: {str(e)}")
        return jsonify({"error": str(e)}), 500


@router.route('/legal/sessions/<session_id>/messages', methods=['GET'])
def get_session_messages(session_id: str):
    """
    获取指定会话的所有消息
    
    Args:
        session_id: 会话ID
        
    Returns:
        会话的所有消息列表
    """
    try:
        from core.database import SessionLocal
        from models.db_models import LegalChatSession
        
        # 获取会话信息
        db = SessionLocal()
        session = db.query(LegalChatSession).filter(LegalChatSession.id == session_id).first()
        db.close()
        
        title = session.title if session else '历史会话'
        
        # 获取消息
        messages = get_legal_agent().get_session_messages(session_id)
        
        return jsonify({
            "success": True,
            "session_id": session_id,
            "title": title,
            "messages": messages
        })
    except Exception as e:
        app_logger.error(f"获取会话消息错误: {str(e)}")
        return jsonify({"error": str(e)}), 500


@router.route('/legal/sessions/<session_id>', methods=['DELETE'])
def delete_session(session_id: str):
    """
    删除指定会话
    
    Args:
        session_id: 会话ID
        
    Returns:
        删除结果
    """
    try:
        from core.database import SessionLocal
        from models.db_models import LegalChatSession, LegalChatMessage
        
        db = SessionLocal()
        try:
            # 删除会话的所有消息
            db.query(LegalChatMessage).filter(LegalChatMessage.session_id == session_id).delete()
            # 删除会话
            session = db.query(LegalChatSession).filter(LegalChatSession.id == session_id).first()
            if session:
                db.delete(session)
                db.commit()
                return jsonify({
                    "success": True,
                    "message": "会话删除成功"
                })
            else:
                return jsonify({
                    "success": False,
                    "error": "会话不存在"
                }), 404
        finally:
            db.close()
            
    except Exception as e:
        app_logger.error(f"删除会话错误: {str(e)}")
        return jsonify({"error": str(e)}), 500


@router.route('/legal/sessions/<session_id>', methods=['PUT'])
def update_session(session_id: str):
    """
    更新会话标题
    
    Args:
        session_id: 会话ID
        
    Request Body:
        - title: 新的会话标题
        
    Returns:
        更新结果
    """
    try:
        from core.database import SessionLocal
        from models.db_models import LegalChatSession
        
        data = request.json
        if not data or 'title' not in data:
            return jsonify({"error": "缺少必要参数 title"}), 400
        
        new_title = data.get('title')
        
        db = SessionLocal()
        try:
            session = db.query(LegalChatSession).filter(LegalChatSession.id == session_id).first()
            if session:
                session.title = new_title
                db.commit()
                return jsonify({
                    "success": True,
                    "message": "会话标题更新成功",
                    "title": new_title
                })
            else:
                return jsonify({
                    "success": False,
                    "error": "会话不存在"
                }), 404
        finally:
            db.close()
            
    except Exception as e:
        app_logger.error(f"更新会话错误: {str(e)}")
        return jsonify({"error": str(e)}), 500
