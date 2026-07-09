"""
健康检查路由
"""

from flask import Blueprint, jsonify
from core.config import settings
from services.llm_factory import LLMFactory

router = Blueprint('health', __name__)


@router.route('/health', methods=['GET'])
def health_check():
    """
    健康检查接口
    
    返回服务状态、版本信息和 LLM 配置
    """
    llm_info = LLMFactory.get_llm_info()
    
    return jsonify({
        "status": "healthy",
        "service": settings.APP_NAME,
        "version": settings.APP_VERSION,
        "llm": llm_info
    })
