"""把劳动规则要件连接到用户确认事实和材料原文位置。"""

from collections import defaultdict
from typing import Any, Iterable

from core.database import SessionLocal
from legal_agent_system.models import MatterFactAssertion
from models.db_models import AgentDocument, DocumentFragment

from .material_adapters import LaborMaterialAdapterRegistry
from .schemas import LaborEvidenceItem


class LaborEvidenceService:
    def __init__(self, materials, adapters: LaborMaterialAdapterRegistry | None = None) -> None:
        self.materials = materials
        self.adapters = adapters or LaborMaterialAdapterRegistry()

    def build(self, matter_id: str, client_id: str, facts: dict, fields: Iterable[str]) -> dict:
        self.materials.get_matter(matter_id, client_id)
        db = SessionLocal()
        try:
            assertions = db.query(MatterFactAssertion).filter(
                MatterFactAssertion.matter_id == matter_id,
                MatterFactAssertion.client_id == client_id,
                MatterFactAssertion.confirmed_by_user.is_(True),
            ).order_by(MatterFactAssertion.version.desc()).all()
            latest_assertion = {}
            for row in assertions:
                latest_assertion.setdefault(row.fact_key, row)
                if row.fact_key.startswith("labor_triage."):
                    latest_assertion.setdefault(row.fact_key.removeprefix("labor_triage."), row)

            documents = db.query(AgentDocument).filter(
                AgentDocument.matter_id == matter_id,
                AgentDocument.client_id == client_id,
            ).order_by(AgentDocument.created_at).all()
            fragments = {
                row.id: db.query(DocumentFragment).filter(
                    DocumentFragment.document_id == row.id,
                ).order_by(DocumentFragment.sequence).all()
                for row in documents
            }
            candidates = defaultdict(list)
            document_types = {}
            for document in documents:
                extracted = self.adapters.extract(document.filename, document.content)
                document_types[document.id] = extracted["document_type"]
                for item in extracted["candidates"]:
                    fragment = self._fragment_for(fragments.get(document.id, []), item.start_offset, item.end_offset)
                    candidates[item.field].append({
                        "value": item.value,
                        "document_id": document.id,
                        "fragment_id": fragment.id if fragment else None,
                        "start_offset": item.start_offset,
                        "end_offset": item.end_offset,
                        "page_number": fragment.page_number if fragment else None,
                        "quote": item.quote,
                        "document_type": item.document_type,
                        "confidence": item.confidence,
                    })

            matrix = []
            for field in fields:
                value = facts.get(field)
                refs = candidates.get(field, [])
                assertion = latest_assertion.get(field)
                matching = [ref for ref in refs if self._same(ref["value"], value)]
                conflicting = self._unique([ref["value"] for ref in refs if not self._same(ref["value"], value)])
                if value in (None, "", []):
                    status = "missing"
                elif conflicting:
                    status = "conflict"
                elif matching:
                    status = "supported"
                else:
                    status = "user_confirmed_only"
                matrix.append(LaborEvidenceItem(
                    field=field,
                    value=value,
                    status=status,
                    fact_refs=[assertion.id] if assertion else [],
                    evidence_refs=[ref["fragment_id"] for ref in matching if ref["fragment_id"]],
                    material_refs=matching,
                    conflicting_values=conflicting,
                ).model_dump(mode="json"))
            return {
                "items": matrix,
                "fact_refs": self._unique([ref for item in matrix for ref in item["fact_refs"]]),
                "evidence_refs": self._unique([ref for item in matrix for ref in item["evidence_refs"]]),
                "document_types": document_types,
                "conflicts": [item["field"] for item in matrix if item["status"] == "conflict"],
                "unsupported": [item["field"] for item in matrix if item["status"] == "user_confirmed_only"],
            }
        finally:
            db.close()

    @staticmethod
    def _fragment_for(fragments, start: int, end: int):
        return next((item for item in fragments if item.start_offset <= start and item.end_offset >= end), None)

    @staticmethod
    def _same(left: Any, right: Any) -> bool:
        if left is None or right is None:
            return left is right
        try:
            return float(left) == float(right)
        except (TypeError, ValueError):
            return str(left).strip() == str(right).strip()

    @staticmethod
    def _unique(values):
        result = []
        for value in values:
            if value not in result:
                result.append(value)
        return result
