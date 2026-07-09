"""
庭审 WebSocket 服务
提供真实的法庭对话流，集成 LLM 实现智能交互
"""

import json
import logging
import threading
import time
import uuid
from typing import Dict, Any, Optional, List
from dataclasses import dataclass, field
from enum import Enum
from datetime import datetime

from core.logger import app_logger
from core.config import settings
from langchain_core.messages import HumanMessage, SystemMessage
from services.llm_factory import LLMFactory

logger = logging.getLogger(__name__)


class DebatePhase(Enum):
    """辩论阶段"""
    OPENING = "opening"
    ARGUMENT = "argument"
    CLOSING = "closing"
    VERDICT = "verdict"


class Party(Enum):
    """当事人"""
    PLAINTIFF = "plaintiff"
    DEFENDANT = "defendant"
    JUDGE = "judge"


@dataclass
class DebateTurn:
    """辩论回合"""
    id: str
    phase: str
    party: str
    content: str
    is_user: bool = False
    timestamp: str = field(default_factory=lambda: datetime.now().isoformat())


@dataclass
class CourtSession:
    """庭审会话"""
    id: str
    case_description: str
    user_role: str
    ws: Any = None
    current_phase: str = "opening"
    debate_history: List[DebateTurn] = field(default_factory=list)
    is_active: bool = True
    waiting_for_user: bool = False
    current_speaker: str = "judge"
    turn_count: int = 0
    max_turns: int = 20


class CourtroomWebSocketService:
    """庭审 WebSocket 服务"""
    
    def __init__(self):
        self.active_sessions: Dict[str, CourtSession] = {}
    
    def _invoke_llm(self, messages: list) -> str:
        """调用LLM生成回复"""
        max_retries = 3
        retry_delay = 2
        
        for attempt in range(max_retries):
            try:
                llm = LLMFactory.create_llm()
                
                langchain_messages = []
                for msg in messages:
                    msg_type = getattr(msg, 'type', None) or getattr(msg, '_type', None)
                    
                    if msg_type == 'system':
                        langchain_messages.append(msg)
                    elif msg_type == 'human':
                        langchain_messages.append(msg)
                    elif msg_type == 'ai':
                        langchain_messages.append(msg)
                    elif hasattr(msg, 'role') and hasattr(msg, 'content'):
                        if msg.role == 'system':
                            langchain_messages.append(SystemMessage(content=msg.content))
                        else:
                            langchain_messages.append(HumanMessage(content=msg.content))
                    else:
                        langchain_messages.append(msg)
                
                logger.info(f"LLM请求: messages_count={len(langchain_messages)}, types={[getattr(m, 'type', 'unknown') for m in langchain_messages]}")
                
                if not langchain_messages:
                    logger.error("消息列表为空，无法调用LLM")
                    return "抱歉，消息处理失败。"
                
                response = llm.invoke(langchain_messages)
                content = response.content
                logger.info(f"LLM调用成功，返回内容长度: {len(content)}")
                return content
                    
            except Exception as e:
                logger.warning(f"LLM调用失败 (尝试 {attempt + 1}/{max_retries}): {str(e)}")
                if attempt < max_retries - 1:
                    time.sleep(retry_delay)
                    retry_delay *= 2
                else:
                    return f"抱歉，AI服务暂时不可用，请稍后再试。"
        
        return "抱歉，AI服务暂时不可用，请稍后再试。"
    
    def start_session(self, ws, session_id: str, user_role: str, case_description: str = ""):
        """启动庭审会话"""
        logger.info(f"启动庭审会话: {session_id}, 用户角色: {user_role}")
        
        try:
            if not case_description:
                case_description = "原告与被告之间的合同纠纷案件，涉及违约责任和赔偿问题。"
            
            session = CourtSession(
                id=session_id,
                case_description=case_description,
                user_role=user_role,
                ws=ws,
                current_phase="opening"
            )
            
            self.active_sessions[session_id] = session
            
            self._send_message(session_id, {
                'type': 'connected',
                'role': 'system',
                'content': '庭审会话已创建，正在准备开庭...',
                'session_id': session_id
            })
            
            time.sleep(1)
            
            if user_role == 'auto':
                self._run_auto_mode(session_id)
            elif user_role == 'plaintiff':
                self._run_user_as_plaintiff(session_id)
            elif user_role == 'defendant':
                self._run_user_as_defendant(session_id)
            else:
                self._run_auto_mode(session_id)
                
        except Exception as e:
            logger.error(f"启动会话失败: {e}")
            self._send_message(session_id, {
                'type': 'error',
                'message': f'启动会话失败: {str(e)}'
            })
    
    def _run_auto_mode(self, session_id: str):
        """自动模式：完全AI对话"""
        session = self.active_sessions.get(session_id)
        if not session:
            return
        
        try:
            self._send_judge_message(session_id, "现在开庭。请原告陈述诉讼请求及事实理由。")
            time.sleep(2)
            
            plaintiff_msg = self._generate_ai_response(session_id, "plaintiff", "开庭陈述")
            self._send_plaintiff_message(session_id, plaintiff_msg, is_user=False)
            time.sleep(3)
            
            self._send_judge_message(session_id, "请被告进行答辩。")
            time.sleep(2)
            
            defendant_msg = self._generate_ai_response(session_id, "defendant", "答辩陈述", plaintiff_msg)
            self._send_defendant_message(session_id, defendant_msg, is_user=False)
            time.sleep(3)
            
            self._run_debate_phase(session_id, "auto")
            
        except Exception as e:
            logger.error(f"自动模式运行失败: {e}")
            self._send_error(session_id, str(e))
    
    def _run_user_as_plaintiff(self, session_id: str):
        """用户作为原告参与"""
        session = self.active_sessions.get(session_id)
        if not session:
            return
        
        try:
            self._send_judge_message(session_id, "现在开庭。原告，请陈述您的诉讼请求及事实理由。")
            time.sleep(1)
            
            self._wait_for_user_input(session_id, "plaintiff")
            
        except Exception as e:
            logger.error(f"用户原告模式失败: {e}")
            self._send_error(session_id, str(e))
    
    def _run_user_as_defendant(self, session_id: str):
        """用户作为被告参与"""
        session = self.active_sessions.get(session_id)
        if not session:
            return
        
        try:
            self._send_judge_message(session_id, "现在开庭。请原告陈述诉讼请求及事实理由。")
            time.sleep(2)
            
            plaintiff_msg = self._generate_ai_response(session_id, "plaintiff", "开庭陈述")
            self._send_plaintiff_message(session_id, plaintiff_msg, is_user=False)
            time.sleep(3)
            
            self._send_judge_message(session_id, "被告，请针对原告的陈述进行答辩。")
            time.sleep(1)
            
            self._wait_for_user_input(session_id, "defendant")
            
        except Exception as e:
            logger.error(f"用户被告模式失败: {e}")
            self._send_error(session_id, str(e))
    
    def _run_debate_phase(self, session_id: str, user_role: str):
        """运行辩论阶段"""
        session = self.active_sessions.get(session_id)
        if not session or not session.is_active:
            return

        session.current_phase = "argument"
        session.turn_count = 0  # 重置回合计数

        self._send_judge_message(session_id, "现在进入法庭辩论阶段。请双方就争议焦点进行辩论。")
        time.sleep(2)

        max_debate_turns = 6
        current_turn = 0
        
        while current_turn < max_debate_turns and session.is_active:
            if user_role == "auto":
                plaintiff_arg = self._generate_ai_response(
                    session_id, "plaintiff", "辩论发言",
                    self._get_last_message_by_role(session, "defendant")
                )
                self._send_plaintiff_message(session_id, plaintiff_arg, is_user=False)
                time.sleep(3)
                
                if not session.is_active:
                    break
                
                defendant_arg = self._generate_ai_response(
                    session_id, "defendant", "辩论发言",
                    self._get_last_message_by_role(session, "plaintiff")
                )
                self._send_defendant_message(session_id, defendant_arg, is_user=False)
                time.sleep(3)
                
            elif user_role == "plaintiff":
                self._wait_for_user_input(session_id, "plaintiff")
                
                if not session.is_active:
                    break
                
                defendant_arg = self._generate_ai_response(
                    session_id, "defendant", "辩论发言",
                    self._get_last_message_by_role(session, "plaintiff")
                )
                self._send_defendant_message(session_id, defendant_arg, is_user=False)
                time.sleep(3)
                
            elif user_role == "defendant":
                plaintiff_arg = self._generate_ai_response(
                    session_id, "plaintiff", "辩论发言",
                    self._get_last_message_by_role(session, "defendant")
                )
                self._send_plaintiff_message(session_id, plaintiff_arg, is_user=False)
                time.sleep(3)
                
                if not session.is_active:
                    break
                
                self._wait_for_user_input(session_id, "defendant")
            
            current_turn += 1
            
            if current_turn >= max_debate_turns // 2:
                self._send_judge_message(session_id, "双方已经充分发表了意见。现在进入最后陈述阶段。")
                break
        
        if session.is_active:
            self._run_closing_phase(session_id, user_role)
    
    def _run_closing_phase(self, session_id: str, user_role: str):
        """运行最后陈述阶段"""
        session = self.active_sessions.get(session_id)
        if not session or not session.is_active:
            return
        
        session.current_phase = "closing"
        
        if user_role == "auto":
            self._send_judge_message(session_id, "原告，请作最后陈述。")
            time.sleep(2)
            
            plaintiff_closing = self._generate_ai_response(session_id, "plaintiff", "最后陈述")
            self._send_plaintiff_message(session_id, plaintiff_closing, is_user=False)
            time.sleep(3)
            
            self._send_judge_message(session_id, "被告，请作最后陈述。")
            time.sleep(2)
            
            defendant_closing = self._generate_ai_response(session_id, "defendant", "最后陈述")
            self._send_defendant_message(session_id, defendant_closing, is_user=False)
            time.sleep(3)
            
        elif user_role == "plaintiff":
            self._send_judge_message(session_id, "原告，请作最后陈述。")
            time.sleep(1)
            self._wait_for_user_input(session_id, "plaintiff", is_closing=True)
            
        elif user_role == "defendant":
            self._send_judge_message(session_id, "原告，请作最后陈述。")
            time.sleep(2)
            
            plaintiff_closing = self._generate_ai_response(session_id, "plaintiff", "最后陈述")
            self._send_plaintiff_message(session_id, plaintiff_closing, is_user=False)
            time.sleep(3)
            
            self._send_judge_message(session_id, "被告，请作最后陈述。")
            time.sleep(1)
            self._wait_for_user_input(session_id, "defendant", is_closing=True)
        
        if session.is_active:
            self._run_verdict_phase(session_id)
    
    def _run_verdict_phase(self, session_id: str):
        """运行宣判阶段"""
        session = self.active_sessions.get(session_id)
        if not session or not session.is_active:
            return
        
        session.current_phase = "verdict"
        
        self._send_judge_message(session_id, "庭审结束，本庭将在评议后作出判决。")
        time.sleep(2)
        
        verdict = self._generate_verdict(session_id)
        self._send_judge_message(session_id, verdict)
        
        self._send_message(session_id, {
            'type': 'session_end',
            'message': '庭审已结束'
        })
        
        session.is_active = False
    
    def _generate_ai_response(self, session_id: str, party: str, phase: str, 
                             previous_content: str = "") -> str:
        """使用LLM生成AI回复"""
        session = self.active_sessions.get(session_id)
        if not session:
            return "抱歉，会话不存在。"
        
        role_name = "原告律师" if party == "plaintiff" else "被告律师"
        opponent = "被告" if party == "plaintiff" else "原告"
        
        system_prompt = f"""你是一位经验丰富的{role_name}，正在参与一场民事案件的庭审。
你需要根据案件情况和庭审进程，发表专业、有说服力的发言。

案件描述：{session.case_description}

你的角色：{role_name}
当前阶段：{phase}

发言要求：
1. 严格根据案件描述中的具体信息进行发言，包括人物、时间、地点、事件等
2. 不要使用"XXX"等模糊或占位符词汇，所有信息必须具体明确
3. 紧扣案件事实和法律依据
4. 针对对方的观点进行反驳或补充
5. 语言专业、逻辑清晰
6. 发言长度控制在200-300字
7. 不要使用表情符号和特殊字符"""

        if previous_content:
            user_prompt = f"{opponent}方刚才说：\n\n{previous_content}\n\n请针对以上内容进行回应。"
        else:
            if phase == "开庭陈述":
                user_prompt = "请发表你的开庭陈述，包括案件事实、法律依据和诉讼请求/答辩意见。"
            elif phase == "辩论发言":
                user_prompt = "请发表你的辩论意见，针对争议焦点进行论述。"
            elif phase == "最后陈述":
                user_prompt = "请发表你的最后陈述，总结你的观点和请求。"
            else:
                user_prompt = "请发表你的意见。"
        
        try:
            response = self._invoke_llm([
                SystemMessage(content=system_prompt),
                HumanMessage(content=user_prompt)
            ])
            return response
        except Exception as e:
            logger.error(f"生成AI回复失败: {e}")
            return f"作为{role_name}，我方坚持我们的主张。"
    
    def _generate_verdict(self, session_id: str) -> str:
        """生成判决"""
        session = self.active_sessions.get(session_id)
        if not session:
            return "判决生成失败。"
        
        history_text = ""
        for turn in session.debate_history:
            role_name = {"plaintiff": "原告", "defendant": "被告", "judge": "法官"}.get(turn.party, turn.party)
            history_text += f"\n{role_name}：{turn.content}\n"
        
        system_prompt = f"""你是一位公正的审判长，需要根据庭审情况作出判决。

案件描述：{session.case_description}

庭审记录：
{history_text}

请作出判决，包括：
1. 案件事实认定（严格根据案件描述中的具体信息）
2. 法律适用
3. 判决结果

判决书格式要求：
- 严格根据案件描述中的具体信息进行判决，包括人物、时间、地点、事件等
- 不要使用"XXX"等模糊或占位符词汇，所有信息必须具体明确
- 语言专业、严谨
- 结论明确
- 长度控制在300-400字
- 不要使用表情符号"""

        try:
            response = self._invoke_llm([
                SystemMessage(content=system_prompt),
                HumanMessage(content="请作出判决。")
            ])
            return response
        except Exception as e:
            logger.error(f"生成判决失败: {e}")
            return "本庭经审理，判决如下：驳回原告/被告的诉讼请求。"
    
    def _wait_for_user_input(self, session_id: str, party: str, is_closing: bool = False):
        """等待用户输入"""
        session = self.active_sessions.get(session_id)
        if not session:
            return
        
        session.waiting_for_user = True
        session.current_speaker = party
        
        self._send_message(session_id, {
            'type': 'user_turn',
            'user_role': party,
            'message': f"现在轮到您发言。"
        })
        
        wait_count = 0
        max_wait = 180
        
        while session.waiting_for_user and session.is_active and wait_count < max_wait:
            time.sleep(1)
            wait_count += 1
        
        if session.waiting_for_user:
            session.waiting_for_user = False
            default_msg = self._generate_ai_response(session_id, party, "发言")
            
            if party == "plaintiff":
                self._send_plaintiff_message(session_id, default_msg, is_user=False)
            else:
                self._send_defendant_message(session_id, default_msg, is_user=False)
            
            time.sleep(2)
            
            self._continue_after_user_input(session_id, party, is_closing)
    
    def _continue_after_user_input(self, session_id: str, party: str, is_closing: bool = False):
        """用户输入后继续庭审流程"""
        session = self.active_sessions.get(session_id)
        if not session or not session.is_active:
            logger.warning(f"_continue_after_user_input: 会话不存在或未激活")
            return

        user_role = session.user_role
        logger.info(f"_continue_after_user_input: session_id={session_id}, party={party}, is_closing={is_closing}, current_phase={session.current_phase}, turn_count={session.turn_count}, user_role={user_role}")

        if is_closing:
            logger.info(f"进入判决阶段")
            self._run_verdict_phase(session_id)
            return

        if session.current_phase == "opening":
            if user_role == "plaintiff":
                self._send_judge_message(session_id, "请被告进行答辩。")
                time.sleep(2)
                
                defendant_msg = self._generate_ai_response(
                    session_id, "defendant", "答辩陈述",
                    self._get_last_message_by_role(session, "plaintiff")
                )
                self._send_defendant_message(session_id, defendant_msg, is_user=False)
                time.sleep(3)
                
                self._run_debate_phase(session_id, user_role)
                
            elif user_role == "defendant":
                self._run_debate_phase(session_id, user_role)
        
        elif session.current_phase == "argument":
            if user_role == "plaintiff":
                defendant_arg = self._generate_ai_response(
                    session_id, "defendant", "辩论发言",
                    self._get_last_message_by_role(session, "plaintiff")
                )
                self._send_defendant_message(session_id, defendant_arg, is_user=False)
                time.sleep(3)

                session.turn_count += 1
                logger.info(f"原告模式: turn_count={session.turn_count}")
                if session.turn_count >= 3:
                    self._send_judge_message(session_id, "双方已经充分发表了意见。现在进入最后陈述阶段。")
                    self._run_closing_phase(session_id, user_role)
                else:
                    self._wait_for_user_input(session_id, "plaintiff")

            elif user_role == "defendant":
                session.turn_count += 1
                logger.info(f"被告模式: turn_count={session.turn_count}")
                if session.turn_count >= 3:
                    logger.info(f"被告模式: turn_count >= 3，进入closing phase")
                    self._send_judge_message(session_id, "双方已经充分发表了意见。现在进入最后陈述阶段。")
                    self._run_closing_phase(session_id, user_role)
                else:
                    logger.info(f"被告模式: 生成原告发言")
                    plaintiff_arg = self._generate_ai_response(
                        session_id, "plaintiff", "辩论发言",
                        self._get_last_message_by_role(session, "defendant")
                    )
                    self._send_plaintiff_message(session_id, plaintiff_arg, is_user=False)
                    time.sleep(3)

                    self._wait_for_user_input(session_id, "defendant")
    
    def handle_user_input(self, session_id: str, content: str) -> bool:
        """处理用户输入"""
        logger.info(f"handle_user_input: session_id={session_id}, content={content[:50]}...")
        session = self.active_sessions.get(session_id)
        if not session:
            logger.warning(f"会话不存在: {session_id}")
            return False

        if not session.waiting_for_user:
            logger.warning(f"会话不在等待用户输入状态: {session_id}, waiting_for_user={session.waiting_for_user}")
            return False

        party = session.current_speaker
        logger.info(f"处理用户输入: party={party}, current_phase={session.current_phase}, turn_count={session.turn_count}")

        if party == "plaintiff":
            self._send_plaintiff_message(session_id, content, is_user=True)
        else:
            self._send_defendant_message(session_id, content, is_user=True)

        session.waiting_for_user = False

        time.sleep(1)

        self._continue_after_user_input(session_id, party, session.current_phase == "closing")

        return True
    
    def _get_last_message_by_role(self, session: CourtSession, role: str) -> str:
        """获取指定角色的最后一条消息"""
        for turn in reversed(session.debate_history):
            if turn.party == role:
                return turn.content
        return ""
    
    def _send_judge_message(self, session_id: str, content: str):
        """发送法官消息"""
        session = self.active_sessions.get(session_id)
        if not session:
            return
        
        turn = DebateTurn(
            id=str(uuid.uuid4()),
            phase=session.current_phase,
            party="judge",
            content=content
        )
        session.debate_history.append(turn)
        
        self._send_message(session_id, {
            'type': 'message',
            'role': 'judge',
            'content': content,
            'phase': session.current_phase
        })
    
    def _send_plaintiff_message(self, session_id: str, content: str, is_user: bool = False):
        """发送原告消息"""
        session = self.active_sessions.get(session_id)
        if not session:
            return
        
        turn = DebateTurn(
            id=str(uuid.uuid4()),
            phase=session.current_phase,
            party="plaintiff",
            content=content,
            is_user=is_user
        )
        session.debate_history.append(turn)
        
        self._send_message(session_id, {
            'type': 'message',
            'role': 'plaintiff',
            'content': content,
            'is_user': is_user,
            'phase': session.current_phase
        })
    
    def _send_defendant_message(self, session_id: str, content: str, is_user: bool = False):
        """发送被告消息"""
        session = self.active_sessions.get(session_id)
        if not session:
            return
        
        turn = DebateTurn(
            id=str(uuid.uuid4()),
            phase=session.current_phase,
            party="defendant",
            content=content,
            is_user=is_user
        )
        session.debate_history.append(turn)
        
        self._send_message(session_id, {
            'type': 'message',
            'role': 'defendant',
            'content': content,
            'is_user': is_user,
            'phase': session.current_phase
        })
    
    def _send_error(self, session_id: str, message: str):
        """发送错误消息"""
        self._send_message(session_id, {
            'type': 'error',
            'message': message
        })
    
    def _send_message(self, session_id: str, message: dict):
        """发送消息到客户端"""
        session = self.active_sessions.get(session_id)
        if not session:
            return
        
        try:
            if session.ws:
                session.ws.send(json.dumps(message))
                logger.debug(f"消息已发送: {message.get('type')}")
        except Exception as e:
            logger.error(f"发送消息失败: {e}")
    
    def end_session(self, session_id: str):
        """结束会话"""
        if session_id in self.active_sessions:
            self.active_sessions[session_id].is_active = False
            self.active_sessions[session_id].waiting_for_user = False
            logger.info(f"会话已结束: {session_id}")
    
    def is_waiting_for_user(self, session_id: str) -> bool:
        """检查是否在等待用户输入"""
        session = self.active_sessions.get(session_id)
        return session.waiting_for_user if session else False


_courtroom_ws_service = None

def get_courtroom_websocket_service():
    """获取庭审 WebSocket 服务实例"""
    global _courtroom_ws_service
    if _courtroom_ws_service is None:
        _courtroom_ws_service = CourtroomWebSocketService()
    return _courtroom_ws_service
