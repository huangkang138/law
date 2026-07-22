"""从已授权材料生成劳动纠纷表单候选值。

候选值仅用于用户确认和编辑，不会自动写入 LaborDisputeProfile。
"""

import re
from typing import Dict, List, Optional, Tuple

from core.database import SessionLocal
from models.db_models import AgentDocument, LegalFact


FIELD_LABELS = {
    "employee_name": "申请人姓名",
    "employer_name": "用人单位",
    "employment_start_date": "入职日期",
    "termination_date": "解除日期",
    "limitation_start_date": "知道权利受损日期",
    "termination_reason": "解除原因",
    "monthly_salary": "月工资",
    "work_location": "实际工作地点",
    "claim_types": "争议类型",
    "demands": "具体仲裁请求",
}


class LaborFactSuggestionService:
    """使用确定性规则提取可解释候选值，避免模型无出处自动填表。"""

    DATE_PATTERN = re.compile(r"(20\d{2})[年/-](\d{1,2})[月/-](\d{1,2})日?")

    def __init__(self, materials, llm_extractor=None) -> None:
        self.materials = materials
        self.llm_extractor = llm_extractor

    def suggest(self, matter_id: str, client_id: str) -> Dict:
        self.materials.get_matter(matter_id, client_id)
        db = SessionLocal()
        try:
            documents = db.query(AgentDocument).filter(
                AgentDocument.matter_id == matter_id,
                AgentDocument.client_id == client_id,
            ).order_by(AgentDocument.created_at).all()
            facts = db.query(LegalFact).filter(
                LegalFact.matter_id == matter_id,
            ).order_by(LegalFact.created_at).all()
            fact_by_text = {fact.fact_text: fact for fact in facts}
            suggestions: Dict[str, Dict] = {}
            for document in documents:
                for sentence in self._sentences(document.content):
                    source = self._source(document.id, sentence, fact_by_text.get(sentence))
                    self._put(suggestions, "employee_name", self._employee(sentence), 0.82, source)
                    self._put(suggestions, "employer_name", self._employer(sentence), 0.82, source)
                    self._put(suggestions, "employment_start_date", self._date_near(sentence, ("入职", "建立劳动关系")), 0.9, source)
                    self._put(suggestions, "termination_date", self._termination_date(sentence), 0.9, source)
                    self._put(suggestions, "limitation_start_date", self._date_near(sentence, ("收到", "知道", "通知")), 0.78, source)
                    self._put(suggestions, "termination_reason", self._termination_reason(sentence), 0.84, source)
                    self._put(suggestions, "monthly_salary", self._salary(sentence), 0.88, source)
                    self._put(suggestions, "work_location", self._location(sentence), 0.84, source)
                    self._put(suggestions, "demands", self._demand(sentence), 0.72, source)
                    claims = self._claim_types(sentence)
                    if claims:
                        current = suggestions.get("claim_types")
                        merged = list(dict.fromkeys((current or {}).get("value", []) + claims))
                        suggestions["claim_types"] = {
                            "field": "claim_types", "label": FIELD_LABELS["claim_types"],
                            "value": merged, "confidence": 0.8,
                            "sources": list((current or {}).get("sources", [])) + [source],
                        }
                if self.llm_extractor:
                    extracted = self.llm_extractor.extract(document.content)
                    for candidate in extracted["candidates"]:
                        if candidate["field"] not in suggestions:
                            source = {"document_id": document.id, "fact_id": None, "quote": candidate["quote"], "start_offset": candidate["start_offset"], "end_offset": candidate["end_offset"]}
                            self._put(suggestions, candidate["field"], candidate["value"], candidate["confidence"], source)
            return {
                "matter_id": matter_id,
                "suggested_facts": {name: item["value"] for name, item in suggestions.items()},
                "fields": list(suggestions.values()),
                "warning": "以上内容仅是带原文定位的候选值；采用前必须由用户确认。",
            }
        finally:
            db.close()

    @staticmethod
    def _sentences(text: str) -> List[str]:
        return [item.strip() for item in re.findall(r"[^。！？\n]+[。！？]?|[^。！？\n]+$", text) if item.strip()]

    @staticmethod
    def _source(document_id: str, sentence: str, fact: Optional[LegalFact]) -> Dict:
        return {
            "document_id": document_id,
            "fact_id": fact.id if fact else None,
            "quote": sentence,
        }

    @staticmethod
    def _put(target: Dict, field: str, value, confidence: float, source: Dict) -> None:
        if value in (None, "", []):
            return
        current = target.get(field)
        if current and current["confidence"] >= confidence:
            return
        target[field] = {
            "field": field, "label": FIELD_LABELS[field], "value": value,
            "confidence": confidence, "sources": [source],
        }

    @staticmethod
    def _employee(sentence: str) -> Optional[str]:
        patterns = [
            r"(?:申请人|劳动者|员工)[：:为]?\s*([\u4e00-\u9fa5·]{2,10})",
            r"事实[：:]\s*([\u4e00-\u9fa5·]{2,10})于20\d{2}年\d{1,2}月\d{1,2}日入职",
        ]
        for pattern in patterns:
            match = re.search(pattern, sentence)
            if match:
                return match.group(1)
        return None

    @staticmethod
    def _employer(sentence: str) -> Optional[str]:
        patterns = [
            r"(?:用人单位|被申请人|公司名称)[：:为]?\s*([^，。；\n]{2,50}?(?:公司|中心|事务所|单位))",
            r"入职\s*([^，。；\n]{2,50}?(?:公司|中心|事务所|单位))",
        ]
        for pattern in patterns:
            match = re.search(pattern, sentence)
            if match:
                return match.group(1).strip()
        return None

    def _date_near(self, sentence: str, keywords: Tuple[str, ...]) -> Optional[str]:
        if not any(keyword in sentence for keyword in keywords):
            return None
        match = self.DATE_PATTERN.search(sentence)
        if not match:
            return None
        return f"{int(match.group(1)):04d}-{int(match.group(2)):02d}-{int(match.group(3)):02d}"

    @staticmethod
    def _termination_date(sentence: str) -> Optional[str]:
        patterns = (
            r"劳动关系于\s*(20\d{2})[年/-](\d{1,2})[月/-](\d{1,2})日?\s*(?:解除|终止)",
            r"(20\d{2})[年/-](\d{1,2})[月/-](\d{1,2})日?\s*(?:解除|终止)(?:劳动关系|劳动合同)?",
        )
        for pattern in patterns:
            match = re.search(pattern, sentence)
            if match:
                return f"{int(match.group(1)):04d}-{int(match.group(2)):02d}-{int(match.group(3)):02d}"
        return None

    @staticmethod
    def _termination_reason(sentence: str) -> Optional[str]:
        match = re.search(
            r"(?:解除)?理由(?:为|是|[：:])\s*[“\"']?([^”\"'，。；\n]+)",
            sentence,
        )
        return match.group(1).strip() if match else None

    @staticmethod
    def _salary(sentence: str) -> Optional[float]:
        match = re.search(r"(?:平均月工资|月工资|工资基数)[^\d]{0,12}(\d+(?:\.\d+)?)元", sentence)
        return float(match.group(1)) if match else None

    @staticmethod
    def _location(sentence: str) -> Optional[str]:
        match = re.search(r"(?:实际工作地点|工作地点)[为：:]?\s*([^，。；\n]+)", sentence)
        return match.group(1).strip() if match else None

    @staticmethod
    def _claim_types(sentence: str) -> List[str]:
        mapping = {
            "欠薪": ("欠薪", "拖欠工资", "尚未支付"),
            "违法解除": ("违法解除", "不同意公司所述解除理由"),
            "经济补偿": ("经济补偿",),
            "赔偿金": ("赔偿金",),
            "加班费": ("加班费", "加班工资"),
        }
        return [label for label, keywords in mapping.items() if any(keyword in sentence for keyword in keywords)]

    @staticmethod
    def _demand(sentence: str) -> Optional[str]:
        if any(keyword in sentence for keyword in ("仲裁请求", "请求支付", "拟通过劳动仲裁主张", "主张")):
            return sentence.removeprefix("事实：").removeprefix("事实:").strip("。")
        return None
