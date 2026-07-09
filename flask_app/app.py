"""
YYS-Law Flask 后端主应用
"""

import os
import sys
from flask import Flask, jsonify
from flask_cors import CORS
from flask_sock import Sock

# 添加当前目录到 Python 路径
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from core.config import settings
from core.logger import app_logger
from core.database import engine, Base
from models.db_models import User, Contract, ContractRisk, LegalChatSession, LegalChatMessage, Case, CourtSession, Evidence, LegalIssue, DebateTurn, LegalCase, CaseExplanationSearch, DocumentDraft, LegalDocumentDraft, ContractDraft, LegalOpinionDraft, CaseAnalysis, SimilarDocumentSearch, DisputeInfo, EvidenceRecord, RightsProtectionPath, LegalDocument, CasePrediction, CaseReminder, RiskWarning, InterestCalculation, LaborCompensation, TrafficAccidentCompensation, CourtFee, WorkInjuryCompensation, LawyerFee, LegalCalendarEvent, LimitationCheck, ContractPenalty, PreservationFee, ExecutionFee, WillFee, AnnouncementFee, AppraisalFee, ArbitrationFee, UMLDiagram, Favorite, Agent, AgentUsage
from models.knowledge_graph import KnowledgeNode, KnowledgeRelationship
from services.legal_agent import get_legal_agent
from routers import analysis_bp, case_bp, dispute_bp, document_bp, document_drafting_bp, health_bp, knowledge_graph_bp, legal_bp, legal_tools_bp, favorites_bp
from routers import courtroom_websocket, agent_bp

app = Flask(__name__)
app.config['JSON_AS_ASCII'] = False  # 确保JSON中的中文不被转义为Unicode
app.url_map.strict_slashes = False  # 禁用严格斜杠模式
CORS(app, origins=settings.CORS_ORIGINS, supports_credentials=True, allow_headers=['Content-Type', 'Authorization', 'X-API-Key', 'X-API-Base-URL', 'X-API-Model'], expose_headers=['Content-Type', 'X-Accel-Buffering'])

# 初始化 WebSocket 支持
sock = Sock(app)

# 创建数据库表
try:
    # 只创建不存在的表，不删除已有表
    Base.metadata.create_all(bind=engine)
    app_logger.info("✅ 数据库表检查完成")
except Exception as e:
    app_logger.error(f"❌ 数据库表创建失败: {e}")
    import traceback
    traceback.print_exc()

# 初始化服务
legal_agent = None
def init_services():
    """初始化服务"""
    global legal_agent
    try:
        legal_agent = get_legal_agent()
        app_logger.info("✅ 所有服务初始化完成")
    except Exception as e:
        app_logger.warning(f"⚠️ 部分服务初始化失败 (知识图谱功能仍可使用): {e}")
        # 不抛出异常，让服务继续启动
    
    return True

# 注册路由
app.register_blueprint(health_bp, url_prefix="/api")
app.register_blueprint(legal_bp, url_prefix="/api")
app.register_blueprint(document_bp, url_prefix="/api")
app.register_blueprint(analysis_bp, url_prefix="/api")
app.register_blueprint(dispute_bp, url_prefix="/api")
app.register_blueprint(knowledge_graph_bp, url_prefix="/api")
app.register_blueprint(case_bp, url_prefix="/api")
app.register_blueprint(document_drafting_bp, url_prefix="/api")
app.register_blueprint(legal_tools_bp, url_prefix="/api")
app.register_blueprint(favorites_bp)
app.register_blueprint(agent_bp)

# 注册 WebSocket 路由
@sock.route('/api/courtroom/ws/<session_id>')
def courtroom_websocket_route(ws, session_id):
    """庭审 WebSocket 路由 - 使用真实 CourtroomEngine 提供完整对话流"""
    import json
    import logging
    import threading
    from flask import request
    
    logger = logging.getLogger(__name__)
    logger.info(f"收到 WebSocket 连接请求: session_id={session_id}")
    
    # 从查询参数获取用户角色
    user_role = request.args.get('user_role', 'auto')
    case_description = request.args.get('case_description', '')
    logger.info(f"用户角色: {user_role}, 案件描述长度: {len(case_description)}")
    
    try:
        # 导入庭审 WebSocket 服务
        from services.courtroom_websocket_service import get_courtroom_websocket_service
        
        # 获取服务实例
        service = get_courtroom_websocket_service()
        
        # 启动庭审会话（在后台线程中运行）
        session_thread = threading.Thread(
            target=service.start_session,
            args=(ws, session_id, user_role, case_description)
        )
        session_thread.daemon = True
        session_thread.start()
        
        # 持续处理客户端消息
        logger.info("开始处理客户端消息")
        while True:
            try:
                data = ws.receive()
                if not data:
                    break
                
                logger.info(f"收到客户端消息: {data}")
                
                try:
                    data = json.loads(data)
                    message_type = data.get('type')
                    
                    if message_type == 'user_input':
                        content = data.get('content', '')
                        logger.info(f"处理用户输入: {content}")
                        
                        # 使用服务处理用户输入
                        success = service.handle_user_input(session_id, content)
                        if not success:
                            ws.send(json.dumps({
                                'type': 'error',
                                'message': '当前不是您的发言时间'
                            }))
                        
                    elif message_type == 'end_session':
                        service.end_session(session_id)
                        ws.send(json.dumps({
                            'type': 'message',
                            'role': 'judge',
                            'content': '庭审结束。',
                            'phase': 'closing'
                        }))
                        break
                        
                except json.JSONDecodeError:
                    logger.error("消息解析失败")
                    ws.send(json.dumps({
                        'type': 'error',
                        'message': '消息格式错误'
                    }))
                    
            except Exception as receive_error:
                # 检查是否是连接关闭错误
                if 'ConnectionClosed' in str(type(receive_error)):
                    logger.info(f"客户端正常断开连接: {receive_error}")
                    break
                else:
                    raise receive_error
                
    except Exception as e:
        logger.error(f"WebSocket 错误: {e}")
        import traceback
        traceback.print_exc()
        try:
            ws.send(json.dumps({
                'type': 'error',
                'message': f'服务器错误: {str(e)}'
            }))
        except:
            pass
    finally:
        try:
            from services.courtroom_websocket_service import get_courtroom_websocket_service
            service = get_courtroom_websocket_service()
            service.end_session(session_id)
        except:
            pass
        logger.info(f"WebSocket 连接已关闭: {session_id}")

# 根路径
@app.route("/")
def root():
    """根路径"""
    return jsonify({
        "name": settings.APP_NAME,
        "version": settings.APP_VERSION,
        "status": "running",
        "docs": "/api/docs",
        "health": "/api/health"
    })

# API 文档
@app.route("/api/docs")
def api_docs():
    """API 文档"""
    return jsonify({
        "endpoints": {
            "/api/health": "健康检查",
            "/api/legal/chat": "法律咨询对话",
            "/api/legal/reset": "重置会话",
            "/api/document/upload": "上传合同",
            "/api/document/review": "合同审查",
            "/api/analysis/debate/start": "模拟法庭"
        },
        "version": settings.APP_VERSION
    })

if __name__ == "__main__":
    app_logger.info(f"🚀 {settings.APP_NAME} v{settings.APP_VERSION} 启动中...")
    app_logger.info(f"📊 LLM 模式: {settings.LLM_MODE}")
    app_logger.info(f"🔧 调试模式: {settings.DEBUG}")
    
    try:
        init_services()
        app_logger.info("✅ 所有服务初始化完成，启动 Flask 服务器...")
        app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 8001)), debug=settings.DEBUG)
    except Exception as e:
        app_logger.error(f"❌ 启动失败: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
