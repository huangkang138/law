"""
WebSocket 消息路由服务器 - 庭审模式
支持用户 <-> AI 法官/律师 实时语音交互
"""
import json
import logging
import asyncio
import uuid
from typing import Dict, Set, Optional, Any
from fastapi import WebSocket, WebSocketDisconnect, status
from datetime import datetime
from services.courtroom_engine import CourtroomEngine, Party, DebatePhase

logger = logging.getLogger(__name__)


class CourtroomConnectionManager:
    """庭审 WebSocket 连接管理器"""
    
    def __init__(self):
        self.active_connections: Dict[str, WebSocket] = {}
        self.courtroom_sessions: Dict[str, Dict[str, Any]] = {}
        self.user_inputs: Dict[str, Dict[str, Any]] = {}
    
    async def connect(self, websocket: WebSocket, session_id: str, user_role: str = 'auto'):
        """建立连接"""
        await websocket.accept()
        connection_id = f"{session_id}_{datetime.now().timestamp()}"
        self.active_connections[connection_id] = websocket
        
        # 初始化庭审会话
        if session_id not in self.courtroom_sessions:
            self.courtroom_sessions[session_id] = {
                'connection_id': connection_id,
                'user_role': user_role,
                'current_phase': DebatePhase.OPENING_STATEMENTS,
                'current_party': Party.PLAINTIFF,
                'debate_history': [],
                'waiting_for_user': False,
                'user_input_received': False,
                'user_input_content': None,
                'is_active': True
            }
        else:
            # 更新现有会话
            self.courtroom_sessions[session_id]['connection_id'] = connection_id
            self.courtroom_sessions[session_id]['user_role'] = user_role
        
        logger.info(f"庭审会话 {session_id} 已连接 (连接ID: {connection_id}, 用户角色: {user_role})")
        
        return connection_id
    
    def disconnect(self, connection_id: str, session_id: str):
        """断开连接"""
        if connection_id in self.active_connections:
            del self.active_connections[connection_id]
        
        if session_id in self.courtroom_sessions:
            self.courtroom_sessions[session_id]['is_active'] = False
        
        logger.info(f"庭审会话 {session_id} 已断开连接 (连接ID: {connection_id})")
    
    async def send_message(self, message: dict, connection_id: str):
        """发送消息到指定连接"""
        if connection_id in self.active_connections:
            try:
                await self.active_connections[connection_id].send_json(message)
                logger.info(f"消息已发送到 {connection_id}: {message.get('type')}")
            except Exception as e:
                logger.error(f"发送消息失败: {e}")
    
    async def send_to_session(self, message: dict, session_id: str):
        """发送消息到指定庭审会话"""
        if session_id in self.courtroom_sessions:
            connection_id = self.courtroom_sessions[session_id]['connection_id']
            await self.send_message(message, connection_id)
    
    def get_session(self, session_id: str) -> Optional[Dict[str, Any]]:
        """获取庭审会话"""
        return self.courtroom_sessions.get(session_id)
    
    def update_session(self, session_id: str, updates: Dict[str, Any]):
        """更新庭审会话"""
        if session_id in self.courtroom_sessions:
            self.courtroom_sessions[session_id].update(updates)


manager = CourtroomConnectionManager()


async def handle_courtroom_websocket(websocket: WebSocket, session_id: str, user_role: str = 'auto'):
    """处理庭审 WebSocket 消息"""
    connection_id = None
    try:
        connection_id = await manager.connect(websocket, session_id, user_role)
        
        # 初始化庭审引擎
        from services.courtroom_engine import get_courtroom_engine
        engine = get_courtroom_engine()
        
        # 开始庭审流程
        await start_courtroom_session(session_id, engine, user_role)
        
        # 持续处理客户端消息
        while True:
            data = await websocket.receive_json()
            
            message_type = data.get('type')
            logger.info(f"收到消息: {message_type} from session {session_id}")
            
            if message_type == 'user_input':
                await handle_user_input(data, session_id, engine)
            elif message_type == 'audio_input':
                await handle_audio_input(data, session_id, engine)
            elif message_type == 'skip_turn':
                await handle_skip_turn(data, session_id, engine)
            elif message_type == 'restart':
                await handle_restart(data, session_id, engine, user_role)
            elif message_type == 'end_session':
                await handle_end_session(data, session_id)
            else:
                logger.warning(f"未知消息类型: {message_type}")
    
    except WebSocketDisconnect:
        logger.info(f"WebSocket 连接断开: {session_id}")
    except Exception as e:
        logger.error(f"处理 WebSocket 消息时出错: {e}")
        import traceback
        traceback.print_exc()
    finally:
        if connection_id:
            manager.disconnect(connection_id, session_id)


async def start_courtroom_session(session_id: str, engine: CourtroomEngine, user_role: str):
    """开始庭审会话"""
    session = manager.get_session(session_id)
    if not session:
        logger.error(f"会话 {session_id} 不存在")
        return
    
    # 发送法官开场
    judge_opening = "尊敬的各位，现在开庭。本案是一起民事纠纷案件，原告与被告之间存在合同争议。现在首先由原告方进行开庭陈述。"
    await manager.send_to_session({
        'type': 'message',
        'role': 'judge',
        'content': judge_opening,
        'phase': 'opening'
    }, session_id)
    
    # 添加到历史记录
    session['debate_history'].append({
        'id': str(uuid.uuid4()),
        'phase': DebatePhase.OPENING_STATEMENTS,
        'party': Party.JUDGE,
        'speaker_role': '法官',
        'content': judge_opening,
        'timestamp': datetime.now().isoformat()
    })
    
    # 开始原告开庭陈述
    await handle_party_turn(session_id, engine, Party.PLAINTIFF, 'opening_statement', user_role)


async def handle_party_turn(session_id: str, engine: CourtroomEngine, party: Party, turn_type: str, user_role: str):
    """处理一方发言"""
    session = manager.get_session(session_id)
    if not session:
        return
    
    # 检查是否是用户角色
    is_user_turn = (
        (user_role == 'plaintiff' and party == Party.PLAINTIFF) or
        (user_role == 'defendant' and party == Party.DEFENDANT)
    )
    
    if is_user_turn:
        # 轮到用户发言
        session['waiting_for_user'] = True
        session['current_party'] = party
        session['current_turn_type'] = turn_type
        
        # 发送用户轮次事件
        role_name = '原告' if party == Party.PLAINTIFF else '被告'
        await manager.send_to_session({
            'type': 'user_turn',
            'role': role_name,
            'party': party.value,
            'turn_type': turn_type,
            'message': f'现在轮到{role_name}方发言，请输入您的陈述内容或使用语音输入。'
        }, session_id)
        
        logger.info(f"等待用户输入: {role_name}, 会话: {session_id}")
    else:
        # 系统生成发言
        await generate_ai_response(session_id, engine, party, turn_type)


async def generate_ai_response(session_id: str, engine: CourtroomEngine, party: Party, turn_type: str):
    """生成 AI 响应"""
    session = manager.get_session(session_id)
    if not session:
        return
    
    try:
        # 根据发言类型生成内容
        if turn_type == 'opening_statement':
            content = engine.generate_opening_statement(session_id, party)
        elif turn_type == 'argument':
            content = engine.generate_argument(session_id, party)
        elif turn_type == 'closing_statement':
            content = engine.generate_closing_statement(session_id, party)
        elif turn_type == 'verdict':
            verdict_data = engine.generate_verdict(session_id)
            content = verdict_data.get('verdict', '')
        else:
            content = "抱歉，我无法生成该类型的发言。"
        
        # 发送 AI 响应
        role_name = '原告' if party == Party.PLAINTIFF else '被告' if party == Party.DEFENDANT else '法官'
        await manager.send_to_session({
            'type': 'message',
            'role': role_name,
            'party': party.value,
            'content': content,
            'phase': turn_type
        }, session_id)
        
        # 添加到历史记录
        session['debate_history'].append({
            'id': str(uuid.uuid4()),
            'phase': session['current_phase'],
            'party': party,
            'speaker_role': role_name,
            'content': content,
            'timestamp': datetime.now().isoformat()
        })
        
        # 继续下一步
        await proceed_to_next_turn(session_id, engine, party, turn_type)
        
    except Exception as e:
        logger.error(f"生成 AI 响应失败: {e}")
        await manager.send_to_session({
            'type': 'error',
            'message': f"生成响应失败: {str(e)}"
        }, session_id)


async def proceed_to_next_turn(session_id: str, engine: CourtroomEngine, current_party: Party, current_turn_type: str):
    """进行到下一个轮次"""
    session = manager.get_session(session_id)
    if not session:
        return
    
    user_role = session['user_role']
    
    # 根据当前状态决定下一步
    if current_turn_type == 'opening_statement':
        if current_party == Party.PLAINTIFF:
            # 原告陈述完毕，被告陈述
            await manager.send_to_session({
                'type': 'message',
                'role': 'judge',
                'content': '📋 原告方陈述完毕，现在由被告方进行开庭陈述。'
            }, session_id)
            await handle_party_turn(session_id, engine, Party.DEFENDANT, 'opening_statement', user_role)
        else:
            # 被告陈述完毕，进入辩论阶段
            session['current_phase'] = DebatePhase.DEBATE
            await manager.send_to_session({
                'type': 'message',
                'role': 'judge',
                'content': '⚖️ 开庭陈述阶段结束，现在进入法庭辩论阶段，由原告方先发言。'
            }, session_id)
            await handle_party_turn(session_id, engine, Party.PLAINTIFF, 'argument', user_role)
    
    elif current_turn_type == 'argument':
        if current_party == Party.PLAINTIFF:
            # 原告辩论完毕，被告辩论
            await manager.send_to_session({
                'type': 'message',
                'role': 'judge',
                'content': '📋 原告方辩论完毕，现在由被告方进行辩论。'
            }, session_id)
            await handle_party_turn(session_id, engine, Party.DEFENDANT, 'argument', user_role)
        else:
            # 被告辩论完毕，进入最后陈述阶段
            session['current_phase'] = DebatePhase.CLOSING_ARGUMENTS
            await manager.send_to_session({
                'type': 'message',
                'role': 'judge',
                'content': '⚖️ 法庭辩论阶段结束，现在进入最后陈述阶段，由原告方先发言。'
            }, session_id)
            await handle_party_turn(session_id, engine, Party.PLAINTIFF, 'closing_statement', user_role)
    
    elif current_turn_type == 'closing_statement':
        if current_party == Party.PLAINTIFF:
            # 原告最后陈述完毕，被告最后陈述
            await manager.send_to_session({
                'type': 'message',
                'role': 'judge',
                'content': '📋 原告方最后陈述完毕，现在由被告方进行最后陈述。'
            }, session_id)
            await handle_party_turn(session_id, engine, Party.DEFENDANT, 'closing_statement', user_role)
        else:
            # 被告最后陈述完毕，进入判决阶段
            session['current_phase'] = DebatePhase.VERDICT
            await manager.send_to_session({
                'type': 'message',
                'role': 'judge',
                'content': '⚖️ 最后陈述阶段结束，现在由本庭进行评议并作出判决。'
            }, session_id)
            await generate_ai_response(session_id, engine, Party.JUDGE, 'verdict')


async def handle_user_input(data: dict, session_id: str, engine: CourtroomEngine):
    """处理用户输入"""
    session = manager.get_session(session_id)
    if not session:
        return
    
    if not session['waiting_for_user']:
        logger.warning(f"会话 {session_id} 当前不等待用户输入")
        return
    
    content = data.get('content', '')
    if not content:
        logger.warning(f"用户输入内容为空")
        return
    
    # 记录用户输入
    current_party = session['current_party']
    role_name = '原告' if current_party == Party.PLAINTIFF else '被告'
    
    await manager.send_to_session({
        'type': 'message',
        'role': role_name,
        'party': current_party.value,
        'content': content,
        'is_user': True
    }, session_id)
    
    # 添加到历史记录
    session['debate_history'].append({
        'id': str(uuid.uuid4()),
        'phase': session['current_phase'],
        'party': current_party,
        'speaker_role': '用户',
        'content': content,
        'timestamp': datetime.now().isoformat()
    })
    
    # 重置等待状态
    session['waiting_for_user'] = False
    session['user_input_received'] = True
    session['user_input_content'] = content
    
    # 继续下一步
    turn_type = session['current_turn_type']
    await proceed_to_next_turn(session_id, engine, current_party, turn_type)


async def handle_audio_input(data: dict, session_id: str, engine: CourtroomEngine):
    """处理音频输入（语音识别）"""
    # 这里可以集成语音识别服务
    # 目前先作为文本输入处理
    transcript = data.get('transcript', '')
    if transcript:
        await handle_user_input({'content': transcript}, session_id, engine)


async def handle_skip_turn(data: dict, session_id: str, engine: CourtroomEngine):
    """跳过当前轮次"""
    session = manager.get_session(session_id)
    if not session or not session['waiting_for_user']:
        return
    
    # 使用 AI 生成默认内容
    current_party = session['current_party']
    turn_type = session['current_turn_type']
    
    session['waiting_for_user'] = False
    
    # 生成 AI 响应
    await generate_ai_response(session_id, engine, current_party, turn_type)


async def handle_restart(data: dict, session_id: str, engine: CourtroomEngine, user_role: str):
    """重新开始庭审"""
    session = manager.get_session(session_id)
    if not session:
        return
    
    # 重置会话状态
    session['current_phase'] = DebatePhase.OPENING_STATEMENTS
    session['current_party'] = Party.PLAINTIFF
    session['debate_history'] = []
    session['waiting_for_user'] = False
    session['user_input_received'] = False
    session['user_input_content'] = None
    
    # 重新开始
    await start_courtroom_session(session_id, engine, user_role)


async def handle_end_session(data: dict, session_id: str):
    """结束庭审会话"""
    session = manager.get_session(session_id)
    if not session:
        return
    
    # 发送结束事件
    await manager.send_to_session({
        'type': 'session_end',
        'message': '庭审已结束',
        'debate_history': session['debate_history']
    }, session_id)
    
    # 标记会话为非活跃
    session['is_active'] = False
    
    logger.info(f"庭审会话 {session_id} 已结束")


def get_connection_stats():
    """获取连接统计信息"""
    return {
        'total_connections': len(manager.active_connections),
        'active_sessions': len([s for s in manager.courtroom_sessions.values() if s['is_active']]),
        'sessions': [
            {
                'session_id': session_id,
                'user_role': session['user_role'],
                'current_phase': session['current_phase'].value,
                'waiting_for_user': session['waiting_for_user'],
                'debate_history_length': len(session['debate_history'])
            }
            for session_id, session in manager.courtroom_sessions.items()
        ]
    }