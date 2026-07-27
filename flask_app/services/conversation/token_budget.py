"""不依赖特定模型Tokenizer的保守会话预算。"""

import re
from typing import Dict, Iterable, List, Tuple


class TokenBudget:
    """按保守估算选择最近消息，保护高优先级上下文。"""

    def __init__(self, recent_budget: int = 2400, total_budget: int = 6000) -> None:
        self.recent_budget = recent_budget
        self.total_budget = total_budget

    @staticmethod
    def estimate(text: str) -> int:
        if not text:
            return 0
        cjk = len(re.findall(r"[\u3400-\u9fff]", text))
        remainder = max(0, len(text) - cjk)
        return max(1, cjk + (remainder + 3) // 4)

    def split_recent(
        self,
        messages: Iterable[Dict],
    ) -> Tuple[List[Dict], List[Dict]]:
        ordered = list(messages)
        selected: List[Dict] = []
        used = 0
        for item in reversed(ordered):
            tokens = int(item.get("estimated_tokens") or self.estimate(item.get("content", "")))
            if selected and used + tokens > self.recent_budget:
                break
            selected.append({**item, "estimated_tokens": tokens})
            used += tokens
        selected.reverse()
        return selected, ordered[:len(ordered) - len(selected)]
