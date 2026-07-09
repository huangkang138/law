"""
收藏相关路由
"""

from flask import Blueprint, request, jsonify
from models.db_models import Favorite
from core.database import get_db
import uuid
from sqlalchemy import func
from datetime import datetime, timedelta

favorites_bp = Blueprint('favorites', __name__)


@favorites_bp.route('/api/favorites', methods=['GET'])
def get_favorites():
    """
    获取所有收藏
    """
    try:
        db = next(get_db())
        favorites = db.query(Favorite).order_by(Favorite.created_at.desc()).all()
        
        # 计算统计数据
        total_count = db.query(func.count(Favorite.id)).scalar() or 0
        
        # 今日新增收藏
        today = datetime.now().date()
        today_count = db.query(func.count(Favorite.id)).filter(
            func.date(Favorite.created_at) == today
        ).scalar() or 0
        
        # 本月收藏数
        this_month = datetime.now().month
        this_year = datetime.now().year
        monthly_count = db.query(func.count(Favorite.id)).filter(
            func.extract('month', Favorite.created_at) == this_month,
            func.extract('year', Favorite.created_at) == this_year
        ).scalar() or 0
        
        favorites_list = []
        for fav in favorites:
            favorites_list.append({
                'id': fav.id,
                'title': fav.title,
                'content': fav.content,
                'source_type': fav.source_type,
                'source_id': fav.source_id,
                'created_at': fav.created_at.isoformat(),
                'updated_at': fav.updated_at.isoformat() if fav.updated_at else None
            })
        
        return jsonify({
            'favorites': favorites_list,
            'total_count': total_count,
            'today_count': today_count,
            'monthly_count': monthly_count
        }), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@favorites_bp.route('/api/favorites', methods=['POST'])
def create_favorite():
    """
    创建新收藏
    """
    try:
        data = request.get_json()
        if not data or 'title' not in data or 'content' not in data or 'source_type' not in data:
            return jsonify({'error': '缺少必要参数'}), 400
        
        db = next(get_db())
        new_favorite = Favorite(
            id=str(uuid.uuid4()),
            title=data['title'],
            content=data['content'],
            source_type=data['source_type'],
            source_id=data.get('source_id')
        )
        
        db.add(new_favorite)
        db.commit()
        db.refresh(new_favorite)
        
        return jsonify({
            'id': new_favorite.id,
            'title': new_favorite.title,
            'content': new_favorite.content,
            'source_type': new_favorite.source_type,
            'source_id': new_favorite.source_id,
            'created_at': new_favorite.created_at.isoformat(),
            'updated_at': new_favorite.updated_at.isoformat() if new_favorite.updated_at else None
        }), 201
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@favorites_bp.route('/api/favorites/<favorite_id>', methods=['DELETE'])
def delete_favorite(favorite_id):
    """
    删除收藏
    """
    try:
        db = next(get_db())
        favorite = db.query(Favorite).filter(Favorite.id == favorite_id).first()
        if not favorite:
            return jsonify({'error': '收藏不存在'}), 404
        
        db.delete(favorite)
        db.commit()
        
        return jsonify({'message': '收藏删除成功'}), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@favorites_bp.route('/api/favorites/<favorite_id>', methods=['PUT'])
def update_favorite(favorite_id):
    """
    更新收藏
    """
    try:
        data = request.get_json()
        if not data:
            return jsonify({'error': '缺少更新数据'}), 400
        
        db = next(get_db())
        favorite = db.query(Favorite).filter(Favorite.id == favorite_id).first()
        if not favorite:
            return jsonify({'error': '收藏不存在'}), 404
        
        if 'title' in data:
            favorite.title = data['title']
        if 'content' in data:
            favorite.content = data['content']
        if 'source_type' in data:
            favorite.source_type = data['source_type']
        if 'source_id' in data:
            favorite.source_id = data['source_id']
        
        db.commit()
        db.refresh(favorite)
        
        return jsonify({
            'id': favorite.id,
            'title': favorite.title,
            'content': favorite.content,
            'source_type': favorite.source_type,
            'source_id': favorite.source_id,
            'created_at': favorite.created_at.isoformat(),
            'updated_at': favorite.updated_at.isoformat() if favorite.updated_at else None
        }), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500