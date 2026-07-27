from .agreements import default_agreement_adapters
from .communications import ChatRecordAdapter
from .employment_records import default_record_adapters


class LaborMaterialAdapterRegistry:
    """按文件名和正文信号选择一个劳动材料适配器，避免重复写入候选。"""

    def __init__(self, adapters=None) -> None:
        self.adapters = list(adapters or [*default_agreement_adapters(), *default_record_adapters(), ChatRecordAdapter()])

    def classify(self, filename: str, text: str):
        haystack = f"{filename}\n{text[:5000]}".lower()
        ranked = []
        for adapter in self.adapters:
            score = sum(1 for keyword in adapter.keywords if keyword.lower() in haystack)
            ranked.append((score, adapter.document_type, adapter))
        score, _name, adapter = max(ranked, key=lambda item: (item[0], item[1]))
        return adapter if score else None

    def extract(self, filename: str, text: str):
        adapter = self.classify(filename, text)
        if adapter is None:
            return {"document_type": "unknown", "candidates": []}
        return {"document_type": adapter.document_type, "candidates": adapter.extract(text)}
