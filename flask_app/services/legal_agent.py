"""
法律 Agent 服务
"""

import uuid
from typing import Dict, List, Optional
from langchain_core.messages import HumanMessage, AIMessage, SystemMessage
from services.llm_factory import LLMFactory
from core.config import settings
from core.logger import app_logger
from core.database import SessionLocal
from models.db_models import LegalChatSession, LegalChatMessage


class LegalAgentService:
    """
    法律 Agent 服务类
    
    提供智能法律咨询功能，支持多轮对话和会话管理。
    基于 LangChain 框架，使用 DeepSeek API。
    
    Attributes:
        llm: LLM 实例（ChatOpenAI - DeepSeek API）
        sessions: 会话历史存储（session_id -> 消息列表）
        system_prompt: 系统提示词
    """
    
    def __init__(self):
        """
        初始化法律 Agent 服务
        
        创建 LLM 实例、初始化会话存储。
        
        Raises:
            Exception: 当 LLM 初始化失败时抛出异常
        """
        try:
            self.llm = LLMFactory.create_llm()
            self.sessions: Dict[str, List[Dict]] = {}
            self.system_prompt = self._get_system_prompt()
            
            app_logger.info("✅ 法律 Agent 服务初始化完成")
        except Exception as e:
            app_logger.error(f"❌ 法律 Agent 服务初始化失败: {str(e)}")
            raise
    
    def _get_system_prompt(self) -> str:
        """
        获取系统提示词
        
        构建法律助手的系统提示词，定义其角色、能力和行为准则。
        
        Returns:
            str: 系统提示词文本
        """
        return f"""你是一个专业的法律咨询助手，专注于{settings.DEFAULT_JURISDICTION}法律体系。

**重要原则：**
1. 使用通俗易懂的语言，避免复杂的法律术语，或在使用时提供清晰解释
2. 你提供的是一般性法律信息，不是专业法律建议
3. 始终建议用户在重要事项上咨询专业律师
4. 保持友好、耐心的态度
5. 如果不确定，诚实地说明，不要编造信息

**你的能力：**
- 解释常见法律概念和条款
- 回答基本的法律问题
- 分析简单合同的关键条款
- 提供法律程序的基本指导

**免责声明：**
⚠️ 本助手提供的信息仅供参考，不构成专业法律建议。如遇具体法律问题，请咨询持牌律师。

请始终保持专业、友好，帮助用户理解法律知识。"""
    
    def _get_session_history(self, session_id: str) -> List[Dict]:
        """
        获取指定会话的历史记录
        
        如果会话不存在，会自动创建一个空的会话。
        
        Args:
            session_id: 会话唯一标识
            
        Returns:
            List[Dict]: 会话历史消息列表
        """
        if session_id not in self.sessions:
            self.sessions[session_id] = []
            app_logger.debug(f"创建新会话: {session_id}")
        return self.sessions[session_id]
    
    def _build_messages(self, session_id: str, user_input: str) -> List:
        """
        构建 LLM 输入的消息列表
        
        包含系统提示词、历史对话（最近10条）和当前用户输入。
        
        Args:
            session_id: 会话唯一标识
            user_input: 用户当前输入
            
        Returns:
            List: LangChain 消息对象列表
        """
        messages = [SystemMessage(content=self.system_prompt)]
        
        # 添加历史对话（最近10条，避免上下文过长）
        history = self._get_session_history(session_id)
        for msg in history[-10:]:
            if msg["role"] == "user":
                messages.append(HumanMessage(content=msg["content"]))
            elif msg["role"] == "assistant":
                messages.append(AIMessage(content=msg["content"]))
        
        # 添加当前用户输入
        messages.append(HumanMessage(content=user_input))
        
        return messages
    
    def _invoke_llm_streaming(self, messages: list) -> str:
        """
        使用流式传输调用LLM，避免长响应中断问题
        
        Args:
            messages: 消息列表
            
        Returns:
            str: LLM响应内容
        """
        import httpx
        import json
        from core.config import settings
        
        # 转换消息格式
        formatted_messages = []
        for msg in messages:
            if hasattr(msg, '_type'):
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
                elif msg._type == 'ai':
                    formatted_messages.append({
                        "role": "assistant",
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
                    
                    app_logger.info(f"LLM调用成功，返回内容长度: {len(content)} 字符")
                    return content
                else:
                    error_text = ""
                    try:
                        for line in response.iter_lines():
                            if line:
                                error_text += line
                    except:
                        pass
                    app_logger.error(f"LLM调用失败: {response.status_code} - {error_text[:200]}")
                    raise Exception(f"LLM调用失败: {response.status_code}")
        finally:
            client.close()
        
        return content
    
    def chat(
        self, 
        question: str, 
        session_id: str = "default",
        custom_config: Optional[Dict] = None
    ) -> Dict:
        """
        处理用户法律咨询问题
        
        接收用户问题，调用 LLM 生成回答，并保存到会话历史中。
        如果处理失败，会返回友好的错误提示。
        
        Args:
            question: 用户的法律问题
            session_id: 会话唯一标识，默认为 "default"
            custom_config: 自定义 LLM 配置（可选），包含：
                - api_key: API Key
                - base_url: API Base URL
                - model: 模型名称
            
        Returns:
            Dict: 包含以下字段的字典：
                - answer (str): AI 生成的回答
                - session_id (str): 会话ID
                - sources (List[str]): 引用来源列表（当前为空，未来可扩展）
                - error (Optional[str]): 错误信息（仅在出错时存在）
        """
        if not question or not question.strip():
            return {
                "answer": "请输入您的法律问题。",
                "session_id": session_id,
                "sources": [],
                "error": "Empty question"
            }
        
        try:
            app_logger.info(f"📝 处理问题 [session={session_id}]: {question[:50]}...")
            
            # 如果提供了自定义配置，使用自定义 LLM
            llm_to_use = self.llm
            if custom_config and custom_config.get("api_key"):
                app_logger.info(f"🔧 使用自定义 LLM 配置")
                llm_to_use = LLMFactory.create_llm(
                    api_key=custom_config.get("api_key"),
                    base_url=custom_config.get("base_url"),
                    model=custom_config.get("model")
                )
            
            # 构建消息
            messages = self._build_messages(session_id, question)
            
            # 使用流式传输调用 LLM
            answer = self._invoke_llm_streaming(messages)
            
            # 保存到历史
            history = self._get_session_history(session_id)
            history.append({"role": "user", "content": question})
            history.append({"role": "assistant", "content": answer})
            
            # 保存到数据库
            db = SessionLocal()
            try:
                # 检查会话是否存在
                db_session = db.query(LegalChatSession).filter(LegalChatSession.id == session_id).first()
                if not db_session:
                    # 创建新会话
                    db_session = LegalChatSession(
                        id=session_id,
                        title=question[:50] + "..." if len(question) > 50 else question,
                        jurisdiction="中国",
                        is_active=True
                    )
                    db.add(db_session)
                    db.flush()  # 确保会话先被创建
                
                # 保存用户消息
                user_message = LegalChatMessage(
                    id=str(uuid.uuid4()),
                    session_id=session_id,
                    role="user",
                    content=question
                )
                db.add(user_message)
                
                # 保存AI回复
                ai_message = LegalChatMessage(
                    id=str(uuid.uuid4()),
                    session_id=session_id,
                    role="assistant",
                    content=answer
                )
                db.add(ai_message)
                
                db.commit()
                app_logger.info(f"✅ 回答生成成功 [session={session_id}]")
                app_logger.info(f"对话已保存到数据库: {session_id}")
            except Exception as e:
                db.rollback()
                app_logger.error(f"对话保存失败: {str(e)}")
            finally:
                db.close()
            
            return {
                "answer": answer,
                "session_id": session_id,
                "sources": []  # TODO: 未来可以添加法律条文引用来源
            }
        
        except Exception as e:
            app_logger.error(f"❌ 处理问题时出错 [session={session_id}]: {str(e)}")
            error_msg = "抱歉，处理您的问题时出现错误。请稍后重试，或咨询专业律师。"
            
            return {
                "answer": error_msg,
                "session_id": session_id,
                "sources": [],
                "error": str(e)
            }
    
    def reset_session(self, session_id: str) -> bool:
        """
        重置会话历史
        
        Args:
            session_id: 会话ID
            
        Returns:
            是否成功
        """
        try:
            # 重置内存中的会话
            if session_id in self.sessions:
                self.sessions[session_id] = []
            
            # 从数据库中删除会话消息
            db = SessionLocal()
            try:
                # 删除会话的所有消息
                db.query(LegalChatMessage).filter(LegalChatMessage.session_id == session_id).delete()
                
                # 删除会话记录
                db_session = db.query(LegalChatSession).filter(LegalChatSession.id == session_id).first()
                if db_session:
                    db.delete(db_session)
                
                db.commit()
                app_logger.info(f"会话已重置 [session={session_id}]")
                app_logger.info(f"会话已从数据库删除: {session_id}")
            except Exception as e:
                db.rollback()
                app_logger.error(f"数据库删除会话失败: {str(e)}")
            finally:
                db.close()
            
            return True
        except Exception as e:
            app_logger.error(f"重置会话失败 [session={session_id}]: {str(e)}")
            return False
    
    def get_session_history(self, session_id: str) -> List[Dict]:
        """
        获取会话历史
        
        Args:
            session_id: 会话ID
            
        Returns:
            会话历史列表
        """
        return self._get_session_history(session_id)
    
    def get_all_sessions(self) -> List[Dict]:
        """
        获取所有会话列表
        
        Returns:
            会话列表
        """
        db = SessionLocal()
        try:
            sessions = db.query(LegalChatSession).order_by(LegalChatSession.updated_at.desc()).all()
            result = []
            for session in sessions:
                # 获取最后一条消息
                last_message = db.query(LegalChatMessage).filter(
                    LegalChatMessage.session_id == session.id
                ).order_by(LegalChatMessage.created_at.desc()).first()
                
                # 获取消息数量
                message_count = db.query(LegalChatMessage).filter(
                    LegalChatMessage.session_id == session.id
                ).count()
                
                result.append({
                    "id": session.id,
                    "title": session.title,
                    "jurisdiction": session.jurisdiction,
                    "is_active": session.is_active,
                    "created_at": session.created_at.isoformat() if session.created_at else None,
                    "updated_at": session.updated_at.isoformat() if session.updated_at else None,
                    "last_message": last_message.content if last_message else None,
                    "last_message_time": last_message.created_at.isoformat() if last_message and last_message.created_at else None,
                    "message_count": message_count
                })
            return result
        except Exception as e:
            app_logger.error(f"获取会话列表失败: {str(e)}")
            return []
        finally:
            db.close()
    
    def get_session_messages(self, session_id: str) -> List[Dict]:
        """
        获取指定会话的所有消息
        
        Args:
            session_id: 会话ID
            
        Returns:
            消息列表
        """
        db = SessionLocal()
        try:
            messages = db.query(LegalChatMessage).filter(
                LegalChatMessage.session_id == session_id
            ).order_by(LegalChatMessage.created_at.asc()).all()
            
            return [{
                "id": msg.id,
                "role": msg.role,
                "content": msg.content,
                "created_at": msg.created_at.isoformat() if msg.created_at else None
            } for msg in messages]
        except Exception as e:
            app_logger.error(f"获取会话消息失败: {str(e)}")
            return []
        finally:
            db.close()

    def draft_document(self, user_input: str, document_type: str) -> str:
        """
        起草法律文档
        
        Args:
            user_input: 用户输入的文档需求
            document_type: 文档类型 (legal-document, contract-drafting, legal-opinion)
            
        Returns:
            str: 生成的文档内容
        """
        try:
            app_logger.info(f"开始起草{document_type}，内容: {user_input[:100]}...")
            
            # 根据文档类型构建提示词
            if document_type == 'legal-document':
                prompt = f"你是一名专业的法律文书起草专家，请根据以下需求起草一份法律文书：\n\n{user_input}\n\n请生成完整的法律文书，包括格式、条款和必要的法律内容。"
            elif document_type == 'contract-drafting':
                prompt = f"你是一名专业的合同起草专家，请根据以下需求起草一份合同：\n\n{user_input}\n\n请生成完整的合同文本，包括当事人信息、合同标的、权利义务、违约责任、争议解决等条款。"
            elif document_type == 'legal-opinion':
                prompt = f"你是一名专业的律师，请根据以下案情提供法律意见：\n\n{user_input}\n\n请分析案件的法律问题，提供专业的法律意见和建议。"
            else:
                prompt = f"请根据以下需求起草文档：\n\n{user_input}"
            
            # 构建消息
            messages = [
                SystemMessage(content="你是一名专业的法律文书起草专家，擅长起草各种法律文档。请根据用户的需求，生成专业、规范的法律文档。"),
                HumanMessage(content=prompt)
            ]
            
            # 调用 LLM 生成文档
            response = self.llm.invoke(messages)
            
            result = response.content
            app_logger.info(f"文档起草完成，长度: {len(result)} 字符")
            
            return result
        except Exception as e:
            app_logger.error(f"文档起草失败: {str(e)}")
            return f"文档起草失败: {str(e)}"


# 全局 Agent 实例
legal_agent = None

def get_legal_agent():
    global legal_agent
    if legal_agent is None:
        legal_agent = LegalAgentService()
    return legal_agent
