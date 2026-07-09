"""
法律案例相关路由
"""

from flask import Blueprint, request, jsonify
from services.case_service import CaseService
from core.logger import app_logger

router = Blueprint('case', __name__)


@router.route('/case/search', methods=['POST'])
def search_cases():
    """
    搜索相似案件
    
    请求体:
    {
        "query": "法律问题或案情描述",
        "use_web_search": true
    }
    
    返回:
    {
        "success": true,
        "cases": [
            {
                "id": "案件ID",
                "title": "案件标题",
                "case_number": "案号",
                "court": "法院",
                "date": "日期",
                "summary": "案件摘要",
                "similarity": 相似度,
                "source": "案例来源",
                "url": "案例链接"
            }
        ]
    }
    """
    try:
        app_logger.info(f"接收到的原始请求: {request.get_data()}")
        data = request.json
        app_logger.info(f"解析后的JSON: {data}")
        if not data or 'query' not in data:
            return jsonify({"error": "缺少搜索关键词"}), 400
        
        query = data['query']
        use_web_search = data.get('use_web_search', True)
        app_logger.info(f"提取的查询词: {query}, 使用网络搜索: {use_web_search}")
        
        case_service = CaseService()
        cases, search_id = case_service.search_similar_cases(query, use_web_search)
        
        return jsonify({
            "success": True,
            "cases": cases,
            "search_id": search_id
        })
    except Exception as e:
        app_logger.error(f"搜索案件错误: {str(e)}")
        return jsonify({"error": str(e)}), 500


@router.route('/case/<case_id>', methods=['GET'])
def get_case_detail(case_id):
    """
    获取案件详情
    
    返回:
    {
        "success": true,
        "case": {
            "id": "案件ID",
            "title": "案件标题",
            "case_number": "案号",
            "court": "法院",
            "date": "日期",
            "summary": "案件摘要",
            "content": "案件内容",
            "keywords": ["关键词1", "关键词2"]
        }
    }
    """
    try:
        case_service = CaseService()
        case = case_service.get_case_detail(case_id)
        
        if not case:
            return jsonify({"error": "案件不存在"}), 404
        
        return jsonify({
            "success": True,
            "case": case
        })
    except Exception as e:
        app_logger.error(f"获取案件详情错误: {str(e)}")
        return jsonify({"error": str(e)}), 500


@router.route('/case/history', methods=['GET'])
def get_search_history():
    """
    获取搜索历史
    
    返回:
    {
        "success": true,
        "history": [
            {
                "id": "历史记录ID",
                "query": "搜索关键词",
                "timestamp": "搜索时间",
                "result_count": "结果数量"
            }
        ]
    }
    """
    try:
        case_service = CaseService()
        history = case_service.get_search_history()
        
        return jsonify({
            "success": True,
            "history": history
        })
    except Exception as e:
        app_logger.error(f"获取搜索历史错误: {str(e)}")
        return jsonify({"error": str(e)}), 500


@router.route('/case/history/<search_id>', methods=['GET', 'DELETE'])
def handle_search_history(search_id):
    """
    处理搜索历史记录
    
    GET: 获取单个历史记录详情
    DELETE: 删除搜索历史记录
    
    返回:
    {
        "success": true,
        "history": {
            "id": "历史记录ID",
            "query": "搜索关键词",
            "timestamp": "搜索时间",
            "similar_cases": []
        }
    }
    """
    try:
        case_service = CaseService()
        
        if request.method == 'GET':
            # 获取单个历史记录详情
            history = case_service.get_search_history_detail(search_id)
            if not history:
                return jsonify({"error": "历史记录不存在"}), 404
            
            return jsonify({
                "success": True,
                "history": history
            })
        elif request.method == 'DELETE':
            # 删除搜索历史记录
            success = case_service.delete_search_history(search_id)
            return jsonify({
                "success": success
            })
            
    except Exception as e:
        app_logger.error(f"处理搜索历史错误: {str(e)}")
        return jsonify({"error": str(e)}), 500