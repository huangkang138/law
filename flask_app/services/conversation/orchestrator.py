"""一次会话请求的唯一编排入口。"""

import uuid
from dataclasses import asdict
from typing import Dict

from langchain_core.messages import AIMessage, HumanMessage, SystemMessage

from .actions import ConversationActions
from .cancel import (
    ConversationCancelled,
    arm,
    disarm,
    is_cancelled,
)
from .context_builder import ConversationContextBuilder
from .locks import ConversationSessionLock
from .memory import ConversationMemoryManager
from .repository import ConversationRepository
from .router import ConversationRouter
from .tracing import trace
from .schemas import (
    ContextEnvelope,
    ConversationAction,
    MemorySnapshot,
    RouterDecision,
)
from .workspace import get_conversation_workspace_service


class ConversationOrchestrator:
    def __init__(
        self,
        llm,
        system_prompt: str,
        invoke_llm,
        parse_llm_response,
        route_map: Dict,
        min_route_confidence: float,
    ) -> None:
        self.llm = llm
        self.system_prompt = system_prompt
        self.invoke_llm = invoke_llm
        self.parse_llm_response = parse_llm_response
        self.route_map = route_map
        self.min_route_confidence = min_route_confidence
        self.repository = ConversationRepository()
        self.memory = ConversationMemoryManager(self.repository.token_budget)
        self.context_builder = ConversationContextBuilder(
            self.repository, self.repository.token_budget,
        )
        self.router = ConversationRouter()
        self.actions = ConversationActions()
        self.session_lock = ConversationSessionLock()

    def chat(
        self,
        question: str,
        client_id: str,
        request_id: str,
        session_id: str | None = None,
        llm=None,
    ) -> Dict:
        session_id = session_id or f"dh_{uuid.uuid4().hex}"
        lease_token = None
        arm(request_id)
        try:
            if is_cancelled(request_id):
                # 取消先于请求行创建到达：不建行、不持久化用户消息，直接结束。
                raise ConversationCancelled()
            with self.session_lock.acquire(session_id):
                cached, user_message_id, lease_token = self.repository.begin_request(
                    request_id, client_id, session_id, question,
                )
                initial_workspace_version = (
                    get_conversation_workspace_service().get_version(
                        session_id,
                        client_id,
                    )
                )
            if cached is not None:
                # 已完成请求的取消是 no-op：优先返回既有缓存。
                trace("request_replayed", request_id, session_id=session_id)
                return cached
            if is_cancelled(request_id, poll_db=True):
                # begin_request 执行期间到达的取消（含跨 worker 的 cancelling）。
                raise ConversationCancelled()
            return self._chat_locked(
                question,
                client_id,
                request_id,
                session_id,
                user_message_id,
                lease_token,
                initial_workspace_version,
                llm,
            )
        except Exception as exc:
            if lease_token:
                try:
                    with self.session_lock.acquire(session_id):
                        if isinstance(exc, ConversationCancelled) or is_cancelled(
                            request_id, poll_db=True,
                        ):
                            self.repository.mark_cancelled(request_id, lease_token)
                            trace("request_cancelled", request_id)
                        else:
                            self.repository.mark_retryable(request_id, lease_token)
                            trace("request_failed", request_id, error=type(exc).__name__)
                except Exception:
                    pass
            raise
        finally:
            disarm(request_id)

    def _chat_locked(
        self,
        question: str,
        client_id: str,
        request_id: str,
        session_id: str,
        user_message_id: str,
        lease_token: str,
        initial_workspace_version: int,
        llm=None,
    ) -> Dict:
        request_state = self.repository.load_request_checkpoint(request_id)
        if request_state["status"] == "action_completed":
            checkpoint = request_state["checkpoint"]
            parsed = dict(checkpoint["parsed"])
            result = dict(checkpoint["result"])
            memory = MemorySnapshot(**checkpoint["memory"])
            self._ensure_not_cancelled(request_id, session_id, lease_token)
            with self.session_lock.acquire(session_id):
                self.repository.complete_request(
                    request_id,
                    session_id,
                    parsed,
                    result,
                    memory,
                    lease_token,
                )
            return result

        if request_state["status"] == "action_running":
            checkpoint = request_state["checkpoint"]
            return self._execute_recoverable_action(
                request_id=request_id,
                session_id=session_id,
                client_id=client_id,
                question=checkpoint["question"],
                parsed=dict(checkpoint["parsed"]),
                decision=RouterDecision(**checkpoint["decision"]),
                memory=MemorySnapshot(**checkpoint["memory"]),
                context=ContextEnvelope(**checkpoint["context"]),
                resources=dict(request_state["resources"]),
                lease_token=lease_token,
                recovering=True,
                expected_workspace_version=checkpoint.get(
                    "workspace_version"
                ),
            )

        previous = self.repository.load_memory(session_id)
        prior_context = self.repository.matter_context(session_id, client_id)
        history = self.repository.messages(session_id, client_id)
        memory = self.memory.update(
            previous,
            question,
            user_message_id,
            history,
            prior_context.get("matter_id"),
        )
        context = self.context_builder.build(
            session_id,
            client_id,
            question,
            self.system_prompt,
            memory,
            request_id,
        )
        decision = self.router.route(question, context)
        if decision.route == "high_risk_handoff":
            parsed = {
                "reply": "这可能涉及人身安全或其他高风险情况。请先确保安全，并尽快联系当地有权限的专业人员处理。",
                "intent": "general_chat",
                "emotion": "serious",
                "confidence": 1.0,
            }
        else:
            raw = self.invoke_llm(
                self._to_langchain_messages(context.messages),
                llm or self.llm,
                request_id=request_id,
            )
            parsed = self.parse_llm_response(raw)
            decision = self.router.route(question, context, parsed)

        trace(
            "route_decision",
            request_id,
            route=decision.route,
            confidence=decision.confidence,
            reason_code=decision.reason_code,
            side_effect_authorized=decision.side_effect_authorized,
        )

        if decision.side_effect_authorized:
            resources = {
                "matter_id": f"matter_{uuid.uuid4().hex}",
                "run_id": f"run_{uuid.uuid4().hex}",
            }
            checkpoint = {
                "question": question,
                "parsed": dict(parsed),
                "decision": decision.to_dict(),
                "memory": asdict(memory),
                "context": self._checkpoint_context(context),
                "workspace_version": initial_workspace_version,
            }
            self._ensure_not_cancelled(request_id, session_id, lease_token)
            with self.session_lock.acquire(session_id):
                self.repository.mark_action_started(
                    request_id,
                    lease_token,
                    decision.route,
                    resources,
                    checkpoint,
                )
            return self._execute_recoverable_action(
                request_id=request_id,
                session_id=session_id,
                client_id=client_id,
                question=question,
                parsed=parsed,
                decision=decision,
                memory=memory,
                context=context,
                resources=resources,
                lease_token=lease_token,
                recovering=False,
                expected_workspace_version=initial_workspace_version,
            )

        action = self.actions.execute(
            decision, question, client_id, session_id, context,
            request_id=request_id,
        )
        trace(
            "action_executed",
            request_id,
            action_type=action.action,
            status=action.status,
            matter_id=action.matter_id,
            run_id=action.run_id,
        )
        result = self._build_result(
            parsed, action, decision, context, session_id,
        )
        self._ensure_not_cancelled(request_id, session_id, lease_token)
        with self.session_lock.acquire(session_id):
            self.repository.complete_request(
                request_id,
                session_id,
                parsed,
                result,
                memory,
                lease_token,
            )
        trace("request_completed", request_id, action_type=action.action)
        return result

    def _ensure_not_cancelled(
        self,
        request_id: str,
        session_id: str,
        lease_token: str,
    ) -> None:
        """已完成持久化前的取消检查；命中则落 cancelled 终态并抛出。"""
        if not is_cancelled(request_id, poll_db=True):
            return
        with self.session_lock.acquire(session_id):
            self.repository.mark_cancelled(request_id, lease_token)
        raise ConversationCancelled()

    def _execute_recoverable_action(
        self,
        request_id: str,
        session_id: str,
        client_id: str,
        question: str,
        parsed: Dict,
        decision: RouterDecision,
        memory: MemorySnapshot,
        context: ContextEnvelope,
        resources: Dict,
        lease_token: str,
        recovering: bool,
        expected_workspace_version: int | None,
    ) -> Dict:
        def checkpoint_resource(**changes) -> None:
            with self.session_lock.acquire(session_id):
                self.repository.update_action_resource(
                    request_id,
                    lease_token,
                    **changes,
                )
            resources.update({
                key: value for key, value in changes.items()
                if value is not None
            })

        self._ensure_not_cancelled(request_id, session_id, lease_token)
        action = self.actions.execute(
            decision,
            question,
            client_id,
            session_id,
            context,
            resources=resources,
            checkpoint_resource=checkpoint_resource,
            recovering=recovering,
            expected_workspace_version=expected_workspace_version,
            request_id=request_id,
        )
        trace(
            "action_executed",
            request_id,
            action_type=action.action,
            status=action.status,
            matter_id=action.matter_id,
            run_id=action.run_id,
            recovering=recovering,
        )
        if action.matter_id:
            memory.structured["matter_id"] = action.matter_id
            memory.structured["conversation_stage"] = "matter"
        result = self._build_result(
            parsed, action, decision, context, session_id,
        )
        completed_checkpoint = {
            "question": question,
            "parsed": dict(parsed),
            "decision": decision.to_dict(),
            "memory": asdict(memory),
            "context": self._checkpoint_context(context),
            "workspace_version": expected_workspace_version,
            "result": result,
        }
        self._ensure_not_cancelled(request_id, session_id, lease_token)
        with self.session_lock.acquire(session_id):
            self.repository.mark_action_completed(
                request_id,
                lease_token,
                resources,
                completed_checkpoint,
            )
        # 动作完成到请求完成之间是取消竞态窗口：
        # mark_cancelling 允许从 action_completed 转 cancelling，
        # 若取消恰好落在这里必须拒绝把结果写成 completed。
        # complete_request 内部的允许状态校验是同一竞态的第二道防线。
        self._ensure_not_cancelled(request_id, session_id, lease_token)
        with self.session_lock.acquire(session_id):
            self.repository.complete_request(
                request_id,
                session_id,
                parsed,
                result,
                memory,
                lease_token,
            )
        trace(
            "request_completed",
            request_id,
            action_type=action.action,
            recovering=recovering,
        )
        return result

    def _build_result(
        self,
        parsed: Dict,
        action: ConversationAction,
        decision: RouterDecision,
        context: ContextEnvelope,
        session_id: str,
    ) -> Dict:
        parsed["reply"] = self._present_action(parsed["reply"], action)
        route_info = self.route_map.get(parsed["intent"], {})
        should_route = parsed["confidence"] >= self.min_route_confidence
        return {
            **parsed,
            "route": route_info.get("route") if should_route else None,
            "route_label": route_info.get("route_label") if should_route else None,
            "session_id": session_id,
            "decision": decision.to_dict(),
            "action": action.to_dict(),
            "context": {
                "matter_id": action.matter_id or context.matter_id,
                "run_id": action.run_id or context.run_id,
                "run_status": action.status if action.run_id else context.run_status,
                "input_tokens_estimated": context.estimated_tokens,
            },
        }

    @staticmethod
    def _checkpoint_context(context: ContextEnvelope) -> Dict:
        return {
            "messages": [],
            "estimated_tokens": context.estimated_tokens,
            "matter_id": context.matter_id,
            "run_id": context.run_id,
            "run_status": context.run_status,
            "memory_conflicts": list(context.memory_conflicts),
        }

    @staticmethod
    def _to_langchain_messages(messages):
        result = []
        for item in messages:
            if item["role"] == "system":
                result.append(SystemMessage(content=item["content"]))
            elif item["role"] == "assistant":
                result.append(AIMessage(content=item["content"]))
            else:
                result.append(HumanMessage(content=item["content"]))
        return result

    @staticmethod
    def _present_action(reply: str, action: ConversationAction) -> str:
        if action.action == "ask_one_key_question":
            return f"我已为你建立案件工作区。{action.question}"
        if action.action == "start_agent":
            return "案件分流已完成，我已按受控流程开始分析。你可以在案件工作台查看进度。"
        if action.action == "guide_to_workspace":
            return action.question or "这一步需要结合案件中的事实、材料或任务状态，请到案件工作台继续。"
        if action.action == "stop_for_risk":
            return reply
        return reply
