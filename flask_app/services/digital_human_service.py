"""数字人智能助手服务。"""

import json
import re
import uuid
from typing import Dict, List, Optional

from core.database import SessionLocal
from core.logger import app_logger
from models.db_models import DigitalHumanMessage, DigitalHumanSession
from services.llm_factory import LLMFactory
from services.conversation import ConversationOrchestrator


INTENT_ROUTE_MAP = {
    "legal_chat": {"route": "/chat", "route_label": "普法问答"},
    "contract_review": {"route": "/contract", "route_label": "合同审查"},
    "mock_court": {"route": "/debate", "route_label": "模拟法庭"},
    "dispute_center": {"route": "/dispute-center", "route_label": "纠纷中心"},
    "dispute_organize": {"route": "/dispute-organize", "route_label": "纠纷整理"},
    "knowledge_graph": {"route": "/knowledge-graphs", "route_label": "法律图谱"},
    "document_drafting": {"route": "/document-drafting", "route_label": "文书起草"},
    "legal_calculator": {"route": "/legal-calculator", "route_label": "法律计算器"},
    "case_analysis": {"route": "/case-analysis", "route_label": "案情推断"},
    "similar_documents": {"route": "/similar-documents", "route_label": "相似文书"},
    "general_chat": {"route": None, "route_label": None},
}

VALID_EMOTIONS = {
    "idle",
    "welcome",
    "thinking",
    "talk_normal",
    "serious",
    "success",
    "error",
    "handoff",
}
MIN_ROUTE_CONFIDENCE = 0.6
CONVERSATION_ROUTES = {
    "normal_chat",
    "labor_consultation",
    "labor_triage",
    "matter_interaction",
    "agent_continue",
    "workspace_guidance",
    "high_risk_handoff",
}


class DigitalHumanService:
    """负责数字人的简单问答、意图识别和多轮会话。"""

    def __init__(self) -> None:
        self.llm = LLMFactory.create_llm()
        self.system_prompt = self._get_system_prompt()
        self._orchestrator = self._build_orchestrator()
        app_logger.info("数字人智能助手服务初始化完成")

    def _build_orchestrator(self) -> ConversationOrchestrator:
        return ConversationOrchestrator(
            llm=self.llm,
            system_prompt=self.system_prompt,
            invoke_llm=self._invoke_llm_streaming,
            parse_llm_response=self._parse_llm_response,
            route_map=INTENT_ROUTE_MAP,
            min_route_confidence=MIN_ROUTE_CONFIDENCE,
        )

    @staticmethod
    def _get_system_prompt() -> str:
        intents = ", ".join(INTENT_ROUTE_MAP.keys())
        return f"""你是法务平台的数字人智能助手“法小助”。

你的用户可能是老人、小孩或不熟悉打字和法律术语的人。请始终亲切、耐心、简短，使用容易理解的中文。

你的职责：
1. 识别用户想使用的平台功能，并给出简洁引导。
2. 简单法律常识可以直接回答；复杂或个案问题引导到最合适的专业功能。
3. 不编造法律条文、案例或结论，不承诺案件结果。重要事项提醒用户咨询专业律师。
4. 只选择一个最符合用户当前需求的意图。

可选 intent 只能是：{intents}
可选 emotion 只能是：talk_normal、serious、success。

conversation_route 用于模糊场景的会话分流，只能是：
normal_chat、labor_consultation、labor_triage、matter_interaction、
agent_continue、workspace_guidance、high_risk_handoff。

只返回一个合法 JSON 对象，不要输出 Markdown、代码块或额外说明：
{{"reply":"给用户的中文回复","intent":"general_chat","conversation_route":"normal_chat","emotion":"talk_normal","confidence":0.8}}

confidence 必须是 0 到 1 之间的数字。用户意图不明确时使用 general_chat，并通过回复询问用户需要什么帮助。"""

    @staticmethod
    def _invoke_llm_streaming(messages: List, llm) -> str:
        chunks: List[str] = []
        for chunk in llm.stream(messages):
            content = getattr(chunk, "content", "")
            if isinstance(content, str):
                chunks.append(content)
        response = "".join(chunks).strip()
        if not response:
            raise ValueError("大模型返回了空内容")
        return response

    @staticmethod
    def _parse_llm_response(raw_response: str) -> Dict:
        """
        解析大语言模型(LLM)的原始响应，并将其转换为结构化的字典格式。
        该方法会尝试从原始响应中提取有效JSON数据，并进行必要的验证和规范化处理。
        如果解析失败或数据不符合要求，将返回默认的回退响应。
        Args:
            raw_response (str): 从大语言模型获取的原始响应字符串
        Returns:
            Dict: 包含解析后的回复内容、意图、情感和置信度的字典，格式如下：
                {
                    "reply": str,      # 回复内容
                    "intent": str,     # 意图类别
                    "emotion": str,    # 情感类别
                    "confidence": float # 置信度(0.0-1.0)
                }
        """
        # 定义默认的回退响应，当解析失败时使用
        fallback = {
            "reply": "我还不太确定你的需求，可以换一种简单的说法告诉我吗？",
            "intent": "general_chat",
            "conversation_route": None,
            "emotion": "talk_normal",
            "confidence": 0.0,
        }

        # 清理原始响应，移除可能的代码块标记
        cleaned = raw_response.strip()
        cleaned = re.sub(r"^```(?:json)?\s*", "", cleaned, flags=re.IGNORECASE)  # 移除开始的代码块标记
        cleaned = re.sub(r"\s*```$", "", cleaned)  # 移除结束的代码块标记

        try:
            # 尝试直接解析JSON
            result = json.loads(cleaned)
        except (json.JSONDecodeError, TypeError):
            # 如果直接解析失败，尝试提取可能存在的JSON部分
            start = cleaned.find("{")
            end = cleaned.rfind("}")
            if start < 0 or end <= start:
                app_logger.warning("数字人响应不是有效 JSON")
                return fallback
            try:
                # 尝试解析提取出的JSON部分
                result = json.loads(cleaned[start:end + 1])
            except json.JSONDecodeError:
                app_logger.warning("数字人响应 JSON 解析失败")
                return fallback

        # 验证解析结果是否为字典类型
        if not isinstance(result, dict):
            return fallback

        # 处理回复内容，确保是有效的非空字符串
        reply = result.get("reply")
        if not isinstance(reply, str) or not reply.strip():
            reply = fallback["reply"]

        # 处理意图，确保是有效的意图类别
        intent = result.get("intent", "general_chat")
        if intent not in INTENT_ROUTE_MAP:
            intent = "general_chat"
        conversation_route = result.get("conversation_route")
        if conversation_route not in CONVERSATION_ROUTES:
            conversation_route = None

        # 处理情感，确保是有效的情感类别
        emotion = result.get("emotion", "talk_normal")
        if emotion not in VALID_EMOTIONS:
            emotion = "talk_normal"

        # 处理置信度，确保在0.0到1.0范围内
        try:
            confidence = max(0.0, min(1.0, float(result.get("confidence", 0.0))))
        except (TypeError, ValueError):
            confidence = 0.0

        # 返回处理后的结果
        return {
            "reply": reply.strip(),
            "intent": intent,
            "conversation_route": conversation_route,
            "emotion": emotion,
            "confidence": confidence,
        }

    def chat(
        self,
        question: str,
        client_id: str,
        request_id: str,
        session_id: Optional[str] = None,
        custom_config: Optional[Dict[str, str]] = None,
    ) -> Dict:
        question = question.strip() if isinstance(question, str) else ""
        if not question:
            raise ValueError("问题不能为空")

        session_id = session_id or f"dh_{uuid.uuid4().hex}"
        if not session_id.startswith("dh_"):
            raise ValueError("数字人会话 ID 必须以 dh_ 开头")

        llm = self.llm
        if custom_config and custom_config.get("api_key"):
            llm = LLMFactory.create_llm(
                api_key=custom_config["api_key"],
                base_url=custom_config.get("base_url"),
                model=custom_config.get("model"),
            )

        orchestrator = getattr(self, "_orchestrator", None)
        if orchestrator is None:
            orchestrator = self._build_orchestrator()
            self._orchestrator = orchestrator
        return orchestrator.chat(
            question=question,
            client_id=client_id,
            request_id=request_id,
            session_id=session_id,
            llm=llm,
        )

    @staticmethod
    def list_sessions(client_id: str) -> List[Dict]:
        db = SessionLocal()
        try:
            sessions = db.query(DigitalHumanSession).filter(
                DigitalHumanSession.user_id == client_id
            ).order_by(DigitalHumanSession.updated_at.desc()).all()
            return [{
                "id": item.id, "title": item.title or "新对话",
                "created_at": item.created_at.isoformat() if item.created_at else None,
                "updated_at": item.updated_at.isoformat() if item.updated_at else None,
            } for item in sessions]
        finally:
            db.close()

    @staticmethod
    def get_messages(session_id: str, client_id: str) -> List[Dict]:
        db = SessionLocal()
        try:
            session = db.get(DigitalHumanSession, session_id)
            if session is None:
                raise LookupError("会话不存在")
            if session.user_id != client_id:
                raise PermissionError("无权访问该数字人会话")
            messages = db.query(DigitalHumanMessage).filter(
                DigitalHumanMessage.session_id == session_id
            ).order_by(DigitalHumanMessage.created_at, DigitalHumanMessage.id).all()
            return [{
                "id": item.id, "role": item.role, "content": item.content,
                "intent": item.intent, "emotion": item.emotion,
                "created_at": item.created_at.isoformat() if item.created_at else None,
            } for item in messages]
        finally:
            db.close()

    def reset_session(self, session_id: str, client_id: str) -> bool:
        db = SessionLocal()
        try:
            session = db.get(DigitalHumanSession, session_id)
            if session is None:
                return False
            if session.user_id != client_id:
                raise PermissionError("无权访问该数字人会话")
            db.query(DigitalHumanMessage).filter(
                DigitalHumanMessage.session_id == session_id
            ).delete(synchronize_session=False)
            deleted = db.query(DigitalHumanSession).filter(
                DigitalHumanSession.id == session_id
            ).delete(synchronize_session=False)
            db.commit()
            app_logger.info(f"数字人会话已重置 [session={session_id}]")
            return bool(deleted)
        except Exception:
            db.rollback()
            raise
        finally:
            db.close()


digital_human_service: Optional[DigitalHumanService] = None


def get_digital_human_service() -> DigitalHumanService:
    global digital_human_service
    if digital_human_service is None:
        digital_human_service = DigitalHumanService()
    return digital_human_service
