"""
模拟法庭引擎

提供最严密、最复杂、最高级的法庭辩论逻辑
基于真实法律专业知识和 LLM 智能分析
保障人民权益
"""

import uuid
import json
import re
from datetime import datetime
from typing import List, Dict, Optional, Tuple
from dataclasses import dataclass, field, asdict
from enum import Enum

from core.logger import app_logger
from core.database import SessionLocal
from models.db_models import Case as DBCase, CourtSession as DBCourtSession, Evidence as DBEvidence, LegalIssue as DBLegalIssue, DebateTurn as DBDebateTurn
from services.llm_factory import LLMFactory
from langchain_core.messages import HumanMessage, SystemMessage


class DebatePhase(Enum):
    """辩论阶段"""
    OPENING = "opening"           # 开庭陈述
    EVIDENCE = "evidence"         # 举证质证
    ARGUMENT = "argument"         # 法庭辩论
    CLOSING = "closing"           # 最后陈述
    DELIBERATION = "deliberation" # 法官评议
    VERDICT = "verdict"           # 宣判


class Party(Enum):
    """当事人"""
    PLAINTIFF = "plaintiff"       # 原告
    DEFENDANT = "defendant"       # 被告
    JUDGE = "judge"               # 法官


@dataclass
class EvidenceData:
    """证据数据"""
    id: str
    party: Party
    name: str
    content: str
    evidence_type: str  # 书证、物证、证人证言、视听资料、电子数据等
    probative_force: int = 0  # 证明力 0-100
    is_authenticated: bool = False  # 是否经过质证
    authentication_opinion: str = ""  # 质证意见
    created_at: str = field(default_factory=lambda: datetime.now().isoformat())


@dataclass
class DebateTurnData:
    """辩论回合数据"""
    id: str
    phase: DebatePhase
    party: Party
    speaker_role: str  # 代理律师、当事人、法官等
    content: str
    legal_basis: List[str] = field(default_factory=list)
    facts_stated: List[str] = field(default_factory=list)
    arguments_made: List[str] = field(default_factory=list)
    counter_arguments: List[str] = field(default_factory=list)
    timestamp: str = field(default_factory=lambda: datetime.now().isoformat())


@dataclass
class LegalIssueData:
    """法律争议点数据"""
    id: str
    description: str
    relevant_law: str
    plaintiff_position: str
    defendant_position: str
    judge_analysis: str = ""
    conclusion: str = ""
    is_resolved: bool = False


@dataclass
class CaseData:
    """案件数据"""
    id: str
    title: str
    case_type: str  # 民事、刑事、行政等
    case_description: str
    plaintiff_claims: List[str] = field(default_factory=list)
    defendant_defenses: List[str] = field(default_factory=list)
    evidence_list: List[EvidenceData] = field(default_factory=list)
    legal_issues: List[LegalIssueData] = field(default_factory=list)
    created_at: str = field(default_factory=lambda: datetime.now().isoformat())


@dataclass
class CourtSessionData:
    """庭审会话数据"""
    id: str
    case: CaseData
    current_phase: DebatePhase
    debate_history: List[DebateTurnData] = field(default_factory=list)
    is_active: bool = True
    verdict: str = ""
    reasoning: str = ""
    created_at: str = field(default_factory=lambda: datetime.now().isoformat())
    updated_at: str = field(default_factory=lambda: datetime.now().isoformat())


class CourtroomEngine:
    """
    模拟法庭引擎
    
    提供最严密的法庭辩论逻辑和智能裁决系统
    """
    
    def __init__(self):
        self.sessions: Dict[str, CourtSessionData] = {}
    
    def _invoke_llm(self, messages: list) -> str:
        """
        调用LLM，使用流式传输方式，避免长响应中断问题
        """
        import time
        import httpx
        import json
        from core.config import settings
        
        max_retries = 3
        retry_delay = 2
        
        for attempt in range(max_retries):
            try:
                app_logger.info(f"直接调用DeepSeek API (流式传输, 尝试 {attempt + 1}/{max_retries})")
                
                # 转换消息格式，将SystemMessage和HumanMessage对象转换为字典
                formatted_messages = []
                for msg in messages:
                    if hasattr(msg, 'role') and hasattr(msg, 'content'):
                        formatted_messages.append({
                            "role": msg.role,
                            "content": msg.content
                        })
                    elif hasattr(msg, '_type'):
                        if msg._type == 'system':
                            formatted_messages.append({
                                "role": "system",
                                "content": msg.content
                            })
                        elif msg._type == 'human':
                            formatted_messages.append({
                                "role": "user",
                                "content": msg.content
                            })
                    elif hasattr(msg, 'type'):
                        if msg.type == 'system':
                            formatted_messages.append({
                                "role": "system",
                                "content": msg.content
                            })
                        elif msg.type == 'human':
                            formatted_messages.append({
                                "role": "user",
                                "content": msg.content
                            })
                    else:
                        try:
                            formatted_messages.append({
                                "role": msg.get('role', 'user'),
                                "content": msg.get('content', '')
                            })
                        except:
                            app_logger.error(f"无法转换消息: {msg}")
                
                app_logger.info(f"格式化后的消息数量: {len(formatted_messages)}")
                
                # 构建请求数据
                payload = {
                    "model": settings.OPENAI_MODEL,
                    "messages": formatted_messages,
                    "temperature": float(settings.OPENAI_TEMPERATURE),
                    "max_tokens": int(settings.OPENAI_MAX_TOKENS),
                    "stream": True  # 启用流式传输
                }
                
                # 设置请求头
                headers = {
                    "Content-Type": "application/json",
                    "Authorization": f"Bearer {settings.OPENAI_API_KEY}"
                }
                
                # 使用流式传输发送请求
                client = httpx.Client(timeout=180.0)
                content = ""
                
                try:
                    with client.stream(
                        "POST",
                        f"{settings.OPENAI_BASE_URL}/chat/completions",
                        json=payload,
                        headers=headers
                    ) as response:
                        if response.status_code == 200:
                            # 接收流式数据
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
                                                    content += chunk_content
                                        except json.JSONDecodeError:
                                            continue
                            
                            app_logger.info(f"API调用成功，返回内容长度: {len(content)} 字符")
                            return content
                        else:
                            error_text = ""
                            try:
                                for line in response.iter_lines():
                                    if line:
                                        error_text += line
                            except:
                                pass
                            app_logger.error(f"API调用失败: {response.status_code} - {error_text[:200]}")
                            raise Exception(f"API调用失败: {response.status_code}")
                finally:
                    client.close()
                    
            except Exception as e:
                app_logger.warning(f"LLM调用失败 (尝试 {attempt + 1}/{max_retries}): {str(e)}")
                if attempt < max_retries - 1:
                    app_logger.info(f"等待 {retry_delay} 秒后重试...")
                    time.sleep(retry_delay)
                    retry_delay *= 2
                else:
                    app_logger.error(f"所有重试均失败，返回错误信息")
                    return f"抱歉，AI服务暂时不可用，请稍后重试。错误: {str(e)}"
        
        return "抱歉，AI服务暂时不可用，请稍后重试。"
    
    def create_session(self, case_description: str, case_type: str = "民事纠纷") -> CourtSessionData:
        """
        创建新的庭审会话
        
        Args:
            case_description: 案件描述
            case_type: 案件类型
            
        Returns:
            CourtSessionData: 庭审会话
        """
        # 创建临时案件（使用默认值）
        case = CaseData(
            id=str(uuid.uuid4()),
            title="正在分析案件...",
            case_type=case_type,
            case_description=case_description,
            plaintiff_claims=[],
            defendant_defenses=[],
            legal_issues=[]
        )
        
        # 创建数据库会话
        db = SessionLocal()
        try:
            # 创建案件记录
            db_case = DBCase(
                id=case.id,
                title=case.title,
                case_type=case.case_type,
                case_description=case.case_description,
                plaintiff_claims=case.plaintiff_claims,
                defendant_defenses=case.defendant_defenses
            )
            db.add(db_case)
            db.commit()
            db.refresh(db_case)
            
            # 创建庭审会话
            session = CourtSessionData(
                id=str(uuid.uuid4()),
                case=case,
                current_phase=DebatePhase.OPENING
            )
            
            # 创建数据库会话记录
            db_session = DBCourtSession(
                id=session.id,
                case_id=case.id,
                current_phase=session.current_phase.value,
                is_active=session.is_active,
                verdict=session.verdict,
                reasoning=session.reasoning
            )
            db.add(db_session)
            db.commit()
            db.refresh(db_session)
            
            self.sessions[session.id] = session
            
            app_logger.info(f"创建庭审会话: {session.id}, 案件: {case.title}")
            app_logger.info(f"会话已保存到数据库: {session.id}")
            
            # 在后台线程中分析案件
            def analyze_case_async():
                try:
                    # 分析案件
                    case_analysis = self._analyze_case(case_description, case_type)
                    
                    # 更新案件信息
                    case.title = case_analysis.get("title", "未命名案件")
                    case.plaintiff_claims = case_analysis.get("plaintiff_claims", [])
                    case.defendant_defenses = case_analysis.get("defendant_defenses", [])
                    
                    # 更新数据库中的案件信息
                    db_case.title = case.title
                    db_case.plaintiff_claims = case.plaintiff_claims
                    db_case.defendant_defenses = case.defendant_defenses
                    
                    # 清空旧的法律争议点
                    case.legal_issues.clear()
                    
                    # 创建法律争议点
                    for issue in case_analysis.get("legal_issues", []):
                        issue_id = str(uuid.uuid4())
                        legal_issue = LegalIssueData(
                            id=issue_id,
                            description=issue["description"],
                            relevant_law=issue["relevant_law"],
                            plaintiff_position=issue["plaintiff_position"],
                            defendant_position=issue["defendant_position"]
                        )
                        case.legal_issues.append(legal_issue)
                        
                        # 保存到数据库
                        db_issue = DBLegalIssue(
                            id=issue_id,
                            case_id=case.id,
                            description=issue["description"],
                            relevant_law=issue["relevant_law"],
                            plaintiff_position=issue["plaintiff_position"],
                            defendant_position=issue["defendant_position"]
                        )
                        db.add(db_issue)
                    
                    db.commit()
                    app_logger.info(f"案件分析完成并更新: {session.id}, 识别 {len(case.legal_issues)} 个法律争议点")
                    app_logger.info(f"案件分析结果已保存到数据库: {case.id}")
                    
                except Exception as e:
                    db.rollback()
                    app_logger.error(f"后台案件分析失败: {str(e)}")
                finally:
                    db.close()
            
            # 启动后台线程
            import threading
            thread = threading.Thread(target=analyze_case_async)
            thread.daemon = True
            thread.start()
            
            return session
            
        except Exception as e:
            db.rollback()
            app_logger.error(f"创建会话失败: {str(e)}")
            raise
        finally:
            if db:
                db.close()
    
    def _analyze_case(self, case_description: str, case_type: str) -> Dict:
        """
        使用 LLM 分析案件
        
        Args:
            case_description: 案件描述
            case_type: 案件类型
            
        Returns:
            Dict: 案件分析结果
        """
        prompt = f"""你是一位资深法律专家。请分析以下{case_type}案件，提取关键信息：

案件描述：
{case_description}

请提供以下信息（JSON格式）：
{{
    "title": "案件标题",
    "plaintiff_claims": ["原告主张1", "原告主张2"],
    "defendant_defenses": ["被告抗辩1", "被告抗辩2"],
    "legal_issues": [
        {{
            "description": "争议点描述",
            "relevant_law": "相关法律条文",
            "plaintiff_position": "原告立场",
            "defendant_position": "被告立场"
        }}
    ]
}}

只返回JSON，不要其他内容。"""

        try:
            content = self._invoke_llm([
                SystemMessage(content="你是一位专业的法律分析师，擅长从案件描述中提取关键法律要素。"),
                HumanMessage(content=prompt)
            ])
            
            # 提取JSON
            json_match = re.search(r'\{.*\}', content, re.DOTALL)
            if json_match:
                return json.loads(json_match.group())
            else:
                return {
                    "title": "未命名案件",
                    "plaintiff_claims": [],
                    "defendant_defenses": [],
                    "legal_issues": []
                }
        except Exception as e:
            app_logger.error(f"案件分析失败: {str(e)}")
            return {
                "title": "未命名案件",
                "plaintiff_claims": [],
                "defendant_defenses": [],
                "legal_issues": []
            }
    
    def submit_evidence(self, session_id: str, party: Party, evidence_name: str, 
                       evidence_content: str, evidence_type: str) -> EvidenceData:
        """
        提交证据
        
        Args:
            session_id: 会话ID
            party: 提交方
            evidence_name: 证据名称
            evidence_content: 证据内容
            evidence_type: 证据类型
            
        Returns:
            EvidenceData: 证据对象
        """
        if session_id not in self.sessions:
            raise ValueError(f"会话不存在: {session_id}")
        
        session = self.sessions[session_id]
        
        # 创建证据
        evidence = EvidenceData(
            id=str(uuid.uuid4()),
            party=party,
            name=evidence_name,
            content=evidence_content,
            evidence_type=evidence_type
        )
        
        # 添加到案件
        session.case.evidence_list.append(evidence)
        
        # 保存到数据库
        db = SessionLocal()
        try:
            db_evidence = DBEvidence(
                id=evidence.id,
                case_id=session.case.id,
                party=party.value,
                name=evidence_name,
                content=evidence_content,
                evidence_type=evidence_type
            )
            db.add(db_evidence)
            db.commit()
            app_logger.info(f"证据已提交并保存到数据库: {evidence.id}")
        except Exception as e:
            db.rollback()
            app_logger.error(f"证据保存失败: {str(e)}")
        finally:
            db.close()
        
        return evidence
    
    def generate_opening_statement(self, session_id: str, party: Party) -> str:
        """
        生成开庭陈述
        
        Args:
            session_id: 会话ID
            party: 当事人
            
        Returns:
            str: 开庭陈述内容
        """
        if session_id not in self.sessions:
            raise ValueError(f"会话不存在: {session_id}")
        
        session = self.sessions[session_id]
        case = session.case
        
        if party == Party.PLAINTIFF:
            claims = "\n".join([f"{i+1}. {claim}" for i, claim in enumerate(case.plaintiff_claims)])
            prompt = f"""作为原告代理律师，请为以下案件撰写开庭陈述：

案件：{case.title}
案件类型：{case.case_type}

原告主张：
{claims}

请撰写一份专业的开庭陈述，包括：
1. 对案件事实的陈述
2. 法律依据
3. 诉讼请求

要求：专业、严谨、有说服力。"""
        else:
            defenses = "\n".join([f"{i+1}. {defense}" for i, defense in enumerate(case.defendant_defenses)])
            prompt = f"""作为被告代理律师，请为以下案件撰写开庭陈述：

案件：{case.title}
案件类型：{case.case_type}

被告抗辩：
{defenses}

请撰写一份专业的开庭陈述，包括：
1. 对案件事实的陈述
2. 法律依据
3. 答辩意见

要求：专业、严谨、有说服力。"""
        
        try:
            content = self._invoke_llm([
                SystemMessage(content="你是一位经验丰富的诉讼律师，擅长撰写专业的法律文书。"),
                HumanMessage(content=prompt)
            ])
            
            # 记录辩论回合
            debate_turn = DebateTurnData(
                id=str(uuid.uuid4()),
                phase=DebatePhase.OPENING,
                party=party,
                speaker_role="代理律师",
                content=content
            )
            session.debate_history.append(debate_turn)
            
            # 保存到数据库
            db = SessionLocal()
            try:
                db_turn = DBDebateTurn(
                    id=debate_turn.id,
                    session_id=session_id,
                    phase=DebatePhase.OPENING.value,
                    party=party.value,
                    speaker_role="代理律师",
                    content=content
                )
                db.add(db_turn)
                db.commit()
                app_logger.info(f"开庭陈述已保存到数据库: {debate_turn.id}")
            except Exception as e:
                db.rollback()
                app_logger.error(f"开庭陈述保存失败: {str(e)}")
            finally:
                db.close()
            
            return content
            
        except Exception as e:
            app_logger.error(f"生成开庭陈述失败: {str(e)}")
            return "开庭陈述生成失败，请重试。"
    
    def generate_argument(self, session_id: str, party: Party, 
                         target_issue: Optional[LegalIssueData] = None) -> str:
        """
        生成法庭辩论意见
        
        Args:
            session_id: 会话ID
            party: 当事人
            target_issue: 目标争议点（可选）
            
        Returns:
            str: 辩论意见内容
        """
        if session_id not in self.sessions:
            raise ValueError(f"会话不存在: {session_id}")
        
        session = self.sessions[session_id]
        case = session.case
        
        if target_issue:
            issue_desc = f"争议点：{target_issue.description}"
        else:
            issue_desc = "针对对方的主张进行辩论"
        
        if party == Party.PLAINTIFF:
            position = target_issue.plaintiff_position if target_issue else "维护原告权益"
            prompt = f"""作为原告代理律师，请就以下争议点发表辩论意见：

案件：{case.title}
{issue_desc}

原告立场：{position}

请撰写一份专业的法庭辩论意见，包括：
1. 事实依据
2. 法律论证
3. 反驳对方观点

要求：逻辑严密、论据充分、有说服力。"""
        else:
            position = target_issue.defendant_position if target_issue else "维护被告权益"
            prompt = f"""作为被告代理律师，请就以下争议点发表辩论意见：

案件：{case.title}
{issue_desc}

被告立场：{position}

请撰写一份专业的法庭辩论意见，包括：
1. 事实依据
2. 法律论证
3. 反驳对方观点

要求：逻辑严密、论据充分、有说服力。"""
        
        try:
            content = self._invoke_llm([
                SystemMessage(content="你是一位经验丰富的诉讼律师，擅长法庭辩论。"),
                HumanMessage(content=prompt)
            ])
            
            # 记录辩论回合
            debate_turn = DebateTurnData(
                id=str(uuid.uuid4()),
                phase=DebatePhase.ARGUMENT,
                party=party,
                speaker_role="代理律师",
                content=content
            )
            session.debate_history.append(debate_turn)
            
            # 保存到数据库
            db = SessionLocal()
            try:
                db_turn = DBDebateTurn(
                    id=debate_turn.id,
                    session_id=session_id,
                    phase=DebatePhase.ARGUMENT.value,
                    party=party.value,
                    speaker_role="代理律师",
                    content=content
                )
                db.add(db_turn)
                db.commit()
                app_logger.info(f"辩论意见已保存到数据库: {debate_turn.id}")
            except Exception as e:
                db.rollback()
                app_logger.error(f"辩论意见保存失败: {str(e)}")
            finally:
                db.close()
            
            return content
            
        except Exception as e:
            app_logger.error(f"生成辩论意见失败: {str(e)}")
            return "辩论意见生成失败，请重试。"
    
    def generate_closing_statement(self, session_id: str, party: Party) -> str:
        """
        生成最后陈述
        
        Args:
            session_id: 会话ID
            party: 当事人
            
        Returns:
            str: 最后陈述内容
        """
        if session_id not in self.sessions:
            raise ValueError(f"会话不存在: {session_id}")
        
        session = self.sessions[session_id]
        case = session.case
        
        # 总结之前的辩论
        debate_summary = "\n".join([
            f"{turn.party.value}: {turn.content[:100]}..." 
            for turn in session.debate_history[-5:]  # 最近5轮
        ])
        
        if party == Party.PLAINTIFF:
            prompt = f"""作为原告代理律师，请为以下案件撰写最后陈述：

案件：{case.title}

辩论摘要：
{debate_summary}

请撰写一份专业的最后陈述，总结原告的主要观点和诉讼请求。
要求：简洁有力、重点突出。"""
        else:
            prompt = f"""作为被告代理律师，请为以下案件撰写最后陈述：

案件：{case.title}

辩论摘要：
{debate_summary}

请撰写一份专业的最后陈述，总结被告的主要抗辩意见。
要求：简洁有力、重点突出。"""
        
        try:
            content = self._invoke_llm([
                SystemMessage(content="你是一位经验丰富的诉讼律师，擅长总结陈词。"),
                HumanMessage(content=prompt)
            ])
            
            # 记录辩论回合
            debate_turn = DebateTurnData(
                id=str(uuid.uuid4()),
                phase=DebatePhase.CLOSING,
                party=party,
                speaker_role="代理律师",
                content=content
            )
            session.debate_history.append(debate_turn)
            
            # 保存到数据库
            db = SessionLocal()
            try:
                db_turn = DBDebateTurn(
                    id=debate_turn.id,
                    session_id=session_id,
                    phase=DebatePhase.CLOSING.value,
                    party=party.value,
                    speaker_role="代理律师",
                    content=content
                )
                db.add(db_turn)
                db.commit()
                app_logger.info(f"最后陈述已保存到数据库: {debate_turn.id}")
            except Exception as e:
                db.rollback()
                app_logger.error(f"最后陈述保存失败: {str(e)}")
            finally:
                db.close()
            
            return content
            
        except Exception as e:
            app_logger.error(f"生成最后陈述失败: {str(e)}")
            return "最后陈述生成失败，请重试。"
    
    def generate_verdict(self, session_id: str) -> Dict:
        """
        生成判决
        
        Args:
            session_id: 会话ID
            
        Returns:
            Dict: 判决结果
        """
        if session_id not in self.sessions:
            raise ValueError(f"会话不存在: {session_id}")
        
        session = self.sessions[session_id]
        case = session.case
        
        # 总结所有辩论
        debate_summary = "\n".join([
            f"{turn.party.value} ({turn.phase.value}): {turn.content[:150]}..." 
            for turn in session.debate_history
        ])
        
        # 法律争议点
        issues_summary = "\n".join([
            f"{i+1}. {issue.description}\n   原告：{issue.plaintiff_position}\n   被告：{issue.defendant_position}"
            for i, issue in enumerate(case.legal_issues)
        ])
        
        prompt = f"""作为法官，请根据以下案件信息和辩论记录作出判决：

案件：{case.title}
案件类型：{case.case_type}

法律争议点：
{issues_summary}

辩论记录：
{debate_summary}

请提供判决结果（JSON格式）：
{{
    "verdict": "判决主文",
    "reasoning": "判决理由",
    "legal_basis": ["适用法律条文1", "适用法律条文2"],
    "case_resolution": {{
        "issue1": "对争议点1的认定",
        "issue2": "对争议点2的认定"
    }}
}}

要求：
1. 判决要基于事实和法律
2. 理由要充分、逻辑严密
3. 体现公平正义

只返回JSON，不要其他内容。"""

        try:
            content = self._invoke_llm([
                SystemMessage(content="你是一位公正的法官，擅长根据事实和法律作出公正判决。"),
                HumanMessage(content=prompt)
            ])
            
            # 提取JSON
            json_match = re.search(r'\{.*\}', content, re.DOTALL)
            if json_match:
                verdict_data = json.loads(json_match.group())
            else:
                verdict_data = {
                    "verdict": "无法作出判决",
                    "reasoning": "辩论记录不足以支持判决",
                    "legal_basis": [],
                    "case_resolution": {}
                }
            
            # 更新会话
            session.verdict = verdict_data.get("verdict", "")
            session.reasoning = verdict_data.get("reasoning", "")
            session.current_phase = DebatePhase.VERDICT
            session.is_active = False
            
            # 记录判决
            debate_turn = DebateTurnData(
                id=str(uuid.uuid4()),
                phase=DebatePhase.VERDICT,
                party=Party.JUDGE,
                speaker_role="法官",
                content=verdict_data.get("verdict", "")
            )
            session.debate_history.append(debate_turn)
            
            # 保存到数据库
            db = SessionLocal()
            try:
                # 更新庭审会话
                db_session = db.query(DBCourtSession).filter(DBCourtSession.id == session_id).first()
                if db_session:
                    db_session.verdict = session.verdict
                    db_session.reasoning = session.reasoning
                    db_session.current_phase = DebatePhase.VERDICT.value
                    db_session.is_active = False
                
                # 保存判决记录
                db_turn = DBDebateTurn(
                    id=debate_turn.id,
                    session_id=session_id,
                    phase=DebatePhase.VERDICT.value,
                    party=Party.JUDGE.value,
                    speaker_role="法官",
                    content=verdict_data.get("verdict", "")
                )
                db.add(db_turn)
                db.commit()
                app_logger.info(f"判决已生成并保存到数据库: {session_id}")
            except Exception as e:
                db.rollback()
                app_logger.error(f"判决保存失败: {str(e)}")
            finally:
                db.close()
            
            return verdict_data
            
        except Exception as e:
            app_logger.error(f"生成判决失败: {str(e)}")
            return {
                "verdict": "判决生成失败",
                "reasoning": str(e),
                "legal_basis": [],
                "case_resolution": {}
            }
    
    def get_session(self, session_id: str) -> Optional[CourtSessionData]:
        """
        获取庭审会话
        
        Args:
            session_id: 会话ID
            
        Returns:
            CourtSessionData: 庭审会话，如果不存在则返回None
        """
        return self.sessions.get(session_id)
    
    def get_all_sessions(self) -> List[Dict]:
        """
        获取所有庭审会话列表
        
        Returns:
            List[Dict]: 会话列表
        """
        db = SessionLocal()
        try:
            sessions = db.query(DBCourtSession).order_by(DBCourtSession.created_at.desc()).all()
            result = []
            for session in sessions:
                # 获取案件信息
                case = db.query(DBCase).filter(DBCase.id == session.case_id).first()
                
                result.append({
                    "id": session.id,
                    "case_id": session.case_id,
                    "case_title": case.title if case else "未知案件",
                    "case_type": case.case_type if case else "未知类型",
                    "current_phase": session.current_phase,
                    "is_active": session.is_active,
                    "created_at": session.created_at.isoformat() if session.created_at else None,
                    "updated_at": session.updated_at.isoformat() if session.updated_at else None
                })
            return result
        except Exception as e:
            app_logger.error(f"获取会话列表失败: {str(e)}")
            return []
        finally:
            db.close()


# 全局引擎实例
courtroom_engine = None

def get_courtroom_engine():
    global courtroom_engine
    if courtroom_engine is None:
        courtroom_engine = CourtroomEngine()
    return courtroom_engine
