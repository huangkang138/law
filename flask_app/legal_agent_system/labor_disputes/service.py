"""阶段 3 劳动纠纷编排服务。

使用确定性规则控制缺失事实、法域、来源验证和草稿审批；不让模型绕过安全边界。

        真正的劳动纠纷业务规则。
"""

import hashlib
import json
import uuid
from datetime import datetime, timezone
from typing import Dict, List

from core.database import SessionLocal
from models.db_models import AgentArtifact, LegalFact, LaborDisputeProfile
from legal_agent_system.models import MatterFactAssertion

from legal_agent_system.runtime.errors import AgentRuntimeError
from .schemas import FIELD_QUESTIONS, LaborDisputeFacts
from .rules import LaborRuleEngine, RULE_VERSION
from .dispute_tags import dispute_tags_from_facts
from .evidence import LaborEvidenceService
from .labor_rules import CompensationRule, OvertimePayRule, ProbationRule, TerminationRule, WageArrearsRule


def _id(prefix: str) -> str:
    return f"{prefix}_{uuid.uuid4().hex}"


class LaborDisputeService:
    """围绕一个 Matter 提供可暂停、恢复和审阅的劳动纠纷闭环。"""

    REQUIRED_FIELDS = tuple(FIELD_QUESTIONS)
    DRAFT_TEMPLATE_VERSION = "2"

    def __init__(self, materials, authorities) -> None:
        self.materials = materials
        self.authorities = authorities
        self.rules = LaborRuleEngine()
        self.evidence = LaborEvidenceService(materials)
        self.substantive_rules = {
            "wage_arrears": (WageArrearsRule(), ["劳动报酬"]),
            "probation": (ProbationRule(), ["试用期"]),
            "termination": (TerminationRule(), ["解除"]),
            "economic_compensation": (CompensationRule(), ["经济补偿"]),
            "overtime_pay": (OvertimePayRule(), ["延长工作时间"]),
        }

    def update_facts(self, matter_id: str, client_id: str, patch: Dict) -> Dict:
        """合并用户确认事实，并按当前目标动态生成下一轮追问。"""
        self.materials.get_matter(matter_id, client_id)
        db = SessionLocal()
        try:
            profile = db.get(LaborDisputeProfile, matter_id)
            current = dict(profile.facts_json or {}) if profile else {}
            current.update({key: value for key, value in patch.items() if value not in (None, "", [])})
            facts = LaborDisputeFacts.model_validate(current)
            normalized = facts.model_dump(mode="json", exclude_none=True)
            missing = [name for name in self.REQUIRED_FIELDS if not normalized.get(name)]
            plan = self._build_plan(missing)
            if profile is None:
                profile = LaborDisputeProfile(matter_id=matter_id, client_id=client_id)
                db.add(profile)
            elif profile.client_id != client_id:
                raise AgentRuntimeError("无权访问该劳动纠纷任务", "FORBIDDEN")
            changed = normalized != dict(profile.facts_json or {})
            if changed:
                profile.facts_version = int(profile.facts_version or 0) + 1
                for key, value in patch.items():
                    if value not in (None, "", []):
                        db.add(MatterFactAssertion(id=_id("factassert"), matter_id=matter_id, client_id=client_id, fact_key=key, value_json=normalized.get(key), source_type="user_input", confirmed_by_user=True, version=profile.facts_version))
            profile.facts_json = normalized
            profile.missing_facts_json = missing
            profile.plan_json = plan
            profile.status = "awaiting_information" if missing else "ready"
            profile.rule_version = RULE_VERSION
            db.commit()
            return self._snapshot(profile)
        except Exception:
            db.rollback()
            raise
        finally:
            db.close()

    def get_workflow(self, matter_id: str, client_id: str) -> Dict:
        self.materials.get_matter(matter_id, client_id)
        db = SessionLocal()
        try:
            profile = db.get(LaborDisputeProfile, matter_id)
            if profile is None:
                return self.update_facts(matter_id, client_id, {})
            if profile.client_id != client_id:
                raise AgentRuntimeError("无权访问该劳动纠纷任务", "FORBIDDEN")
            return self._snapshot(profile)
        finally:
            db.close()

    def analyze(self, matter_id: str, client_id: str) -> Dict:
        """完成期限、来源和证据校验；任一前置条件不足即暂停。"""
        jurisdiction = self.materials.get_confirmed_jurisdiction(matter_id, client_id)
        if jurisdiction["country_code"] != "CN":
            raise AgentRuntimeError("劳动纠纷闭环当前只支持中国法域", "UNSUPPORTED_JURISDICTION")
        workflow = self.get_workflow(matter_id, client_id)
        if workflow["missing_facts"]:
            return workflow
        facts = workflow["facts"]
        authorities = self._verified_authorities(jurisdiction["effective_at"])
        if not authorities:
            return {**workflow, "status": "blocked_authority", "warning": "未找到可验证且当前有效的劳动法律来源，已阻止确定性结论和文书生成。"}
        rule_decisions = [
            self.evaluate_rule(matter_id, client_id, tag)
            for tag in dispute_tags_from_facts(facts)
        ]
        blocked_rules = [item["issue_tag"] for item in rule_decisions if item["status"] == "authority_required"]
        if blocked_rules:
            return {
                **workflow,
                "status": "blocked_authority",
                "rule_decisions": rule_decisions,
                "warning": f"实体规则法源覆盖不足: {', '.join(blocked_rules)}；已阻止确定性结论和文书生成。",
            }
        missing_rule_facts = list(dict.fromkeys(
            name for item in rule_decisions for name in item.get("missing_facts", [])
        ))
        if missing_rule_facts:
            return {
                **workflow,
                "status": "awaiting_information",
                "missing_rule_facts": missing_rule_facts,
                "rule_decisions": rule_decisions,
                "warning": "实体规则关键事实仍不完整，已停止后续确定性分析。",
            }
        fact_refs = self._fact_refs(matter_id)
        deadline = self.rules.limitation(facts, authorities, fact_refs)
        checklist = self.materials.evidence_checklist(matter_id, client_id)
        return {
            **workflow, "status": "awaiting_draft_approval",
            "deadline": deadline,
            "evidence_checklist": checklist,
            "authorities": authorities,
            "rule_decisions": rule_decisions,
            "approval_prompt": "事实、期限和来源已整理。是否确认基于这些信息生成劳动仲裁申请书草稿？",
        }

    def evaluate_rule(self, matter_id: str, client_id: str, issue_tag: str) -> Dict:
        """执行单个版本化实体规则，并绑定事实、材料和当前有效法源。"""
        workflow = self.get_workflow(matter_id, client_id)
        facts = workflow["facts"]
        entry = self.substantive_rules.get(issue_tag)
        if entry is None:
            raise AgentRuntimeError(f"未注册的劳动实体规则: {issue_tag}", "INVALID_INPUT")
        rule, terms = entry
        jurisdiction = self.materials.get_confirmed_jurisdiction(matter_id, client_id)
        authorities = self.authorities.search("CN", jurisdiction["effective_at"], terms)
        evidence = self.evidence.build(matter_id, client_id, facts, rule.fields)
        return rule.evaluate(facts, evidence, authorities)

    def create_draft(self, matter_id: str, client_id: str, approved: bool) -> Dict:
        """只有用户明确确认且来源验证通过时才持久化草稿。"""
        if approved is not True:
            raise AgentRuntimeError("生成申请书草稿需要用户明确确认", "APPROVAL_REQUIRED")
        analysis = self.analyze(matter_id, client_id)
        if analysis["status"] != "awaiting_draft_approval":
            raise AgentRuntimeError("当前事实或法律来源不足，不能生成草稿", "INVALID_STATE")
        facts = analysis["facts"]
        authority_ids = list(dict.fromkeys([
            *[item["authority_id"] for item in analysis["authorities"]],
            *[
                authority_id
                for decision in analysis.get("rule_decisions", [])
                for authority_id in decision.get("authority_refs", [])
            ],
        ]))
        jurisdiction = self.materials.get_confirmed_jurisdiction(matter_id, client_id)
        draft_authorities = []
        for authority_id in authority_ids:
            verification = self.authorities.verify(
                authority_id,
                jurisdiction["effective_at"],
                jurisdiction["country_code"],
            )
            if not verification["valid"]:
                raise AgentRuntimeError("文书法源验证失败，不能生成草稿", "AUTHORITY_REQUIRED")
            draft_authorities.append(verification["authority"])
        content = self._draft_text(facts, analysis["deadline"], draft_authorities)
        fingerprint = hashlib.sha256(json.dumps({
            "facts": facts,
            "authority_ids": authority_ids,
            "rule_versions": [
                analysis["deadline"]["rule_version"],
                *[item["rule_version"] for item in analysis.get("rule_decisions", [])],
            ],
            "type": "labor_arbitration_application",
            "draft_template_version": self.DRAFT_TEMPLATE_VERSION,
        }, ensure_ascii=False, sort_keys=True).encode()).hexdigest()
        db = SessionLocal()
        try:
            existing = db.query(AgentArtifact).filter(
                AgentArtifact.matter_id == matter_id,
                AgentArtifact.client_id == client_id,
                AgentArtifact.artifact_type == "labor_arbitration_application",
                AgentArtifact.input_fingerprint == fingerprint,
            ).order_by(AgentArtifact.created_at.desc()).first()
            if existing:
                return {
                    "artifact_id": existing.id, "title": existing.title,
                    "status": existing.status, "content": existing.content,
                    "authority_refs": list(existing.authority_refs_json or []),
                    "deduplicated": True,
                }
            evidence_ids = list(dict.fromkeys([
                *analysis["deadline"]["fact_refs"],
                *[
                    ref
                    for decision in analysis.get("rule_decisions", [])
                    for ref in [
                        *decision.get("fact_refs", []),
                        *decision.get("evidence_refs", []),
                    ]
                ],
            ])) or [row.id for row in db.query(LegalFact.id).filter(LegalFact.matter_id == matter_id).all()]
            latest = db.query(AgentArtifact).filter(AgentArtifact.matter_id == matter_id, AgentArtifact.artifact_type == "labor_arbitration_application").order_by(AgentArtifact.version.desc()).first()
            artifact = AgentArtifact(
                id=_id("artifact"), matter_id=matter_id, client_id=client_id,
                artifact_type="labor_arbitration_application", title="劳动仲裁申请书（草稿）",
                content=content, status="draft", evidence_refs_json=evidence_ids,
                authority_refs_json=authority_ids, input_fingerprint=fingerprint,
                version=(latest.version + 1 if latest else 1),
            )
            db.add(artifact)
            profile = db.get(LaborDisputeProfile, matter_id)
            profile.status = "completed"
            profile.draft_approved = True
            db.commit()
            return {
                "artifact_id": artifact.id, "title": artifact.title, "status": artifact.status,
                "content": content, "authority_refs": authority_ids, "deduplicated": False,
            }
        except Exception:
            db.rollback()
            raise
        finally:
            db.close()

    @staticmethod
    def _build_plan(missing: List[str]) -> List[Dict]:
        steps = []
        if missing:
            steps.append({"name": "补充关键事实", "status": "waiting", "questions": [FIELD_QUESTIONS[name] for name in missing]})
        steps.extend([
            {"name": "核对材料与证据缺口", "status": "pending"},
            {"name": "计算关键期限", "status": "pending"},
            {"name": "检索并验证法律来源", "status": "pending"},
            {"name": "经用户确认后生成申请书草稿", "status": "pending"},
        ])
        return steps

    def _verified_authorities(self, effective_at: datetime) -> List[Dict]:
        return self.authorities.search("CN", effective_at, ["仲裁时效", "一年"])

    @staticmethod
    def _fact_refs(matter_id: str) -> List[str]:
        db = SessionLocal()
        try:
            return [row.id for row in db.query(MatterFactAssertion).filter(MatterFactAssertion.matter_id == matter_id, MatterFactAssertion.confirmed_by_user.is_(True)).all()]
        finally:
            db.close()

    @staticmethod
    def _snapshot(profile: LaborDisputeProfile) -> Dict:
        missing = list(profile.missing_facts_json or [])
        return {
            "matter_id": profile.matter_id, "status": profile.status,
            "facts": dict(profile.facts_json or {}), "missing_facts": missing,
            "questions": [FIELD_QUESTIONS[name] for name in missing],
            "plan": list(profile.plan_json or []),
            "facts_version": profile.facts_version, "rule_version": profile.rule_version,
        }

    @staticmethod
    def _draft_text(facts: Dict, deadline: Dict, authorities: List[Dict]) -> str:
        claims = "、".join(facts.get("claim_types", []))
        citations = "\n".join(f"- {item['title']} {item.get('provision') or ''}（{item['source_url']}）" for item in authorities)
        return f"""劳动仲裁申请书（草稿）

申请人：{facts['employee_name']}
被申请人：{facts['employer_name']}
工作地点：{facts['work_location']}

仲裁请求：
{facts['demands']}

事实与理由：
申请人与被申请人自 {facts['employment_start_date']} 起建立劳动关系，争议类型为{claims}。月工资基数暂按 {facts['monthly_salary']} 元记录。以上内容均待申请人结合原始证据复核。

期限提示：自 {deadline['start_date']} 起初步推算至 {deadline['estimated_deadline'] or '劳动关系终止后另行起算'}；具体以规则假设和人工复核为准。

已验证来源：
{citations}

声明：本文件仅为待审阅草稿，不代表已向仲裁机构提交，也不替代律师对事实、请求和期限的复核。
"""
