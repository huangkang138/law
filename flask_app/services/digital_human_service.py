"""数字人智能助手服务。"""

import json
import re
import time
import uuid
from typing import Dict, List, Optional

from langchain_core.messages import HumanMessage

from core.database import SessionLocal
from core.logger import app_logger
from models.db_models import DigitalHumanMessage, DigitalHumanRequest, DigitalHumanSession
from services.llm_factory import LLMFactory
from services.conversation import ConversationOrchestrator
from services.conversation.cancel import (
    ConversationCancelled,
    is_cancelled,
    set_cancelled,
)
from services.conversation.repository import ConversationRepository, RequestInProgress
from services.conversation.sse import (
    DEFAULT_CHUNK_DELAY,
    EVENT_COMPLETED,
    EVENT_DELTA,
    EVENT_ERROR,
    EVENT_STATUS,
    STATUS_ACCEPTED,
    STATUS_THINKING,
    encode_event,
    encode_voice_event,
    iter_text_chunks,
    stream_error_data,
)
from services.voice import VoiceOrchestrator, get_active_provider


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
        # 语音层独立于聊天编排：只消费最终展示文本，不进入 Chat Service 逻辑。
        self._voice_orchestrator = VoiceOrchestrator(provider=get_active_provider())
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
    def _invoke_llm_streaming(
        messages: List,
        llm,
        request_id: Optional[str] = None,
    ) -> str:
        raw = DigitalHumanService._stream_joined(llm, messages, request_id)
        if not raw:
            raise ValueError("大模型返回了空内容")
        if DigitalHumanService._parse_raw_json(raw, log_failure=False) is not None:
            return raw
        # 真实模型偶发忽略JSON格式要求：强化格式指令重试一次，
        # 重试仍失败时交由解析层做纯文本可靠降级。
        app_logger.warning(
            f"数字人LLM首次响应不是有效JSON(len={len(raw)})，强化格式要求重试一次"
        )
        retry_messages = [
            *messages,
            HumanMessage(content=(
                "请严格只返回一个合法JSON对象，格式为 "
                '{"reply":"给用户的中文回复","intent":"general_chat",'
                '"conversation_route":"normal_chat","emotion":"talk_normal","confidence":0.8}，'
                "不要输出任何其他文字或Markdown。"
            )),
        ]
        raw = DigitalHumanService._stream_joined(llm, retry_messages, request_id)
        if not raw:
            raise ValueError("大模型返回了空内容")
        if DigitalHumanService._parse_raw_json(raw, log_failure=False) is None:
            app_logger.warning(
                f"数字人LLM重试响应仍不是有效JSON(len={len(raw)})，交由解析层降级"
            )
        return raw

    @staticmethod
    def _stream_joined(llm, messages, request_id: Optional[str] = None) -> str:
        chunks: List[str] = []
        stream = llm.stream(messages)
        try:
            for chunk in stream:
                if request_id and is_cancelled(request_id, poll_db=True):
                    # 停止消费并显式关闭流：GeneratorExit 沿
                    # langchain/openai/httpx 关闭链中止在途模型请求。
                    break
                content = getattr(chunk, "content", "")
                if isinstance(content, str):
                    chunks.append(content)
        finally:
            close = getattr(stream, "close", None)
            if close is not None:
                try:
                    close()
                except Exception:
                    pass
        if request_id and is_cancelled(request_id):
            raise ConversationCancelled()
        return "".join(chunks).strip()

    @staticmethod
    def _parse_llm_response(raw_response: str) -> Dict:
        """
        解析大语言模型(LLM)的原始响应，并将其转换为结构化的字典格式。
        解析链：清理代码围栏 → 直接JSON → 平衡提取 → 修复后解析；
        全部失败时先降级为模型纯文本回复，最后才使用固定兜底回复。
        路由仍由服务端确定性规则重新决定，本方法只负责展示文案与元数据。
        """
        # 定义默认的回退响应，当解析与纯文本降级均失败时使用
        fallback = {
            "reply": "我还不太确定你的需求，可以换一种简单的说法告诉我吗？",
            "intent": "general_chat",
            "conversation_route": None,
            "emotion": "talk_normal",
            "confidence": 0.0,
        }

        result = DigitalHumanService._parse_raw_json(raw_response)
        if result is None:
            result = DigitalHumanService._degrade_to_prose(raw_response)
        if result is None:
            app_logger.warning("数字人响应无法解析且无可用纯文本，使用固定兜底回复")
            result = dict(fallback)

        # 验证解析结果是否为字典类型
        if not isinstance(result, dict):
            return fallback

        # 处理回复内容，确保是有效的非空字符串
        reply = result.get("reply")
        if not isinstance(reply, str) or not reply.strip():
            reply = fallback["reply"]
        else:
            reply = DigitalHumanService._normalize_reply_text(reply)

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

    @staticmethod
    def _normalize_reply_text(reply: str) -> str:
        """把模型双重转义的常见排版符恢复为真实空白字符。"""
        reply = re.sub(r"(?<!\\)\\r\\n", "\n", reply)
        reply = re.sub(r"(?<!\\)\\n", "\n", reply)
        return re.sub(r"(?<!\\)\\t", "\t", reply)

    @staticmethod
    def _parse_raw_json(raw_response: str, log_failure: bool = True) -> Optional[Dict]:
        """清理代码围栏后依次尝试直接解析、平衡提取与修复解析。"""
        cleaned = raw_response.strip()
        cleaned = re.sub(r"^```(?:json)?\s*", "", cleaned, flags=re.IGNORECASE)  # 移除开始的代码块标记
        cleaned = re.sub(r"\s*```$", "", cleaned)  # 移除结束的代码块标记
        if not cleaned:
            if log_failure:
                app_logger.warning("数字人响应为空，无法解析JSON")
            return None
        parsed = DigitalHumanService._load_json_attempts(cleaned)
        if parsed is None and log_failure:
            app_logger.warning(
                "数字人响应不是有效JSON，原始响应头部为："
                f"{re.sub(r'\\s+', ' ', cleaned)[:200]!r}"
            )
        return parsed

    @staticmethod
    def _load_json_attempts(cleaned: str) -> Optional[Dict]:
        """直接解析 → 平衡提取 → 修复后解析；全部失败返回None。"""
        try:
            result = json.loads(cleaned)
            if isinstance(result, dict):
                return result
        except (json.JSONDecodeError, TypeError):
            pass
        candidate = DigitalHumanService._extract_json_candidate(cleaned)
        if candidate is not None:
            try:
                result = json.loads(candidate)
                if isinstance(result, dict):
                    return result
            except (json.JSONDecodeError, TypeError):
                pass
            repaired = DigitalHumanService._repair_json_text(candidate)
            if repaired != candidate:
                try:
                    result = json.loads(repaired)
                    if isinstance(result, dict):
                        return result
                except (json.JSONDecodeError, TypeError):
                    pass
        return None

    @staticmethod
    def _extract_json_candidate(text: str) -> Optional[str]:
        """提取第一个括号平衡的JSON对象；找不到或括号不平衡返回None。"""
        start = text.find("{")
        while start >= 0:
            depth = 0
            in_string = False
            escaped = False
            for index in range(start, len(text)):
                char = text[index]
                if in_string:
                    if escaped:
                        escaped = False
                    elif char == "\\":
                        escaped = True
                    elif char == '"':
                        in_string = False
                elif char == '"':
                    in_string = True
                elif char == "{":
                    depth += 1
                elif char == "}":
                    depth -= 1
                    if depth == 0:
                        return text[start:index + 1]
            start = text.find("{", start + 1)
        return None

    @staticmethod
    def _repair_json_text(candidate: str) -> str:
        """修复真实模型常见畸形：字符串内裸换行/制表符、尾逗号。"""
        parts: List[str] = []
        in_string = False
        escaped = False
        for char in candidate:
            if in_string:
                if escaped:
                    parts.append(char)
                    escaped = False
                elif char == "\\":
                    parts.append(char)
                    escaped = True
                elif char == "\n":
                    parts.append("\\n")
                elif char == "\r":
                    parts.append("\\r")
                elif char == "\t":
                    parts.append("\\t")
                else:
                    parts.append(char)
            else:
                if char == '"':
                    in_string = True
                parts.append(char)
        repaired = "".join(parts)
        return re.sub(r",\s*([}\]])", r"\1", repaired)

    @staticmethod
    def _degrade_to_prose(raw_response: str) -> Optional[Dict]:
        """解析全部失败时，把模型纯文本作为降级回复。

        只接受不含花括号的短文本；含花括号说明更可能是损坏的JSON，
        不冒险把半成品JSON展示给用户。路由仍由确定性规则重新决定。
        """
        text = re.sub(r"\s+", " ", raw_response).strip(" `\t\n\r")
        text = text.replace("**", "")
        if not (2 <= len(text) <= 800):
            return None
        if "{" in text or "}" in text:
            return None
        return {
            "reply": text,
            "intent": "general_chat",
            "conversation_route": None,
            "emotion": "talk_normal",
            "confidence": 0.0,
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

    def chat_stream(
        self,
        question: str,
        client_id: str,
        request_id: str,
        session_id: Optional[str] = None,
        custom_config: Optional[Dict[str, str]] = None,
        chunk_delay: float = DEFAULT_CHUNK_DELAY,
        voice: bool = False,
    ):
        """生成SSE增量呈现事件流。

        事件顺序固定为 accepted → thinking → delta* → completed，
        处理异常时以 error 事件收尾。生成器先完整复用 chat() 的
        解析、路由、安全校验与持久化，再对已验证 reply 分块下发；
        只呈现结果，不输出原始LLM Token，也不提供服务端取消。
        """
        question = question.strip() if isinstance(question, str) else ""
        if not question:
            raise ValueError("问题不能为空")

        session_id = session_id or f"dh_{uuid.uuid4().hex}"
        if not session_id.startswith("dh_"):
            raise ValueError("数字人会话 ID 必须以 dh_ 开头")
        if not isinstance(request_id, str) or not request_id.startswith("dhr_"):
            raise ValueError("缺少或无效的 request_id")

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

        def generate():
            yield encode_event(
                EVENT_STATUS,
                {"status": STATUS_ACCEPTED, "message": "已收到消息，正在处理"},
                request_id,
            )
            yield encode_event(
                EVENT_STATUS,
                {"status": STATUS_THINKING, "message": "正在整理回答"},
                request_id,
            )
            try:
                result = orchestrator.chat(
                    question=question,
                    client_id=client_id,
                    request_id=request_id,
                    session_id=session_id,
                    llm=llm,
                )
            except Exception as exc:
                yield encode_event(EVENT_ERROR, stream_error_data(exc), request_id)
                return
            reply = result.get("reply")
            if not isinstance(reply, str):
                reply = ""
            if voice:
                # 句级语音：文本分块下发的同时，完整句立即合成并下发 voice 事件；
                # 取消信号到达时停止继续下发（音频打断由前端播放器按 requestId 完成）。
                yield from self._stream_voice_presentation(reply, request_id, chunk_delay)
            else:
                for chunk in iter_text_chunks(reply):
                    yield encode_event(EVENT_DELTA, {"text": chunk}, request_id)
                    if chunk_delay > 0:
                        time.sleep(chunk_delay)
            yield encode_event(EVENT_COMPLETED, result, request_id)

        return generate()

    def _stream_voice_presentation(
        self,
        reply: str,
        request_id: str,
        chunk_delay: float,
    ):
        """句级语音呈现：delta 与 voice 事件交错，句子完成即合成下发。

        与纯文本呈现的事件序兼容：voice 事件只出现在 voice=true 的请求中。
        取消后不再下发任何 delta/voice 事件，以 CANCELLED 收尾。
        """
        for chunk in iter_text_chunks(reply):
            if is_cancelled(request_id):
                yield encode_event(
                    EVENT_ERROR,
                    stream_error_data(ConversationCancelled()),
                    request_id,
                )
                return
            yield encode_event(EVENT_DELTA, {"text": chunk}, request_id)
            if chunk_delay > 0:
                time.sleep(chunk_delay)
            for voice_chunk in self._voice_orchestrator.push_text(request_id, chunk):
                yield encode_voice_event(
                    {
                        "seq": voice_chunk.seq,
                        "text": voice_chunk.text,
                        "tts_mode": voice_chunk.tts_mode,
                        "audio_b64": voice_chunk.audio_b64,
                        "mime_type": voice_chunk.mime_type,
                    },
                    request_id,
                )
        for voice_chunk in self._voice_orchestrator.finish(request_id):
            yield encode_voice_event(
                {
                    "seq": voice_chunk.seq,
                    "text": voice_chunk.text,
                    "tts_mode": voice_chunk.tts_mode,
                    "audio_b64": voice_chunk.audio_b64,
                    "mime_type": voice_chunk.mime_type,
                },
                request_id,
            )

    def cancel_request(self, request_id: str, client_id: str) -> Dict:
        """幂等取消在途数字人请求；返回最新状态。

        进程标志先生效（请求行尚未创建也能拦截即将开始的执行），
        随后在会话锁内把活跃请求标记为 cancelling，由在途线程
        或分块循环轮询发现并落 cancelled 终态。
        """
        set_cancelled(request_id)
        # 取消语音流水线：丢弃该请求句缓冲并取消供应商在途合成。
        self._voice_orchestrator.cancel(request_id)
        db = SessionLocal()
        try:
            record = db.get(DigitalHumanRequest, request_id)
            if record is None:
                raise LookupError("数字人请求不存在")
            if record.client_id != client_id:
                raise PermissionError("无权取消该请求")
            session_id = record.session_id
            status = record.status
        finally:
            db.close()
        if status not in ConversationRepository.IN_FLIGHT_STATUSES:
            return {"cancelled": False, "request_id": request_id, "status": status}

        orchestrator = getattr(self, "_orchestrator", None)
        if orchestrator is None:
            orchestrator = self._build_orchestrator()
            self._orchestrator = orchestrator
        for _ in range(3):
            try:
                with orchestrator.session_lock.acquire(session_id):
                    new_status = orchestrator.repository.mark_cancelling(request_id)
                return {
                    "cancelled": new_status == "cancelling",
                    "request_id": request_id,
                    "status": new_status,
                }
            except RequestInProgress:
                # 锁只被短事务持有；短暂争抢时重试。
                time.sleep(0.05)
        return {
            "cancelled": False,
            "request_id": request_id,
            "status": status,
            "error": "该会话正在处理另一条消息，请稍后重试",
        }

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
