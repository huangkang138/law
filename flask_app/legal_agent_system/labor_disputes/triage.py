"""青年就业劳动案件分流结果的持久化服务。接收事实 → 调规则 → 保存结果"""

from __future__ import annotations

import uuid
from typing import Dict

from core.database import SessionLocal
from legal_agent_system.models import LaborCaseTriage, MatterFactAssertion
from legal_agent_system.runtime.errors import AgentRuntimeError

from .triage_rules import LaborTriageDecisionEngine
from .triage_schemas import LaborTriageFacts


class LaborCaseTriageService:
    """保存分流事实、版本和结果，并校验 Matter 归属。"""

    def __init__(self, materials) -> None:
        self.materials = materials
        self.engine = LaborTriageDecisionEngine()

    def update(self, matter_id: str, client_id: str, patch: Dict) -> Dict:
        self.materials.get_matter(matter_id, client_id)
        db = SessionLocal()
        try:
            row = db.get(LaborCaseTriage, matter_id)
            if row and row.client_id != client_id:
                raise AgentRuntimeError("无权访问该劳动案件分流", "FORBIDDEN")
            current = dict(row.facts_json or {}) if row else {}
            merged = {**current, **{key: value for key, value in patch.items() if value is not None}}
            facts = LaborTriageFacts.model_validate(merged)
            normalized = facts.model_dump(mode="json")
            result = self.engine.assess(facts)
            if row is None:
                row = LaborCaseTriage(
                    matter_id=matter_id, client_id=client_id,
                    facts_json={}, result_json={}, version=0,
                )
                db.add(row)
            changed = normalized != dict(row.facts_json or {})
            if changed:
                row.version = int(row.version or 0) + 1
                self._record_assertions(db, matter_id, client_id, patch, normalized, row.version)
            row.facts_json = normalized
            row.result_json = result
            db.commit()
            return self._snapshot(row)
        except Exception:
            db.rollback()
            raise
        finally:
            db.close()

    def get(self, matter_id: str, client_id: str) -> Dict:
        self.materials.get_matter(matter_id, client_id)
        db = SessionLocal()
        try:
            row = db.get(LaborCaseTriage, matter_id)
            if row is None:
                facts = LaborTriageFacts()
                return {
                    "matter_id": matter_id,
                    "facts": facts.model_dump(mode="json"),
                    "result": self.engine.assess(facts),
                    "version": 0,
                }
            if row.client_id != client_id:
                raise AgentRuntimeError("无权访问该劳动案件分流", "FORBIDDEN")
            return self._snapshot(row)
        finally:
            db.close()

    def assess(self, matter_id: str, client_id: str) -> Dict:
        return self.get(matter_id, client_id)["result"]

    @staticmethod
    def _record_assertions(db, matter_id, client_id, patch, normalized, version) -> None:
        for key, value in patch.items():
            if value is None:
                continue
            db.add(MatterFactAssertion(
                id=f"factassert_{uuid.uuid4().hex}",
                matter_id=matter_id,
                client_id=client_id,
                fact_key=f"labor_triage.{key}",
                value_json=normalized.get(key),
                source_type="user_input",
                confirmed_by_user=True,
                version=version,
            ))

    @staticmethod
    def _snapshot(row: LaborCaseTriage) -> Dict:
        return {
            "matter_id": row.matter_id,
            "facts": dict(row.facts_json or {}),
            "result": dict(row.result_json or {}),
            "version": row.version,
        }
