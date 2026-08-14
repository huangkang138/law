"""结构化会话记忆与双层Rolling Summary。"""

import re
import uuid
from datetime import datetime, timezone
from typing import Dict, Iterable, List, Optional, Tuple

from .schemas import MemorySnapshot
from .token_budget import TokenBudget


LABOR_TERMS = (
    "劳动", "工资", "薪资", "欠薪", "加班", "辞退", "解雇", "离职",
    "入职", "试用期", "实习", "兼职", "社保", "工伤", "劳动合同",
)


class ConversationMemoryManager:
    """只从用户输入提取候选记忆，保留来源和替代关系。"""

    def __init__(self, token_budget: Optional[TokenBudget] = None) -> None:
        self.token_budget = token_budget or TokenBudget()

    # snapshot             # 旧记忆
    # question             # 当前用户输入
    # source_message_id    # 当前消息ID
    # history              # 历史原始消息
    # matter_id            # 当前关联案件
    def update(
        self,
        snapshot: MemorySnapshot,
        question: str,
        source_message_id: str,
        history: Iterable[Dict],
        matter_id: Optional[str] = None,
    ) -> MemorySnapshot:
        structured = dict(snapshot.structured or {})
        structured.setdefault("user_goals", [])
        structured.setdefault("user_claims", [])
        structured.setdefault("confirmed_decisions", [])
        structured.setdefault("open_questions", [])
        structured["current_topic"] = (
            "cn_labor" if any(term in question for term in LABOR_TERMS)
            else structured.get("current_topic", "general")
        )
        if matter_id:
            structured["matter_id"] = matter_id
            structured["conversation_stage"] = "matter"
        else:
            structured.setdefault("conversation_stage", "initial_chat")
        items = [dict(item) for item in snapshot.summary_items]
        if (
            not structured["user_goals"]
            or re.search(r"我想|我要|请帮我|我的目标", question)
        ):
            goal_text = self._goal_text(question)
            items, goal_item = self._replace_item(
                items,
                "primary_goal",
                goal_text,
                "goal",
                source_message_id,
            )
            structured["user_goals"] = [{
                "text": goal_text,
                "source_message_id": source_message_id,
                "status": "active",
                "summary_item_id": goal_item["item_id"],
            }]
        extracted = self._extract_items(question)
        active_salary = next((#寻找当前有效工资
            item for item in items
            if item.get("subject") == "monthly_salary"
            and item.get("status") == "active"
        ), None)
        correction = re.search(
            r"不是\s*\d{3,8}(?:\.\d+)?\s*[，,、]?\s*是\s*(\d{3,8}(?:\.\d+)?)",
            question,
        )
        if active_salary and correction and not any(
            item[0] == "monthly_salary" for item in extracted
        ):
            extracted.append(("monthly_salary", float(correction.group(1)), "fact"))
        for subject, value, item_type in extracted:
            items, new_item = self._replace_item(
                items, subject, value, item_type, source_message_id,
            )
            if item_type == "fact":
                claims = [
                    item for item in structured["user_claims"]
                    if item.get("subject") != subject or item.get("status") != "active"
                ]
                claims.append({
                    "subject": subject,
                    "value": value,
                    "source_message_id": source_message_id,
                    "status": "active",
                    "summary_item_id": new_item["item_id"],
                })
                structured["user_claims"] = claims

        all_messages = list(history)
        _recent, older = self.token_budget.split_recent(all_messages)
        through = snapshot.summary_through_message_id
        if older:
            through = older[-1].get("id")
        summary_text = self._render_summary(structured, items, older)
        return MemorySnapshot(
            session_id=snapshot.session_id,
            revision=snapshot.revision + 1,
            structured=structured,
            summary_text=summary_text,
            summary_items=items,
            summary_through_message_id=through,
        )

    @staticmethod
    def _goal_text(question: str) -> str:
        """目标只保存非事实语义，金额、日期等必须进入可治理fact条目。"""
        if any(term in question for term in LABOR_TERMS):
            if re.search(r"仲裁|维权|帮我处理|建立案件|开始分析", question):
                return "处理当前劳动争议"
            return "咨询劳动用工问题"
        return re.sub(r"\d+(?:\.\d+)?", "[数值]", question[:300])

    @staticmethod
    def _extract_items(question: str) -> List[Tuple[str, object, str]]:
        results: List[Tuple[str, object, str]] = []
        salary = re.search(
            r"(?:月工资|工资|月薪|薪资)[^\d]{0,10}(\d{3,8}(?:\.\d+)?)",
            question,
        )
        if salary:
            results.append(("monthly_salary", float(salary.group(1)), "fact"))
        arrears = re.search(r"(?:拖欠|欠了?)([一二三四五六七八九十\d]+)个?月", question)
        if arrears:
            results.append(("arrears_months", arrears.group(1), "fact"))
        if "已经离职" in question or "已离职" in question:
            results.append(("employment_status", "left", "fact"))
        elif "还在职" in question or "仍在职" in question:
            results.append(("employment_status", "employed", "fact"))
        return results

    @staticmethod
    def _replace_item(
        items: List[Dict],
        subject: str,
        value: object,
        item_type: str,
        source_message_id: str,
    ) -> Tuple[List[Dict], Dict]:
        now = datetime.now(timezone.utc).isoformat()
        previous_id = None
        for item in items:
            if item.get("subject") == subject and item.get("status") == "active":
                if item.get("value") == value:
                    sources = list(item.get("source_message_ids") or [])
                    if source_message_id not in sources:
                        sources.append(source_message_id)
                    item["source_message_ids"] = sources
                    item["updated_at"] = now
                    return items, item
                item["status"] = "superseded"
                item["updated_at"] = now
                previous_id = item.get("item_id")
        new_item = {
            "item_id": f"summary_{uuid.uuid4().hex}",
            "item_type": item_type,
            "subject": subject,
            "value": value,
            "source_message_ids": [source_message_id],
            "status": "active",
            "supersedes_item_id": previous_id,
            "updated_at": now,
        }
        items.append(new_item)
        return items, new_item

    @staticmethod
    def _render_summary(
        structured: Dict,
        items: List[Dict],
        older: List[Dict],
    ) -> str:
        labels = {
            "primary_goal": "用户当前目标",
            "monthly_salary": "用户陈述月工资",
            "arrears_months": "用户陈述欠薪月数",
            "employment_status": "用户陈述就业状态",
        }
        lines = []
        topic = structured.get("current_topic")
        if topic:
            lines.append(f"当前主题：{topic}")
        for item in items:
            if item.get("status") != "active":
                continue
            label = labels.get(item.get("subject"), item.get("subject"))
            lines.append(f"{label}：{item.get('value')}")
        if older:
            user_count = sum(1 for item in older if item.get("role") == "user")
            lines.append(f"已压缩较早对话：{user_count}轮用户陈述。")
        return "\n".join(lines)
