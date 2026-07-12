"""数字人智能助手服务。"""

import json
import re
import uuid
from datetime import datetime, timedelta, timezone
from typing import Dict, List, Optional

from langchain_core.messages import AIMessage, HumanMessage, SystemMessage

from core.database import SessionLocal
from core.logger import app_logger
from models.db_models import DigitalHumanMessage, DigitalHumanRequest, DigitalHumanSession
from services.llm_factory import LLMFactory


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


class DigitalHumanService:
    """负责数字人的简单问答、意图识别和多轮会话。"""

    def __init__(self) -> None:
        self.llm = LLMFactory.create_llm()
        self.system_prompt = self._get_system_prompt()
        app_logger.info("数字人智能助手服务初始化完成")

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

只返回一个合法 JSON 对象，不要输出 Markdown、代码块或额外说明：
{{"reply":"给用户的中文回复","intent":"general_chat","emotion":"talk_normal","confidence":0.8}}

confidence 必须是 0 到 1 之间的数字。用户意图不明确时使用 general_chat，并通过回复询问用户需要什么帮助。"""

    @staticmethod
    def _get_session_history(session_id: str, client_id: str) -> List[Dict[str, str]]:
        """从数据库读取指定会话最近 6 条消息，并恢复为正序。"""
        db = SessionLocal()
        try:
            session = db.get(DigitalHumanSession, session_id)
            if session is not None and session.user_id != client_id:
                raise PermissionError("无权访问该数字人会话")
            messages = (
                db.query(DigitalHumanMessage)
                .filter(DigitalHumanMessage.session_id == session_id)
                .order_by(
                    DigitalHumanMessage.created_at.desc(),
                    DigitalHumanMessage.id.desc(),
                )
                .limit(6)
                .all()
            )
            return [
                {"role": message.role, "content": message.content}
                for message in reversed(messages)
            ]
        finally:
            db.close()

    def _build_messages(self, session_id: str, client_id: str, question: str) -> List:
        messages = [SystemMessage(content=self.system_prompt)]
        for message in self._get_session_history(session_id, client_id):
            if message["role"] == "user":
                messages.append(HumanMessage(content=message["content"]))
            elif message["role"] == "assistant":
                messages.append(AIMessage(content=message["content"]))
        messages.append(HumanMessage(content=question))
        return messages

    @staticmethod
    def _save_exchange(
        session_id: str,
        client_id: str,
        question: str,
        parsed: Dict,
    ) -> None:
        """在同一事务中保存会话、用户消息和助手消息。"""
        db = SessionLocal()
        try:
            session = db.get(DigitalHumanSession, session_id)
            now = datetime.now(timezone.utc)
            if session is None:
                session = DigitalHumanSession(
                    id=session_id,
                    user_id=client_id,
                    title=question[:30],
                    is_active=True,
                )
                db.add(session)
                # 两个模型没有 ORM relationship，先落父记录以保证外键顺序。
                db.flush()
            else:
                if session.user_id != client_id:
                    raise PermissionError("无权访问该数字人会话")
                session.is_active = True
                session.updated_at = now

            db.add_all([
                DigitalHumanMessage(
                    id=uuid.uuid4().hex,
                    session_id=session_id,
                    role="user",
                    content=question,
                    created_at=now,
                ),
                DigitalHumanMessage(
                    id=uuid.uuid4().hex,
                    session_id=session_id,
                    role="assistant",
                    content=parsed["reply"],
                    intent=parsed["intent"],
                    emotion=parsed["emotion"],
                    confidence=parsed["confidence"],
                    created_at=now + timedelta(microseconds=1),
                ),
            ])
            db.commit()
        except Exception:
            db.rollback()
            raise
        finally:
            db.close()

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
        fallback = {
            "reply": "我还不太确定你的需求，可以换一种简单的说法告诉我吗？",
            "intent": "general_chat",
            "emotion": "talk_normal",
            "confidence": 0.0,
        }

        cleaned = raw_response.strip()
        cleaned = re.sub(r"^```(?:json)?\s*", "", cleaned, flags=re.IGNORECASE)
        cleaned = re.sub(r"\s*```$", "", cleaned)

        try:
            result = json.loads(cleaned)
        except (json.JSONDecodeError, TypeError):
            start = cleaned.find("{")
            end = cleaned.rfind("}")
            if start < 0 or end <= start:
                app_logger.warning("数字人响应不是有效 JSON")
                return fallback
            try:
                result = json.loads(cleaned[start:end + 1])
            except json.JSONDecodeError:
                app_logger.warning("数字人响应 JSON 解析失败")
                return fallback

        if not isinstance(result, dict):
            return fallback

        reply = result.get("reply")
        if not isinstance(reply, str) or not reply.strip():
            reply = fallback["reply"]

        intent = result.get("intent", "general_chat")
        if intent not in INTENT_ROUTE_MAP:
            intent = "general_chat"

        emotion = result.get("emotion", "talk_normal")
        if emotion not in VALID_EMOTIONS:
            emotion = "talk_normal"

        try:
            confidence = max(0.0, min(1.0, float(result.get("confidence", 0.0))))
        except (TypeError, ValueError):
            confidence = 0.0

        return {
            "reply": reply.strip(),
            "intent": intent,
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

        cached = self._begin_request(request_id, client_id, session_id)
        if cached is not None:
            return cached

        try:
            messages = self._build_messages(session_id, client_id, question)
            raw_response = self._invoke_llm_streaming(messages, llm)
            parsed = self._parse_llm_response(raw_response)
            self._save_exchange(session_id, client_id, question, parsed)

            route_info = INTENT_ROUTE_MAP[parsed["intent"]]
            should_route = parsed["confidence"] >= MIN_ROUTE_CONFIDENCE
            result = {
                **parsed,
                "route": route_info["route"] if should_route else None,
                "route_label": route_info["route_label"] if should_route else None,
                "session_id": session_id,
            }
            self._complete_request(request_id, result)
            return result
        except Exception:
            self._discard_request(request_id)
            raise

    @staticmethod
    def _begin_request(request_id: str, client_id: str, session_id: str) -> Optional[Dict]:
        db = SessionLocal()
        try:
            record = db.get(DigitalHumanRequest, request_id)
            if record is not None:
                if record.client_id != client_id:
                    raise PermissionError("无权访问该请求")
                if record.status == "completed" and record.response_json:
                    return json.loads(record.response_json)
                raise RuntimeError("该请求正在处理中")
            db.add(DigitalHumanRequest(
                request_id=request_id,
                client_id=client_id,
                session_id=session_id,
                status="processing",
            ))
            db.commit()
            return None
        except Exception:
            db.rollback()
            raise
        finally:
            db.close()

    @staticmethod
    def _complete_request(request_id: str, result: Dict) -> None:
        db = SessionLocal()
        try:
            record = db.get(DigitalHumanRequest, request_id)
            if record is not None:
                record.status = "completed"
                record.response_json = json.dumps(result, ensure_ascii=False)
                db.commit()
        finally:
            db.close()

    @staticmethod
    def _discard_request(request_id: str) -> None:
        db = SessionLocal()
        try:
            db.query(DigitalHumanRequest).filter(
                DigitalHumanRequest.request_id == request_id,
                DigitalHumanRequest.status == "processing",
            ).delete(synchronize_session=False)
            db.commit()
        finally:
            db.close()

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
