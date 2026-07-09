"""
智能分析路由
提供合同审查和多智能体辩论接口

采用最严密、最复杂、最高级的逻辑解析
基于真实 LLM 智能分析，保障人民权益
"""

from flask import Blueprint, request, jsonify
from core.logger import app_logger
from services.courtroom_engine import (
    get_courtroom_engine, 
    Party, 
    DebatePhase,
    CourtroomEngine
)

router = Blueprint('analysis', __name__)


# ==================== 模拟法庭辩论接口 ====================

@router.route('/debate/start', methods=['POST'])
def start_debate():
    """
    启动模拟法庭辩论
    
    创建新的庭审会话，使用 LLM 深度分析案件
    提供最严密、最复杂的法庭辩论模拟
    """
    try:
        data = request.json
        if not data or 'case_description' not in data:
            return jsonify({
                "success": False,
                "error": "缺少必要参数 case_description"
            }), 400
        
        case_description = data.get('case_description')
        case_type = data.get('case_type', '民事纠纷')
        
        app_logger.info(f"启动模拟法庭，案件描述长度: {len(case_description)} 字符")
        
        # 获取模拟法庭引擎
        engine = get_courtroom_engine()
        
        # 创建庭审会话
        session = engine.create_session(case_description, case_type)
        
        # 生成原告开庭陈述
        plaintiff_opening = engine.generate_opening_statement(session.id, Party.PLAINTIFF)
        
        # 生成被告开庭陈述
        defendant_opening = engine.generate_opening_statement(session.id, Party.DEFENDANT)
        
        app_logger.info(f"模拟法庭启动成功，会话ID: {session.id}")
        
        return jsonify({
            "success": True,
            "session_id": session.id,
            "case_title": session.case.title,
            "case_type": session.case.case_type,
            "current_phase": session.current_phase.value,
            "plaintiff_opening": {
                "content": plaintiff_opening,
                "legal_basis": "",
                "arguments": []
            },
            "defendant_opening": {
                "content": defendant_opening,
                "legal_basis": "",
                "arguments": []
            },
            "legal_issues": [
                {
                    "id": issue.id,
                    "description": issue.description,
                    "relevant_law": issue.relevant_law,
                    "plaintiff_position": issue.plaintiff_position,
                    "defendant_position": issue.defendant_position
                }
                for issue in session.case.legal_issues
            ]
        })
        
    except Exception as e:
        app_logger.error(f"启动模拟法庭错误: {str(e)}")
        import traceback
        traceback.print_exc()
        return jsonify({
            "success": False,
            "error": str(e)
        }), 500


@router.route('/debate/<session_id>/submit_evidence', methods=['POST'])
def submit_evidence(session_id: str):
    """
    提交证据
    
    支持原告或被告提交证据，系统会自动评估证据证明力
    """
    try:
        data = request.json
        if not data:
            return jsonify({
                "success": False,
                "error": "缺少请求数据"
            }), 400
        
        party_str = data.get('party')
        evidence_name = data.get('evidence_name')
        evidence_content = data.get('evidence_content')
        evidence_type = data.get('evidence_type', '书证')
        
        if not all([party_str, evidence_name, evidence_content]):
            return jsonify({
                "success": False,
                "error": "缺少必要参数：party、evidence_name、evidence_content"
            }), 400
        
        # 转换当事人
        party = Party.PLAINTIFF if party_str == 'plaintiff' else Party.DEFENDANT
        
        engine = get_courtroom_engine()
        evidence = engine.submit_evidence(
            session_id, party, evidence_name, evidence_content, evidence_type
        )
        
        app_logger.info(f"证据提交成功: {evidence.name}, 证明力: {evidence.probative_force}")
        
        return jsonify({
            "success": True,
            "evidence": {
                "id": evidence.id,
                "name": evidence.name,
                "evidence_type": evidence.evidence_type,
                "probative_force": evidence.probative_force,
                "party": evidence.party.value
            }
        })
        
    except Exception as e:
        app_logger.error(f"提交证据错误: {str(e)}")
        import traceback
        traceback.print_exc()
        return jsonify({
            "success": False,
            "error": str(e)
        }), 500


@router.route('/debate/<session_id>/authenticate_evidence', methods=['POST'])
def authenticate_evidence(session_id: str):
    """
    质证
    
    对对方提交的证据进行质证，系统会分析质证意见的有效性
    """
    try:
        data = request.json
        if not data:
            return jsonify({
                "success": False,
                "error": "缺少请求数据"
            }), 400
        
        evidence_id = data.get('evidence_id')
        party_str = data.get('party')
        opinion = data.get('opinion')
        
        if not all([evidence_id, party_str, opinion]):
            return jsonify({
                "success": False,
                "error": "缺少必要参数：evidence_id、party、opinion"
            }), 400
        
        party = Party.PLAINTIFF if party_str == 'plaintiff' else Party.DEFENDANT
        
        engine = get_courtroom_engine()
        result = engine.authenticate_evidence(session_id, evidence_id, party, opinion)
        
        app_logger.info(f"质证完成: {evidence_id}")
        
        return jsonify({
            "success": True,
            "result": result
        })
        
    except Exception as e:
        app_logger.error(f"质证错误: {str(e)}")
        import traceback
        traceback.print_exc()
        return jsonify({
            "success": False,
            "error": str(e)
        }), 500


@router.route('/debate/<session_id>/argument', methods=['POST'])
def generate_argument(session_id: str):
    """
    生成法庭辩论意见
    
    基于案件信息和辩论历史，生成专业的法庭辩论意见
    """
    try:
        data = request.json or {}
        party_str = data.get('party', 'plaintiff')
        
        party = Party.PLAINTIFF if party_str == 'plaintiff' else Party.DEFENDANT
        
        engine = get_courtroom_engine()
        argument_turn = engine.generate_argument(session_id, party)
        
        app_logger.info(f"法庭辩论意见生成完成: {argument_turn.id}")
        
        return jsonify({
            "success": True,
            "argument": {
                "id": argument_turn.id,
                "party": argument_turn.party.value,
                "speaker_role": argument_turn.speaker_role,
                "content": argument_turn.content,
                "legal_basis": argument_turn.legal_basis,
                "facts_stated": argument_turn.facts_stated,
                "arguments_made": argument_turn.arguments_made,
                "counter_arguments": argument_turn.counter_arguments
            },
            "current_phase": engine.sessions[session_id].current_phase.value
        })
        
    except Exception as e:
        app_logger.error(f"生成辩论意见错误: {str(e)}")
        import traceback
        traceback.print_exc()
        return jsonify({
            "success": False,
            "error": str(e)
        }), 500


@router.route('/debate/<session_id>/closing', methods=['POST'])
def generate_closing(session_id: str):
    """
    生成最后陈述
    
    基于完整的辩论历史，生成总结性的最后陈述
    """
    try:
        data = request.json or {}
        party_str = data.get('party', 'plaintiff')
        
        party = Party.PLAINTIFF if party_str == 'plaintiff' else Party.DEFENDANT
        
        engine = get_courtroom_engine()
        closing_turn = engine.generate_closing_statement(session_id, party)
        
        app_logger.info(f"最后陈述生成完成: {closing_turn.id}")
        
        return jsonify({
            "success": True,
            "closing": {
                "id": closing_turn.id,
                "party": closing_turn.party.value,
                "speaker_role": closing_turn.speaker_role,
                "content": closing_turn.content
            },
            "current_phase": engine.sessions[session_id].current_phase.value
        })
        
    except Exception as e:
        app_logger.error(f"生成最后陈述错误: {str(e)}")
        import traceback
        traceback.print_exc()
        return jsonify({
            "success": False,
            "error": str(e)
        }), 500


@router.route('/debate/<session_id>/verdict', methods=['POST'])
def generate_verdict(session_id: str):
    """
    生成判决
    
    基于完整的庭审记录，生成专业的判决书
    """
    try:
        engine = get_courtroom_engine()
        verdict_result, verdict_reasoning = engine.generate_verdict(session_id)
        
        session = engine.sessions[session_id]
        
        app_logger.info(f"判决书生成完成: {session_id}")
        
        return jsonify({
            "success": True,
            "verdict": {
                "result": verdict_result,
                "reasoning": verdict_reasoning,
                "full_content": session.debate_history[-1].content if session.debate_history else ""
            },
            "case_summary": {
                "title": session.case.title,
                "legal_issues_resolved": [
                    {
                        "description": issue.description,
                        "conclusion": issue.conclusion
                    }
                    for issue in session.case.legal_issues if issue.is_resolved
                ]
            },
            "current_phase": session.current_phase.value,
            "is_active": session.is_active
        })
        
    except Exception as e:
        app_logger.error(f"生成判决错误: {str(e)}")
        import traceback
        traceback.print_exc()
        return jsonify({
            "success": False,
            "error": str(e)
        }), 500


@router.route('/debate/user-input', methods=['POST'])
def submit_user_input():
    """
    提交用户输入
    
    接收用户在语音庭审模式下的发言内容
    """
    try:
        data = request.json
        if not data:
            return jsonify({
                "success": False,
                "error": "缺少请求数据"
            }), 400
        
        session_id = data.get('session_id')
        user_role = data.get('user_role')
        content = data.get('content')
        
        if not all([session_id, user_role, content]):
            return jsonify({
                "success": False,
                "error": "缺少必要参数：session_id、user_role、content"
            }), 400
        
        app_logger.info(f"收到用户输入: 角色={user_role}, 内容长度={len(content)} 字符")
        
        # 获取模拟法庭引擎
        engine = get_courtroom_engine()
        
        # 存储用户输入
        if session_id in engine.sessions:
            session = engine.sessions[session_id]
            
            # 记录用户发言
            from services.courtroom_engine import DebateTurnData, DebatePhase, Party
            
            party = Party.PLAINTIFF if user_role == 'plaintiff' else Party.DEFENDANT
            
            debate_turn = DebateTurnData(
                id=str(uuid.uuid4()),
                phase=session.current_phase,
                party=party,
                speaker_role="用户",
                content=content
            )
            session.debate_history.append(debate_turn)
            
            app_logger.info(f"用户输入已记录: {debate_turn.id}")
        
        return jsonify({
            "success": True,
            "message": "用户输入已提交"
        })
        
    except Exception as e:
        app_logger.error(f"提交用户输入错误: {str(e)}")
        import traceback
        traceback.print_exc()
        return jsonify({
            "success": False,
            "error": str(e)
        }), 500


@router.route('/debate/<session_id>/status', methods=['GET'])
def get_debate_status(session_id: str):
    """
    获取庭审状态
    
    查询当前庭审会话的状态信息
    """
    try:
        engine = get_courtroom_engine()
        status = engine.get_session_status(session_id)
        
        return jsonify({
            "success": True,
            "status": status
        })
        
    except Exception as e:
        app_logger.error(f"获取庭审状态错误: {str(e)}")
        import traceback
        traceback.print_exc()
        return jsonify({
            "success": False,
            "error": str(e)
        }), 500


@router.route('/debate/<session_id>/details', methods=['GET'])
def get_debate_details(session_id: str):
    """
    获取庭审详情
    
    获取完整的庭审会话详情，包括案件信息、辩论历史等
    """
    try:
        engine = get_courtroom_engine()
        details = engine.get_session_details(session_id)
        
        return jsonify({
            "success": True,
            "details": details
        })
        
    except Exception as e:
        app_logger.error(f"获取庭审详情错误: {str(e)}")
        import traceback
        traceback.print_exc()
        return jsonify({
            "success": False,
            "error": str(e)
        }), 500


# ==================== 异步模拟法庭处理 ====================

import threading
import json
from flask import Response
from services.llm_factory import LLMFactory
from langchain_core.messages import HumanMessage, SystemMessage

# 存储正在处理的会话
processing_sessions = {}
# 存储SSE连接
streaming_sessions = {}

def process_debate_async(session_id: str, engine, case_type: str, user_role: str = 'auto'):
    """
    异步处理模拟法庭流程
    
    在后台线程中完成所有 LLM 调用
    """
    try:
        processing_sessions[session_id] = {
            "status": "processing",
            "progress": 0,
            "current_step": "正在分析案件...",
            "result": None
        }
        
        # 发送SSE事件
        def send_event(event_type, data):
            app_logger.info(f"发送SSE事件: {event_type}, 角色: {data.get('role') if 'role' in data else 'N/A'}")
            
            # 确保streaming_sessions中存在该会话的队列
            if session_id not in streaming_sessions:
                app_logger.info(f"会话 {session_id} 不在streaming_sessions中，创建队列")
                streaming_sessions[session_id] = []
            
            try:
                event_data = json.dumps({"type": event_type, "data": data})
                streaming_sessions[session_id].append(f"data: {event_data}\n\n")
                app_logger.info(f"事件已添加到队列，队列长度: {len(streaming_sessions[session_id])}")
            except Exception as e:
                app_logger.error(f"发送SSE事件错误: {str(e)}")
        
        # 渐进式更新进度条
        def update_progress(current, target, step_description):
            import time
            step = 1
            while current < target:
                current += step
                if current > target:
                    current = target
                send_event("progress", {"step": step_description, "progress": current})
                processing_sessions[session_id]["progress"] = current
                processing_sessions[session_id]["current_step"] = step_description
                time.sleep(0.1)  # 控制进度条更新速度
            return current
        
        # 法官开场
        current_progress = 0
        current_progress = update_progress(current_progress, 5, "法官开场...")
        judge_opening = "尊敬的各位，现在开庭。本案是一起民事纠纷案件，原告与被告之间存在合同争议。现在首先由原告方进行开庭陈述。"
        send_event("message", {"role": "judge", "content": judge_opening})
        app_logger.info("法官开场发言完成")
        
        # 生成原告开庭陈述
        current_progress = update_progress(current_progress, 15, "生成原告开庭陈述...")
        
        if user_role != 'plaintiff':
            # 系统生成原告陈述
            plaintiff_opening = engine.generate_opening_statement(session_id, Party.PLAINTIFF)
            app_logger.info(f"原告开庭陈述长度: {len(plaintiff_opening)} 字符")
            
            # 发送原告开庭陈述
            send_event("message", {"role": "plaintiff", "content": plaintiff_opening})
        else:
            # 轮到用户发言
            send_event("user_turn", {"role": "plaintiff"})
            # 等待用户输入（实际应用中会通过用户输入接口提交）
            # 这里我们设置一个较长的等待时间，让用户有足够时间输入
            import time
            time.sleep(30)  # 等待30秒，给用户足够时间输入
            # 如果用户没有输入，使用默认内容
            plaintiff_opening = "尊敬的法官，我是原告律师。我方认为被告的行为构成违约，应当承担相应的法律责任..."
            send_event("message", {"role": "plaintiff", "content": plaintiff_opening})
        
        app_logger.info(f"原告开庭陈述消息发送完成")
        
        # 添加过渡提示 - 原告陈述完毕
        send_event("message", {"role": "judge", "content": "📋 原告方陈述完毕，现在由被告方进行开庭陈述。"})
        
        # 生成被告开庭陈述
        current_progress = update_progress(current_progress, 30, "生成被告开庭陈述...")
        
        if user_role != 'defendant':
            # 系统生成被告陈述
            defendant_opening = engine.generate_opening_statement(session_id, Party.DEFENDANT)
            app_logger.info(f"被告开庭陈述长度: {len(defendant_opening)} 字符")
            
            # 发送被告开庭陈述
            send_event("message", {"role": "defendant", "content": defendant_opening})
        else:
            # 轮到用户发言
            send_event("user_turn", {"role": "defendant"})
            # 等待用户输入
            import time
            time.sleep(30)  # 等待30秒，给用户足够时间输入
            # 如果用户没有输入，使用默认内容
            defendant_opening = "尊敬的法官，我是被告律师。我方认为原告的主张没有事实和法律依据，请求驳回原告的诉讼请求..."
            send_event("message", {"role": "defendant", "content": defendant_opening})
        
        # 添加过渡提示 - 开庭陈述阶段结束
        send_event("message", {"role": "judge", "content": "⚖️ 开庭陈述阶段结束，现在进入法庭辩论阶段，由原告方先发言。"})
        
        # 生成原告辩论意见
        current_progress = update_progress(current_progress, 45, "生成原告辩论意见...")
        
        if user_role != 'plaintiff':
            # 系统生成原告辩论
            plaintiff_argument = engine.generate_argument(session_id, Party.PLAINTIFF)
            app_logger.info(f"原告辩论意见长度: {len(plaintiff_argument)} 字符")
            
            # 发送原告辩论意见
            send_event("message", {"role": "plaintiff", "content": plaintiff_argument})
        else:
            # 轮到用户发言
            send_event("user_turn", {"role": "plaintiff"})
            # 等待用户输入
            import time
            time.sleep(30)  # 等待30秒，给用户足够时间输入
            # 如果用户没有输入，使用默认内容
            plaintiff_argument = "尊敬的法官，针对本案，我方有以下辩论意见：首先，被告的行为违反了合同约定..."
            send_event("message", {"role": "plaintiff", "content": plaintiff_argument})
        
        # 添加过渡提示 - 原告辩论完毕
        send_event("message", {"role": "judge", "content": "📋 原告方辩论完毕，现在由被告方进行辩论。"})
        
        # 生成被告辩论意见
        current_progress = update_progress(current_progress, 60, "生成被告辩论意见...")
        
        if user_role != 'defendant':
            # 系统生成被告辩论
            defendant_argument = engine.generate_argument(session_id, Party.DEFENDANT)
            app_logger.info(f"被告辩论意见长度: {len(defendant_argument)} 字符")
            
            # 发送被告辩论意见
            send_event("message", {"role": "defendant", "content": defendant_argument})
        else:
            # 轮到用户发言
            send_event("user_turn", {"role": "defendant"})
            # 等待用户输入
            import time
            time.sleep(30)  # 等待30秒，给用户足够时间输入
            # 如果用户没有输入，使用默认内容
            defendant_argument = "尊敬的法官，我方针对原告的辩论意见，有以下反驳：首先，原告的主张没有证据支持..."
            send_event("message", {"role": "defendant", "content": defendant_argument})
        
        # 添加过渡提示 - 法庭辩论阶段结束
        send_event("message", {"role": "judge", "content": "⚖️ 法庭辩论阶段结束，现在进入最后陈述阶段，由原告方先发言。"})
        
        # 生成原告最后陈述
        current_progress = update_progress(current_progress, 75, "生成原告最后陈述...")
        
        if user_role != 'plaintiff':
            # 系统生成原告最后陈述
            plaintiff_closing = engine.generate_closing_statement(session_id, Party.PLAINTIFF)
            app_logger.info(f"原告最后陈述长度: {len(plaintiff_closing)} 字符")
            
            # 发送原告最后陈述
            send_event("message", {"role": "plaintiff", "content": plaintiff_closing})
        else:
            # 轮到用户发言
            send_event("user_turn", {"role": "plaintiff"})
            # 等待用户输入
            import time
            time.sleep(30)  # 等待30秒，给用户足够时间输入
            # 如果用户没有输入，使用默认内容
            plaintiff_closing = "尊敬的法官，综上所述，我方认为被告的行为构成违约，应当承担相应的法律责任。请求法院支持我方的诉讼请求。"
            send_event("message", {"role": "plaintiff", "content": plaintiff_closing})
        
        # 添加过渡提示 - 原告最后陈述完毕
        send_event("message", {"role": "judge", "content": "📋 原告方最后陈述完毕，现在由被告方进行最后陈述。"})
        
        # 生成被告最后陈述
        current_progress = update_progress(current_progress, 90, "生成被告最后陈述...")
        
        if user_role != 'defendant':
            # 系统生成被告最后陈述
            defendant_closing = engine.generate_closing_statement(session_id, Party.DEFENDANT)
            app_logger.info(f"被告最后陈述长度: {len(defendant_closing)} 字符")
            
            # 发送被告最后陈述
            send_event("message", {"role": "defendant", "content": defendant_closing})
        else:
            # 轮到用户发言
            send_event("user_turn", {"role": "defendant"})
            # 等待用户输入
            import time
            time.sleep(30)  # 等待30秒，给用户足够时间输入
            # 如果用户没有输入，使用默认内容
            defendant_closing = "尊敬的法官，综上所述，我方认为原告的主张没有事实和法律依据，请求法院驳回原告的诉讼请求。"
            send_event("message", {"role": "defendant", "content": defendant_closing})
        
        # 添加过渡提示 - 最后陈述阶段结束
        send_event("message", {"role": "judge", "content": "⚖️ 最后陈述阶段结束，现在由本庭进行评议并作出判决。"})
        
        # 生成判决
        current_progress = update_progress(current_progress, 95, "生成判决书...")
        verdict_data = engine.generate_verdict(session_id)
        verdict_result = verdict_data.get("verdict", "")
        verdict_reasoning = verdict_data.get("reasoning", "")
        
        session = engine.sessions[session_id]
        
        # 发送法官意见
        judge_opinion = session.debate_history[-1].content if session.debate_history else ""
        send_event("message", {"role": "judge", "content": judge_opinion})
        
        # 保存结果
        processing_sessions[session_id] = {
            "status": "completed",
            "progress": 100,
            "current_step": "完成",
            "result": {
                "session_id": session_id,
                "case_title": session.case.title,
                "case_type": session.case.case_type,
                "plaintiff_arguments": plaintiff_argument,
                "defendant_arguments": defendant_argument,
                "judge_opinion": judge_opinion,
                "verdict_result": verdict_result,
                "verdict_reasoning": verdict_reasoning,
                "legal_issues": [
                    {
                        "description": issue.description,
                        "relevant_law": issue.relevant_law,
                        "conclusion": issue.conclusion
                    }
                    for issue in session.case.legal_issues
                ],
                "debate_summary": {
                    "plaintiff_opening": plaintiff_opening[:200] + "...",
                    "defendant_opening": defendant_opening[:200] + "...",
                    "plaintiff_closing": plaintiff_closing[:200] + "...",
                    "defendant_closing": defendant_closing[:200] + "..."
                }
            }
        }
        
        # 发送完成事件，包含完整的会话数据
        complete_data = {
            "result": processing_sessions[session_id]["result"],
            "case_info": {
                "title": session.case.title,
                "case_type": session.case.case_type,
                "case_description": session.case.case_description,
                "plaintiff_claims": session.case.plaintiff_claims,
                "defendant_defenses": session.case.defendant_defenses
            },
            "legal_issues": [
                {
                    "description": issue.description,
                    "relevant_law": issue.relevant_law,
                    "plaintiff_position": issue.plaintiff_position,
                    "defendant_position": issue.defendant_position,
                    "conclusion": issue.conclusion
                }
                for issue in session.case.legal_issues
            ],
            "debate_history": [
                {
                    "id": turn.id,
                    "phase": turn.phase.value,
                    "party": turn.party.value,
                    "speaker_role": turn.speaker_role,
                    "content": turn.content,
                    "timestamp": turn.timestamp
                }
                for turn in session.debate_history
            ],
            "evidence_list": [
                {
                    "id": evidence.id,
                    "party": evidence.party.value,
                    "name": evidence.name,
                    "evidence_type": evidence.evidence_type,
                    "probative_force": evidence.probative_force,
                    "is_authenticated": evidence.is_authenticated
                }
                for evidence in session.case.evidence_list
            ]
        }
        send_event("complete", complete_data)
        
        app_logger.info(f"异步模拟法庭处理完成，会话ID: {session_id}")
        
    except Exception as e:
        app_logger.error(f"异步模拟法庭处理错误: {str(e)}")
        processing_sessions[session_id] = {
            "status": "error",
            "progress": 0,
            "current_step": f"错误: {str(e)}",
            "result": None
        }
        # 发送错误事件
        if session_id in streaming_sessions:
            try:
                event_data = json.dumps({"type": "error", "data": {"error": str(e)}})
                streaming_sessions[session_id].append(f"data: {event_data}\n\n")
            except Exception as send_error:
                app_logger.error(f"发送错误事件错误: {str(send_error)}")


# ==================== 简化版模拟法庭接口（兼容旧版）====================

@router.route('/analysis/debate/start', methods=['POST'])
def start_debate_legacy():
    """
    启动模拟法庭辩论（兼容旧版路径）
    
    快速返回会话ID，在后台异步处理
    """
    try:
        data = request.json
        if not data or 'case_description' not in data:
            return jsonify({
                "success": False,
                "error": "缺少必要参数 case_description"
            }), 400
        
        case_description = data.get('case_description')
        case_type = data.get('case_type', '民事纠纷')
        user_role = data.get('user_role', 'auto')
        
        app_logger.info(f"启动模拟法庭（异步版），案件描述长度: {len(case_description)} 字符, 用户角色: {user_role}")
        
        # 获取模拟法庭引擎
        engine = get_courtroom_engine()
        
        # 创建庭审会话
        session = engine.create_session(case_description, case_type)
        
        # 立即启动后台线程处理，不等待返回
        def start_processing():
            try:
                # 初始化处理状态
                processing_sessions[session.id] = {
                    "status": "processing",
                    "progress": 0,
                    "current_step": "正在分析案件...",
                    "result": None
                }
                
                # 等待SSE连接建立（最多等待5秒）
                import time
                for i in range(50):  # 50 * 0.1s = 5s
                    if session.id in streaming_sessions:
                        app_logger.info(f"SSE连接已建立，开始处理会话: {session.id}")
                        break
                    time.sleep(0.1)
                else:
                    app_logger.warning(f"SSE连接未建立，继续处理会话: {session.id}")
                
                # 调用处理函数
                process_debate_async(session.id, engine, case_type, user_role)
            except Exception as e:
                app_logger.error(f"启动处理线程错误: {str(e)}")
        
        # 启动后台线程
        thread = threading.Thread(target=start_processing)
        thread.daemon = True
        thread.start()
        
        app_logger.info(f"模拟法庭异步处理启动，会话ID: {session.id}")
        
        # 立即返回会话ID
        return jsonify({
            "success": True,
            "session_id": session.id,
            "case_title": session.case.title,
            "case_type": session.case.case_type,
            "status": "processing",
            "message": "模拟法庭已启动，请使用 /api/debate/progress 查询进度"
        })
        
    except Exception as e:
        app_logger.error(f"启动模拟法庭（异步版）错误: {str(e)}")
        import traceback
        traceback.print_exc()
        return jsonify({
            "success": False,
            "error": str(e)
        }), 500


@router.route('/debate/progress', methods=['GET'])
def get_debate_progress():
    """
    获取模拟法庭处理进度
    
    查询异步处理的进度和结果
    """
    try:
        session_id = request.args.get('session_id')
        if not session_id:
            return jsonify({
                "success": False,
                "error": "缺少必要参数 session_id"
            }), 400
        
        if session_id not in processing_sessions:
            # 检查是否已完成并存储在引擎中
            engine = get_courtroom_engine()
            if session_id in engine.sessions:
                session = engine.sessions[session_id]
                if not session.is_active and session.verdict:
                    return jsonify({
                        "success": True,
                        "session_id": session_id,
                        "status": "completed",
                        "progress": 100,
                        "current_step": "完成",
                        "result": {
                            "session_id": session_id,
                            "case_title": session.case.title,
                            "case_type": session.case.case_type,
                            "judge_opinion": session.debate_history[-1].content if session.debate_history else "",
                            "verdict_result": session.verdict,
                            "verdict_reasoning": session.reasoning
                        }
                    })
            
            return jsonify({
                "success": False,
                "error": "会话不存在"
            }), 404
        
        progress_info = processing_sessions[session_id]
        
        return jsonify({
            "success": True,
            "session_id": session_id,
            "status": progress_info["status"],
            "progress": progress_info["progress"],
            "current_step": progress_info["current_step"],
            "result": progress_info["result"]
        })
        
    except Exception as e:
        app_logger.error(f"获取进度错误: {str(e)}")
        import traceback
        traceback.print_exc()
        return jsonify({
            "success": False,
            "error": str(e)
        }), 500


@router.route('/debate/stream/<session_id>', methods=['GET'])
def debate_stream(session_id: str):
    """
    模拟法庭流式输出
    
    使用SSE技术实时推送思考过程和结果
    """
    def generate():
        try:
            # 确保队列存在（不重置现有队列）
            if session_id not in streaming_sessions:
                streaming_sessions[session_id] = []
            else:
                app_logger.info(f"使用现有队列，队列长度: {len(streaming_sessions[session_id])}")
            
            # 发送初始连接事件
            yield f"data: {json.dumps({'type': 'connected', 'data': {'session_id': session_id}})}\n\n"
            
            # 持续发送事件
            while session_id in streaming_sessions:
                # 发送队列中的事件
                if streaming_sessions[session_id]:
                    events = streaming_sessions[session_id].copy()
                    streaming_sessions[session_id].clear()
                    for event in events:
                        yield event
                
                # 检查会话状态，但只有当队列为空时才结束流
                if session_id in processing_sessions:
                    status = processing_sessions[session_id].get('status')
                    if status in ['completed', 'error'] and not streaming_sessions[session_id]:
                        # 会话已完成或出错，且队列为空，结束流
                        break
                
                # 防止CPU占用过高
                import time
                time.sleep(0.1)
            
            # 清理SSE连接
            if session_id in streaming_sessions:
                del streaming_sessions[session_id]
                
        except Exception as e:
            app_logger.error(f"SSE流错误: {str(e)}")
            # 发送错误事件
            yield f"data: {json.dumps({'type': 'error', 'data': {'error': str(e)}})}\n\n"
            # 清理SSE连接
            if session_id in streaming_sessions:
                del streaming_sessions[session_id]
    
    # 设置SSE响应头
    response = Response(generate(), mimetype='text/event-stream')
    response.headers['Cache-Control'] = 'no-cache'
    response.headers['Connection'] = 'keep-alive'
    response.headers['X-Accel-Buffering'] = 'no'
    return response


# ==================== 合同对比分析接口 ====================

@router.route('/analysis/compare', methods=['POST'])
def compare_contracts():
    """
    对比分析多个合同
    
    使用 LLM 深度对比分析多个合同的条款差异
    """
    try:
        from services.llm_factory import LLMFactory
        from langchain_core.messages import HumanMessage, SystemMessage
        
        data = request.json
        if not data or 'contracts' not in data:
            return jsonify({
                "success": False,
                "error": "缺少必要参数 contracts"
            }), 400
        
        contracts = data.get('contracts', [])
        if len(contracts) < 2:
            return jsonify({
                "success": False,
                "error": "至少需要提供2个合同进行对比"
            }), 400
        
        app_logger.info(f"开始合同对比分析，合同数量: {len(contracts)}")
        
        # 调用 LLM 进行对比分析
        llm = LLMFactory.create_llm()
        
        # 构建对比提示
        contracts_text = ""
        for i, contract in enumerate(contracts, 1):
            contracts_text += f"\n{'='*50}\n合同 {i}: {contract.get('name', f'合同{i}')}\n{'='*50}\n"
            content = contract.get('content', '')
            contracts_text += content[:2000] + ("..." if len(content) > 2000 else "")
            contracts_text += "\n"
        
        compare_prompt = f"""你是一名资深的合同法律专家，请对以下合同进行深度对比分析：

{contracts_text}

请从以下维度进行专业对比分析：

1. **合同性质与适用范围**
   - 合同类型差异
   - 适用场景对比
   - 当事人权利义务差异

2. **主要条款对比**
   - 标的条款
   - 价款/报酬条款
   - 履行期限和方式
   - 违约责任条款
   - 争议解决条款

3. **风险条款识别**
   - 各合同的风险点
   - 风险程度对比
   - 对当事人的影响

4. **法律合规性分析**
   - 符合法律规定的程度
   - 潜在的法律风险
   - 条款效力分析

5. **优劣势评估**
   - 各合同的优势
   - 各合同的劣势
   - 适用建议

6. **专业建议**
   - 推荐使用场景
   - 修改建议
   - 注意事项

要求：
- 分析全面、深入
- 引用相关法律条文
- 给出明确的结论和建议
- 不少于1500字"""
        
        messages = [
            SystemMessage(content="你是一名资深的合同法律专家，擅长对比分析不同合同的条款差异和法律风险。"),
            HumanMessage(content=compare_prompt)
        ]
        
        app_logger.info("正在生成合同对比分析...")
        response = llm.invoke(messages)
        analysis_result = response.content if hasattr(response, 'content') else str(response)
        
        app_logger.info("合同对比分析完成")
        
        return jsonify({
            "success": True,
            "contracts_count": len(contracts),
            "analysis_result": analysis_result
        })
        
    except Exception as e:
        app_logger.error(f"合同对比接口错误: {str(e)}")
        import traceback
        traceback.print_exc()
        return jsonify({
            "success": False,
            "error": str(e)
        }), 500


# ==================== 合同模板生成接口 ====================

@router.route('/analysis/template', methods=['POST'])
def generate_template():
    """
    根据需求生成合同模板
    
    使用 LLM 生成专业、完整的合同模板
    """
    try:
        from services.llm_factory import LLMFactory
        from langchain_core.messages import HumanMessage, SystemMessage
        
        data = request.json
        if not data or 'requirements' not in data:
            return jsonify({
                "success": False,
                "error": "缺少必要参数 requirements"
            }), 400
        
        requirements = data.get('requirements')
        contract_type = data.get('contract_type', '通用合同')
        
        app_logger.info(f"开始生成合同模板，类型: {contract_type}")
        
        # 调用 LLM 生成合同模板
        llm = LLMFactory.create_llm()
        
        template_prompt = f"""你是一名专业的合同起草专家，请根据以下需求生成一份完整、专业的合同模板：

合同类型：{contract_type}

需求描述：
{requirements}

请生成一份符合中国法律规定的完整合同模板，包括：

1. **合同标题**
   - 明确的合同名称
   - 合同编号（预留）

2. **当事人信息**
   - 甲方（详细身份信息）
   - 乙方（详细身份信息）
   - 法定代表人/负责人
   - 联系方式

3. **鉴于条款**
   - 合同签订的背景
   - 双方的合作基础

4. **正文条款**
   - 第一条 合同标的
   - 第二条 权利义务
   - 第三条 价款/报酬及支付方式
   - 第四条 履行期限和方式
   - 第五条 质量标准/服务要求
   - 第六条 验收标准
   - 第七条 知识产权（如适用）
   - 第八条 保密条款
   - 第九条 违约责任
   - 第十条 不可抗力
   - 第十一条 争议解决
   - 第十二条 其他约定

5. **合同效力条款**
   - 生效条件
   - 变更和解除
   - 终止条件

6. **签字盖章部分**
   - 甲方签章
   - 乙方签章
   - 签订日期
   - 签订地点

要求：
- 条款完整、严谨
- 符合《民法典》等相关法律规定
- 语言规范、准确
- 预留必要的填写项
- 包含风险提示条款"""
        
        messages = [
            SystemMessage(content="你是一名专业的合同起草专家，精通中国合同法，擅长生成规范、完整的合同模板。"),
            HumanMessage(content=template_prompt)
        ]
        
        app_logger.info("正在生成合同模板...")
        response = llm.invoke(messages)
        template_content = response.content if hasattr(response, 'content') else str(response)
        
        app_logger.info("合同模板生成完成")
        
        return jsonify({
            "success": True,
            "contract_type": contract_type,
            "template_content": template_content
        })
        
    except Exception as e:
        app_logger.error(f"模板生成接口错误: {str(e)}")
        import traceback
        traceback.print_exc()
        return jsonify({
            "success": False,
            "error": str(e)
        }), 500


@router.route('/debate/history', methods=['GET'])
def get_debate_history():
    """
    获取模拟法庭历史记录
    
    返回所有庭审会话列表，包括案件信息和辩论摘要
    """
    try:
        from core.database import get_db
        from models.db_models import Case, CourtSession, DebateTurn
        
        db = next(get_db())
        try:
            sessions = db.query(CourtSession).order_by(CourtSession.created_at.desc()).all()
            
            history = []
            for session in sessions:
                case = db.query(Case).filter(Case.id == session.case_id).first()
                debate_turns = db.query(DebateTurn).filter(DebateTurn.session_id == session.id).all()
                
                if case:
                    history.append({
                        "id": session.id,
                        "case_id": case.id,
                        "case_title": case.title,
                        "case_type": case.case_type,
                        "case_description": case.case_description[:200] + "..." if len(case.case_description) > 200 else case.case_description,
                        "current_phase": session.current_phase,
                        "is_active": session.is_active,
                        "verdict": session.verdict,
                        "debate_turn_count": len(debate_turns),
                        "created_at": session.created_at.isoformat() if session.created_at else None,
                        "updated_at": session.updated_at.isoformat() if session.updated_at else None
                    })
            
            return jsonify({
                "success": True,
                "history": history
            })
        finally:
            db.close()
    except Exception as e:
        app_logger.error(f"获取模拟法庭历史记录错误: {str(e)}")
        import traceback
        traceback.print_exc()
        return jsonify({"error": str(e)}), 500


@router.route('/debate/<session_id>/full-details', methods=['GET'])
def get_debate_full_details(session_id: str):
    """
    获取特定庭审会话的完整详情
    
    Args:
        session_id: 庭审会话ID
        
    Returns:
        庭审会话的完整详情，包括案件信息、所有辩论回合等
    """
    try:
        from core.database import get_db
        from models.db_models import Case, CourtSession, DebateTurn, Evidence, LegalIssue
        
        db = next(get_db())
        try:
            session = db.query(CourtSession).filter(CourtSession.id == session_id).first()
            if not session:
                return jsonify({"error": "庭审会话不存在"}), 404
            
            case = db.query(Case).filter(Case.id == session.case_id).first()
            debate_turns = db.query(DebateTurn).filter(DebateTurn.session_id == session_id).order_by(DebateTurn.timestamp.asc()).all()
            evidence_list = db.query(Evidence).filter(Evidence.case_id == session.case_id).all()
            legal_issues = db.query(LegalIssue).filter(LegalIssue.case_id == session.case_id).all()
            
            debate_details = []
            for turn in debate_turns:
                debate_details.append({
                    "id": turn.id,
                    "phase": turn.phase,
                    "party": turn.party,
                    "speaker_role": turn.speaker_role,
                    "content": turn.content,
                    "legal_basis": turn.legal_basis,
                    "facts_stated": turn.facts_stated,
                    "arguments_made": turn.arguments_made,
                    "counter_arguments": turn.counter_arguments,
                    "timestamp": turn.timestamp.isoformat() if turn.timestamp else None
                })
            
            evidence_details = []
            for evidence in evidence_list:
                evidence_details.append({
                    "id": evidence.id,
                    "party": evidence.party,
                    "name": evidence.name,
                    "content": evidence.content,
                    "evidence_type": evidence.evidence_type,
                    "probative_force": evidence.probative_force,
                    "is_authenticated": evidence.is_authenticated,
                    "authentication_opinion": evidence.authentication_opinion,
                    "created_at": evidence.created_at.isoformat() if evidence.created_at else None
                })
            
            issue_details = []
            for issue in legal_issues:
                issue_details.append({
                    "id": issue.id,
                    "description": issue.description,
                    "relevant_law": issue.relevant_law,
                    "plaintiff_position": issue.plaintiff_position,
                    "defendant_position": issue.defendant_position,
                    "judge_analysis": issue.judge_analysis,
                    "conclusion": issue.conclusion,
                    "is_resolved": issue.is_resolved,
                    "created_at": issue.created_at.isoformat() if issue.created_at else None
                })
            
            return jsonify({
                "success": True,
                "session": {
                    "id": session.id,
                    "current_phase": session.current_phase,
                    "is_active": session.is_active,
                    "verdict": session.verdict,
                    "reasoning": session.reasoning,
                    "created_at": session.created_at.isoformat() if session.created_at else None,
                    "updated_at": session.updated_at.isoformat() if session.updated_at else None
                },
                "case": {
                    "id": case.id if case else None,
                    "title": case.title if case else None,
                    "case_type": case.case_type if case else None,
                    "case_description": case.case_description if case else None,
                    "plaintiff_claims": case.plaintiff_claims if case else None,
                    "defendant_defenses": case.defendant_defenses if case else None
                } if case else None,
                "debate_turns": debate_details,
                "evidence": evidence_details,
                "legal_issues": issue_details
            })
        finally:
            db.close()
    except Exception as e:
        app_logger.error(f"获取庭审详情错误: {str(e)}")
        import traceback
        traceback.print_exc()
        return jsonify({"error": str(e)}), 500


@router.route('/debate/<session_id>', methods=['DELETE'])
def delete_debate_session(session_id: str):
    """
    删除模拟法庭会话
    
    Args:
        session_id: 庭审会话ID
        
    Returns:
        删除结果
    """
    try:
        from core.database import get_db
        from models.db_models import Case, CourtSession, DebateTurn, Evidence, LegalIssue
        
        db = next(get_db())
        try:
            session = db.query(CourtSession).filter(CourtSession.id == session_id).first()
            if not session:
                return jsonify({"error": "庭审会话不存在"}), 404
            
            case_id = session.case_id
            
            # 删除辩论回合
            db.query(DebateTurn).filter(DebateTurn.session_id == session_id).delete()
            # 删除庭审会话
            db.delete(session)
            
            # 检查是否还有其他会话使用这个案件
            other_sessions = db.query(CourtSession).filter(CourtSession.case_id == case_id).count()
            if other_sessions == 0:
                # 删除关联的证据
                db.query(Evidence).filter(Evidence.case_id == case_id).delete()
                # 删除关联的法律问题
                db.query(LegalIssue).filter(LegalIssue.case_id == case_id).delete()
                # 删除案件
                case = db.query(Case).filter(Case.id == case_id).first()
                if case:
                    db.delete(case)
            
            db.commit()
            
            return jsonify({
                "success": True,
                "message": "庭审会话删除成功"
            })
        finally:
            db.close()
    except Exception as e:
        app_logger.error(f"删除庭审会话错误: {str(e)}")
        import traceback
        traceback.print_exc()
        return jsonify({"error": str(e)}), 500


@router.route('/debate/<session_id>', methods=['PUT'])
def update_debate_session(session_id: str):
    """
    更新模拟法庭会话标题（案件标题）
    
    Args:
        session_id: 庭审会话ID
        
    Request Body:
        - title: 新的案件标题
        
    Returns:
        更新结果
    """
    try:
        from flask_app.core.database import get_db
        from flask_app.models.db_models import CourtSession, Case
        
        data = request.json
        if not data or 'title' not in data:
            return jsonify({"error": "缺少必要参数 title"}), 400
        
        new_title = data.get('title')
        
        db = next(get_db())
        try:
            session = db.query(CourtSession).filter(CourtSession.id == session_id).first()
            if not session:
                return jsonify({"error": "庭审会话不存在"}), 404
            
            case = db.query(Case).filter(Case.id == session.case_id).first()
            if case:
                case.title = new_title
                db.commit()
                
                return jsonify({
                    "success": True,
                    "message": "案件标题更新成功",
                    "title": new_title
                })
            else:
                return jsonify({"error": "案件不存在"}), 404
        finally:
            db.close()
    except Exception as e:
        app_logger.error(f"更新庭审会话错误: {str(e)}")
        import traceback
        traceback.print_exc()
        return jsonify({"error": str(e)}), 500


# ==================== 案情推断接口 ====================

@router.route('/analysis/case-analysis', methods=['POST'])
def analyze_case():
    """
    案情推断接口 - 使用流式传输调用DeepSeek API
    """
    try:
        from core.database import get_db
        from models.db_models import CaseAnalysis
        from core.config import settings
        import uuid
        import httpx
        import json

        data = request.json
        if not data or 'case_description' not in data:
            return jsonify({
                "success": False,
                "error": "缺少必要参数 case_description"
            }), 400

        case_description = data.get('case_description')
        app_logger.info(f"开始案情推断，描述长度: {len(case_description)} 字符")

        # 构建提示词
        analysis_prompt = f"""你是一名资深的法律专家，请根据以下案情描述进行分析：

{case_description}

请从以下方面进行专业分析：

1. **案件类型**：判断这是什么类型的案件（如刑事、民事、行政等）
2. **可能的罪名**：如果是刑事案件，推断可能涉及的罪名
3. **罪名解释**：详细解释该罪名的法律定义
4. **罪名特征**：列出该罪名的主要特征和构成要件
5. **相关法律条文**：引用相关的法律条文
6. **法律建议**：基于案情提供专业的法律建议

要求：
- 分析全面、准确
- 引用具体的法律条文
- 给出明确的结论
- 语言专业、严谨"""

        # 使用流式传输调用DeepSeek API
        url = f"{settings.OPENAI_BASE_URL}/chat/completions"
        
        payload = {
            "model": settings.OPENAI_MODEL,
            "messages": [
                {"role": "system", "content": "你是一名资深的法律专家，精通中国法律，擅长分析各类案件并提供专业的法律意见。"},
                {"role": "user", "content": analysis_prompt}
            ],
            "max_tokens": 2048,
            "temperature": settings.OPENAI_TEMPERATURE,
            "stream": True  # 启用流式传输
        }
        
        app_logger.info(f"调用DeepSeek API (流式传输): {url}")
        app_logger.info(f"API Key: {settings.OPENAI_API_KEY[:10]}...{settings.OPENAI_API_KEY[-4:]}")
        app_logger.info(f"请求参数: model={settings.OPENAI_MODEL}, max_tokens=2048, stream=True")
        
        # 使用流式传输
        client = httpx.Client(timeout=180.0)
        analysis_content = ""
        
        try:
            with client.stream(
                "POST",
                url,
                json=payload,
                headers={
                    "Content-Type": "application/json",
                    "Authorization": f"Bearer {settings.OPENAI_API_KEY}"
                }
            ) as response:
                app_logger.info(f"API响应状态码: {response.status_code}")
                
                if response.status_code != 200:
                    error_text = ""
                    try:
                        for line in response.iter_lines():
                            if line:
                                error_text += line
                    except:
                        pass
                    error_msg = f"API调用失败，状态码: {response.status_code}"
                    if error_text:
                        error_msg += f", 响应: {error_text[:200]}"
                    app_logger.error(error_msg)
                    return jsonify({
                        "success": False,
                        "error": error_msg
                    }), 500
                
                # 接收流式数据
                for line in response.iter_lines():
                    if line:
                        line = line.strip()
                        if line.startswith("data: "):
                            data_str = line[6:]  # 移除 "data: " 前缀
                            if data_str == "[DONE]":
                                break
                            try:
                                chunk = json.loads(data_str)
                                if 'choices' in chunk and len(chunk['choices']) > 0:
                                    delta = chunk['choices'][0].get('delta', {})
                                    content = delta.get('content', '')
                                    if content:
                                        analysis_content += content
                            except json.JSONDecodeError:
                                continue
                
                app_logger.info(f"成功获取AI回复，内容长度: {len(analysis_content)} 字符")
                
        finally:
            client.close()
        
        if not analysis_content:
            app_logger.error("API响应为空")
            return jsonify({
                "success": False,
                "error": "API响应为空"
            }), 500
        
        # 保存到数据库
        db = next(get_db())
        try:
            analysis_record = CaseAnalysis(
                id=str(uuid.uuid4()),
                case_description=case_description,
                analysis_result=analysis_content
            )
            db.add(analysis_record)
            db.commit()
            db.refresh(analysis_record)
            app_logger.info(f"案情推断记录已保存到数据库，ID: {analysis_record.id}")
        finally:
            db.close()
        
        app_logger.info("案情分析完成")
        
        return jsonify({
            "success": True,
            "analysis_result": analysis_content
        })
        
    except Exception as e:
        app_logger.error(f"案情推断错误: {str(e)}")
        import traceback
        traceback.print_exc()
        return jsonify({
            "success": False,
            "error": str(e)
        }), 500


# ==================== 相似文书搜索接口 ====================

@router.route('/analysis/similar-documents', methods=['POST'])
def search_similar_documents():
    """
    相似文书搜索接口
    
    根据用户输入的文书内容，搜索相似的过往判决文书
    """
    try:
        from services.llm_factory import LLMFactory
        from langchain_core.messages import HumanMessage, SystemMessage
        from core.database import get_db
        from models.db_models import SimilarDocumentSearch
        import uuid
        
        data = request.json
        if not data or 'document_content' not in data:
            return jsonify({
                "success": False,
                "error": "缺少必要参数 document_content"
            }), 400
        
        document_content = data.get('document_content')
        
        app_logger.info(f"开始相似文书搜索，文书长度: {len(document_content)} 字符")
        
        # 调用 LLM 进行相似文书搜索
        llm = LLMFactory.create_llm()
        
        search_prompt = f"""你是一名资深的法律专家，请根据以下文书内容，搜索并返回3-5份相似的过往判决文书：

{document_content}

请返回相似的判决文书，包括：
1. **案件标题**：文书的标题
2. **判决日期**：判决的日期
3. **审理法院**：审理案件的法院
4. **相似度**：与输入文书的相似度（百分比）
5. **文书内容**：文书的主要内容（简要摘要）

要求：
- 搜索结果要与输入文书在案情、法律问题等方面相似
- 提供具体的案件信息
- 相似度要合理评估
- 返回的结果要真实可信"""
        
        messages = [
            SystemMessage(content="你是一名资深的法律专家，精通中国法律和司法实践，熟悉各类法律文书。"),
            HumanMessage(content=search_prompt)
        ]
        
        app_logger.info("正在搜索相似文书（流式传输）...")
        
        # 使用流式传输调用LLM
        import httpx
        from core.config import settings
        
        formatted_messages = []
        for msg in messages:
            app_logger.info(f"相似文书 - 处理消息: {type(msg)}")
            
            role = None
            content = None
            
            if hasattr(msg, '_type'):
                if msg._type == 'system':
                    role = "system"
                    content = msg.content
                elif msg._type == 'human':
                    role = "user"
                    content = msg.content
                elif msg._type == 'ai':
                    role = "assistant"
                    content = msg.content
            elif hasattr(msg, 'type'):
                if msg.type == 'system':
                    role = "system"
                    content = msg.content
                elif msg.type == 'human':
                    role = "user"
                    content = msg.content
                elif msg.type == 'ai':
                    role = "assistant"
                    content = msg.content
            elif hasattr(msg, 'role') and hasattr(msg, 'content'):
                role = msg.role
                content = msg.content
            elif isinstance(msg, dict):
                role = msg.get('role', 'user')
                content = msg.get('content', '')
            
            if role and content:
                formatted_messages.append({"role": role, "content": content})
                app_logger.info(f"相似文书 - 添加消息: role={role}, content长度={len(content)}")
            else:
                app_logger.warning(f"相似文书 - 无法处理消息: {msg}")
        
        app_logger.info(f"相似文书 - 消息数量: {len(formatted_messages)}")
        
        payload = {
            "model": settings.OPENAI_MODEL,
            "messages": formatted_messages,
            "temperature": float(settings.OPENAI_TEMPERATURE),
            "max_tokens": int(settings.OPENAI_MAX_TOKENS),
            "stream": True
        }
        
        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {settings.OPENAI_API_KEY}"
        }
        
        client = httpx.Client(timeout=180.0)
        search_result = ""
        
        try:
            with client.stream(
                "POST",
                f"{settings.OPENAI_BASE_URL}/chat/completions",
                json=payload,
                headers=headers
            ) as response:
                app_logger.info(f"相似文书 - 响应状态码: {response.status_code}")
                
                if response.status_code == 200:
                    for line in response.iter_lines():
                        if line:
                            line = line.strip()
                            if line.startswith("data: "):
                                data_str = line[6:]
                                if data_str == "[DONE]":
                                    break
                                try:
                                    chunk = json.loads(data_str)
                                    if 'choices' in chunk and len(chunk['choices']) > 0:
                                        delta = chunk['choices'][0].get('delta', {})
                                        chunk_content = delta.get('content', '')
                                        if chunk_content:
                                            search_result += chunk_content
                                except json.JSONDecodeError:
                                    continue
                else:
                    error_text = ""
                    try:
                        for line in response.iter_lines():
                            if line:
                                error_text += line
                        error_data = json.loads(error_text) if error_text else {}
                        error_msg = error_data.get('error', {}).get('message', error_text[:200])
                    except:
                        error_msg = error_text[:200] if error_text else f"状态码: {response.status_code}"
                    app_logger.error(f"相似文书 LLM调用失败: {response.status_code} - {error_msg}")
                    raise Exception(f"LLM调用失败: {error_msg}")
        finally:
            client.close()
        
        # 保存到数据库
        db = next(get_db())
        try:
            search_record = SimilarDocumentSearch(
                id=str(uuid.uuid4()),
                document_content=document_content,
                search_result=search_result
            )
            db.add(search_record)
            db.commit()
            db.refresh(search_record)
            app_logger.info(f"相似文书搜索记录已保存到数据库，ID: {search_record.id}")
        finally:
            db.close()
        
        app_logger.info("相似文书搜索完成")
        
        return jsonify({
            "success": True,
            "similar_documents": search_result,
            "search_id": search_record.id
        })
        
    except Exception as e:
        app_logger.error(f"相似文书搜索错误: {str(e)}")
        import traceback
        traceback.print_exc()
        return jsonify({
            "success": False,
            "error": str(e)
        }), 500


# ==================== 案情推断历史记录接口 ====================

@router.route('/analysis/case-analysis/history', methods=['GET'])
def get_case_analysis_history():
    """
    获取案情推断历史记录
    """
    try:
        from core.database import get_db
        from models.db_models import CaseAnalysis
        
        db = next(get_db())
        try:
            # 获取所有案情推断记录，按创建时间倒序
            analyses = db.query(CaseAnalysis).order_by(CaseAnalysis.created_at.desc()).all()
            
            # 构建返回数据
            history = []
            for analysis in analyses:
                history.append({
                    "id": analysis.id,
                    "case_description": analysis.case_description,
                    "analysis_result": analysis.analysis_result,
                    "created_at": analysis.created_at.isoformat(),
                    "updated_at": analysis.updated_at.isoformat()
                })
            
            return jsonify({
                "success": True,
                "history": history
            })
        finally:
            db.close()
            
    except Exception as e:
        app_logger.error(f"获取案情推断历史记录错误: {str(e)}")
        import traceback
        traceback.print_exc()
        return jsonify({
            "success": False,
            "error": str(e)
        }), 500


@router.route('/analysis/case-analysis/<analysis_id>', methods=['DELETE'])
def delete_case_analysis(analysis_id):
    """
    删除案情推断记录
    """
    try:
        from core.database import get_db
        from models.db_models import CaseAnalysis
        
        db = next(get_db())
        try:
            # 查找记录
            analysis = db.query(CaseAnalysis).filter(CaseAnalysis.id == analysis_id).first()
            if not analysis:
                return jsonify({
                    "success": False,
                    "error": "记录不存在"
                }), 404
            
            # 删除记录
            db.delete(analysis)
            db.commit()
            
            app_logger.info(f"案情推断记录已删除，ID: {analysis_id}")
            
            return jsonify({
                "success": True,
                "message": "删除成功"
            })
        finally:
            db.close()
            
    except Exception as e:
        app_logger.error(f"删除案情推断记录错误: {str(e)}")
        import traceback
        traceback.print_exc()
        return jsonify({
            "success": False,
            "error": str(e)
        }), 500


# ==================== 相似文书搜索历史记录接口 ====================

@router.route('/analysis/similar-documents/history', methods=['GET'])
def get_similar_document_history():
    """
    获取相似文书搜索历史记录
    """
    try:
        from core.database import get_db
        from models.db_models import SimilarDocumentSearch
        
        db = next(get_db())
        try:
            # 获取所有相似文书搜索记录，按创建时间倒序
            searches = db.query(SimilarDocumentSearch).order_by(SimilarDocumentSearch.created_at.desc()).all()
            
            # 构建返回数据
            history = []
            for search in searches:
                history.append({
                    "id": search.id,
                    "document_content": search.document_content,
                    "search_result": search.search_result,
                    "created_at": search.created_at.isoformat(),
                    "updated_at": search.updated_at.isoformat()
                })
            
            return jsonify({
                "success": True,
                "history": history
            })
        finally:
            db.close()
            
    except Exception as e:
        app_logger.error(f"获取相似文书搜索历史记录错误: {str(e)}")
        import traceback
        traceback.print_exc()
        return jsonify({
            "success": False,
            "error": str(e)
        }), 500


@router.route('/analysis/similar-documents/<search_id>', methods=['DELETE'])
def delete_similar_document(search_id):
    """
    删除相似文书搜索记录
    """
    try:
        from core.database import get_db
        from models.db_models import SimilarDocumentSearch
        
        db = next(get_db())
        try:
            # 查找记录
            search = db.query(SimilarDocumentSearch).filter(SimilarDocumentSearch.id == search_id).first()
            if not search:
                return jsonify({
                    "success": False,
                    "error": "记录不存在"
                }), 404
            
            # 删除记录
            db.delete(search)
            db.commit()
            
            app_logger.info(f"相似文书搜索记录已删除，ID: {search_id}")
            
            return jsonify({
                "success": True,
                "message": "删除成功"
            })
        finally:
            db.close()
            
    except Exception as e:
        app_logger.error(f"删除相似文书搜索记录错误: {str(e)}")
        import traceback
        traceback.print_exc()
        return jsonify({
            "success": False,
            "error": str(e)
        }), 500
