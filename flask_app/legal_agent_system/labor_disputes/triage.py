"""青年就业劳动案件分流结果的持久化服务。接收事实 → 调规则 → 保存结果"""

from __future__ import annotations

import uuid
from typing import Dict

from core.database import SessionLocal
from legal_agent_system.models import LaborCaseTriage, MatterFactAssertion
from legal_agent_system.runtime.errors import AgentRuntimeError

from .triage_rules import LaborTriageDecisionEngine
from .triage_schemas import LaborTriageFacts
from .evidence import LaborEvidenceService


class LaborCaseTriageService:
    """保存分流事实、版本和结果，并校验 Matter 归属。"""

    def __init__(self, materials, authorities=None) -> None:
        self.materials = materials
        self.authorities = authorities
        self.engine = LaborTriageDecisionEngine()
        self.evidence = LaborEvidenceService(materials)

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
        workflow = self.get(matter_id, client_id)
        facts = workflow["facts"]
        result = dict(workflow["result"])
        fields = (
            "scenario_type", "student_status", "school_arranged", "employment_intent",
            "employer_qualified", "paid_labor", "management_control", "business_integrated",
            "agreement_type", "regular_schedule",
        )
        evidence = self.evidence.build(matter_id, client_id, facts, fields)
        authorities = []
        if self.authorities is not None and not result.get("missing_facts"):
            jurisdiction = self.materials.get_confirmed_jurisdiction(matter_id, client_id)
            authorities = self.authorities.search("CN", jurisdiction["effective_at"], ["劳动关系"])
        status = (
            "information_required" if result.get("missing_facts")
            else "authority_required" if not authorities
            else "completed"
        )
        return {
            **result,
            "status": status,
            "facts": {name: facts.get(name) for name in fields},
            "fact_refs": evidence["fact_refs"],
            "evidence_refs": evidence["evidence_refs"],
            "authority_refs": [item["authority_id"] for item in authorities],
            "evidence_conflicts": evidence["conflicts"],
        }

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
