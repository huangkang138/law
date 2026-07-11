"""数字人智能助手服务。"""

import json
import re
import uuid
from typing import Dict, List, Optional

from langchain_core.messages import AIMessage, HumanMessage, SystemMessage

from core.logger import app_logger
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
        self.sessions: Dict[str, List[Dict[str, str]]] = {}
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

    def _get_session_history(self, session_id: str) -> List[Dict[str, str]]:
        return self.sessions.setdefault(session_id, [])

    def _build_messages(self, session_id: str, question: str) -> List:
        messages = [SystemMessage(content=self.system_prompt)]
        for message in self._get_session_history(session_id)[-6:]:
            if message["role"] == "user":
                messages.append(HumanMessage(content=message["content"]))
            elif message["role"] == "assistant":
                messages.append(AIMessage(content=message["content"]))
        messages.append(HumanMessage(content=question))
        return messages

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

        messages = self._build_messages(session_id, question)
        raw_response = self._invoke_llm_streaming(messages, llm)
        parsed = self._parse_llm_response(raw_response)

        history = self._get_session_history(session_id)
        history.append({"role": "user", "content": question})
        history.append({"role": "assistant", "content": parsed["reply"]})

        route_info = INTENT_ROUTE_MAP[parsed["intent"]]
        should_route = parsed["confidence"] >= MIN_ROUTE_CONFIDENCE

        return {
            **parsed,
            "route": route_info["route"] if should_route else None,
            "route_label": route_info["route_label"] if should_route else None,
            "session_id": session_id,
        }

    def reset_session(self, session_id: str) -> bool:
        self.sessions.pop(session_id, None)
        app_logger.info(f"数字人会话已重置 [session={session_id}]")
        return True


digital_human_service: Optional[DigitalHumanService] = None


def get_digital_human_service() -> DigitalHumanService:
    global digital_human_service
    if digital_human_service is None:
        digital_human_service = DigitalHumanService()
    return digital_human_service
