"""会话层封闭数据契约。"""

from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional


@dataclass(frozen=True)
class RouterDecision:
    route: str
    confidence: float
    reason_code: str
    side_effect_authorized: bool = False

    def to_dict(self) -> Dict[str, Any]:
        return {
            "route": self.route,
            "confidence": self.confidence,
            "reason_code": self.reason_code,
            "side_effect_authorized": self.side_effect_authorized,
        }


@dataclass
class ConversationAction:
    action: str
    status: str = "completed"
    matter_id: Optional[str] = None
    run_id: Optional[str] = None
    question: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        return {
            "type": self.action,
            "status": self.status,
            "matter_id": self.matter_id,
            "run_id": self.run_id,
            "question": self.question,
        }


@dataclass
class MemorySnapshot:
    session_id: str
    revision: int = 0
    structured: Dict[str, Any] = field(default_factory=dict)
    summary_text: str = ""
    summary_items: List[Dict[str, Any]] = field(default_factory=list)
    summary_through_message_id: Optional[str] = None


@dataclass
class ContextEnvelope:
    messages: List[Dict[str, str]]
    estimated_tokens: int
    matter_id: Optional[str] = None
    run_id: Optional[str] = None
    run_status: Optional[str] = None
    memory_conflicts: List[Dict[str, Any]] = field(default_factory=list)
