from flask import Blueprint, request, jsonify
from services.legal_agent import LegalAgentService
from models.db_models import DocumentDraft, LegalDocumentDraft, ContractDraft, LegalOpinionDraft
from core.database import SessionLocal
import logging

logger = logging.getLogger(__name__)

document_drafting_bp = Blueprint('document_drafting', __name__)

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

@document_drafting_bp.route('/document/draft', methods=['POST'])
def draft_document():
    """
    起草法律文书
    """
    try:
        data = request.get_json()
        if not data:
            return jsonify({'success': False, 'error': '缺少请求数据'}), 400

        user_input = data.get('input')
        document_type = data.get('type', 'legal-document')
        user_id = data.get('user_id', 'anonymous')
        title = data.get('title', user_input[:30] if user_input else '未命名')
        details = data.get('details', {})

        if not user_input:
            return jsonify({'success': False, 'error': '缺少输入内容'}), 400

        logger.info(f"开始起草{document_type}，内容: {user_input[:100]}...")

        # 使用法律代理生成文书
        agent = LegalAgentService()
        result = agent.draft_document(user_input, document_type)

        # 保存到数据库
        db = next(get_db())
        draft = DocumentDraft(
            user_id=user_id,
            document_type=document_type,
            title=title,
            content=user_input,
            result=result,
            status='completed',
            is_pinned=False
        )
        db.add(draft)
        db.flush()

        # 保存详情信息
        if document_type == 'legal-document':
            legal_doc = LegalDocumentDraft(
                draft_id=draft.id,
                template_type=details.get('template_type'),
                case_summary=details.get('case_summary'),
                uploaded_files=details.get('uploaded_files')
            )
            db.add(legal_doc)
        elif document_type == 'contract-drafting':
            contract = ContractDraft(
                draft_id=draft.id,
                contract_type=details.get('contract_type'),
                parties_info=details.get('parties_info'),
                contract_purpose=details.get('contract_purpose'),
                terms_summary=details.get('terms_summary'),
                uploaded_files=details.get('uploaded_files')
            )
            db.add(contract)
        elif document_type == 'legal-opinion':
            opinion = LegalOpinionDraft(
                draft_id=draft.id,
                current_step=details.get('current_step', 4),
                case_summary=details.get('case_summary'),
                case_organized=details.get('case_organized'),
                analysis_focus=details.get('analysis_focus'),
                selected_court=details.get('selected_court'),
                uploaded_files=details.get('uploaded_files')
            )
            db.add(opinion)

        db.commit()
        db.refresh(draft)

        return jsonify({
            'success': True,
            'data': {
                'document_id': draft.id,
                'content': result,
                'type': document_type,
                'title': draft.title,
                'created_at': draft.created_at.isoformat()
            }
        })
    except Exception as e:
        logger.error(f"起草文书失败: {str(e)}")
        return jsonify({'success': False, 'error': f'起草失败: {str(e)}'}), 500

@document_drafting_bp.route('/document/list', methods=['GET'])
def list_documents():
    """
    获取用户的起草记录
    """
    try:
        user_id = request.args.get('user_id', 'anonymous')
        document_type = request.args.get('type')
        limit = int(request.args.get('limit', 50))
        offset = int(request.args.get('offset', 0))

        db = next(get_db())
        query = db.query(DocumentDraft).filter_by(user_id=user_id)
        
        if document_type:
            query = query.filter_by(document_type=document_type)
        
        drafts = query.order_by(DocumentDraft.is_pinned.desc(), DocumentDraft.created_at.desc())\
            .limit(limit)\
            .offset(offset)\
            .all()

        result = []
        for draft in drafts:
            result.append({
                'id': draft.id,
                'type': draft.document_type,
                'title': draft.title,
                'content': draft.content,
                'result': draft.result,
                'status': draft.status,
                'is_pinned': draft.is_pinned,
                'custom_title': draft.custom_title,
                'created_at': draft.created_at.isoformat(),
                'updated_at': draft.updated_at.isoformat()
            })

        total = query.count()

        return jsonify({
            'success': True,
            'data': {
                'drafts': result,
                'total': total,
                'limit': limit,
                'offset': offset
            }
        })
    except Exception as e:
        logger.error(f"获取起草记录失败: {str(e)}")
        return jsonify({'success': False, 'error': f'获取记录失败: {str(e)}'}), 500

@document_drafting_bp.route('/document/<int:document_id>', methods=['GET'])
def get_document(document_id):
    """
    获取单个起草文档
    """
    try:
        db = next(get_db())
        draft = db.query(DocumentDraft).get(document_id)
        if not draft:
            return jsonify({'success': False, 'error': '文档不存在'}), 404

        # 获取详情信息
        details = None
        if draft.document_type == 'legal-document':
            legal_doc = db.query(LegalDocumentDraft).filter_by(draft_id=draft.id).first()
            if legal_doc:
                details = {
                    'template_type': legal_doc.template_type,
                    'case_summary': legal_doc.case_summary,
                    'uploaded_files': legal_doc.uploaded_files
                }
        elif draft.document_type == 'contract-drafting':
            contract = db.query(ContractDraft).filter_by(draft_id=draft.id).first()
            if contract:
                details = {
                    'contract_type': contract.contract_type,
                    'parties_info': contract.parties_info,
                    'contract_purpose': contract.contract_purpose,
                    'terms_summary': contract.terms_summary,
                    'uploaded_files': contract.uploaded_files
                }
        elif draft.document_type == 'legal-opinion':
            opinion = db.query(LegalOpinionDraft).filter_by(draft_id=draft.id).first()
            if opinion:
                details = {
                    'current_step': opinion.current_step,
                    'case_summary': opinion.case_summary,
                    'case_organized': opinion.case_organized,
                    'analysis_focus': opinion.analysis_focus,
                    'selected_court': opinion.selected_court,
                    'uploaded_files': opinion.uploaded_files
                }

        return jsonify({
            'success': True,
            'data': {
                'id': draft.id,
                'type': draft.document_type,
                'title': draft.title,
                'content': draft.content,
                'result': draft.result,
                'status': draft.status,
                'is_pinned': draft.is_pinned,
                'custom_title': draft.custom_title,
                'created_at': draft.created_at.isoformat(),
                'updated_at': draft.updated_at.isoformat(),
                'details': details
            }
        })
    except Exception as e:
        logger.error(f"获取文档失败: {str(e)}")
        return jsonify({'success': False, 'error': f'获取失败: {str(e)}'}), 500

@document_drafting_bp.route('/document/<int:document_id>', methods=['PUT'])
def update_document(document_id):
    """
    更新文档信息
    """
    try:
        data = request.get_json()
        db = next(get_db())
        draft = db.query(DocumentDraft).get(document_id)
        if not draft:
            return jsonify({'success': False, 'error': '文档不存在'}), 404

        if 'title' in data:
            draft.title = data['title']
        if 'custom_title' in data:
            draft.custom_title = data['custom_title']
        if 'is_pinned' in data:
            draft.is_pinned = data['is_pinned']
        if 'result' in data:
            draft.result = data['result']

        db.commit()
        db.refresh(draft)

        return jsonify({
            'success': True,
            'data': {
                'id': draft.id,
                'title': draft.title,
                'custom_title': draft.custom_title,
                'is_pinned': draft.is_pinned,
                'updated_at': draft.updated_at.isoformat()
            }
        })
    except Exception as e:
        logger.error(f"更新文档失败: {str(e)}")
        return jsonify({'success': False, 'error': f'更新失败: {str(e)}'}), 500

@document_drafting_bp.route('/document/<int:document_id>', methods=['DELETE'])
def delete_document(document_id):
    """
    删除起草文档
    """
    try:
        db = next(get_db())
        draft = db.query(DocumentDraft).get(document_id)
        if not draft:
            return jsonify({'success': False, 'error': '文档不存在'}), 404

        # 删除关联的详情记录
        if draft.document_type == 'legal-document':
            db.query(LegalDocumentDraft).filter_by(draft_id=draft.id).delete()
        elif draft.document_type == 'contract-drafting':
            db.query(ContractDraft).filter_by(draft_id=draft.id).delete()
        elif draft.document_type == 'legal-opinion':
            db.query(LegalOpinionDraft).filter_by(draft_id=draft.id).delete()

        db.delete(draft)
        db.commit()

        return jsonify({'success': True, 'message': '文档已删除'})
    except Exception as e:
        logger.error(f"删除文档失败: {str(e)}")
        return jsonify({'success': False, 'error': f'删除失败: {str(e)}'}), 500

@document_drafting_bp.route('/document/<int:document_id>/toggle-pin', methods=['POST'])
def toggle_pin(document_id):
    """
    切换文档置顶状态
    """
    try:
        db = next(get_db())
        draft = db.query(DocumentDraft).get(document_id)
        if not draft:
            return jsonify({'success': False, 'error': '文档不存在'}), 404

        draft.is_pinned = not draft.is_pinned
        db.commit()
        db.refresh(draft)

        return jsonify({
            'success': True,
            'data': {
                'id': draft.id,
                'is_pinned': draft.is_pinned
            }
        })
    except Exception as e:
        logger.error(f"切换置顶状态失败: {str(e)}")
        return jsonify({'success': False, 'error': f'操作失败: {str(e)}'}), 500
