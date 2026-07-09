"""
工具函数
"""

import json
from flask_app.core.logger import app_logger


def jsonify_response(data: dict, status_code: int = 200) -> tuple:
    """
    统一 JSON 响应格式
    
    Args:
        data: 响应数据
        status_code: 状态码
        
    Returns:
        (响应数据, 状态码)
    """
    return data, status_code


def safe_parse_json(data: str) -> dict:
    """
    安全解析 JSON
    
    Args:
        data: JSON 字符串
        
    Returns:
        解析后的字典
    """
    try:
        return json.loads(data)
    except json.JSONDecodeError as e:
        app_logger.error(f"JSON 解析错误: {str(e)}")
        return {}
