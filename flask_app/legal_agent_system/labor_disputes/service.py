"""阶段 3 劳动纠纷编排服务。

使用确定性规则控制缺失事实、法域、来源验证和草稿审批；不让模型绕过安全边界。
"""

import uuid
from datetime import datetime, timedelta, timezone
from typing import Dict, List

from core.database import SessionLocal
from models.db_models import AgentArtifact, LegalAuthority, LegalFact, LaborDisputeProfile

from legal_agent_system.runtime.errors import AgentRuntimeError
from .schemas import FIELD_QUESTIONS, LaborDisputeFacts


def _id(prefix: str) -> str:
    return f"{prefix}_{uuid.uuid4().hex}"


class LaborDisputeService:
    """围绕一个 Matter 提供可暂停、恢复和审阅的劳动纠纷闭环。"""

    REQUIRED_FIELDS = tuple(FIELD_QUESTIONS)

    def __init__(self, materials, authorities) -> None:
        self.materials = materials
        self.authorities = authorities

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
            profile.facts_json = normalized
            profile.missing_facts_json = missing
            profile.plan_json = plan
            profile.status = "awaiting_information" if missing else "ready"
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
        start = datetime.fromisoformat(facts["limitation_start_date"]).date()
        deadline = start + timedelta(days=365)
        checklist = self.materials.evidence_checklist(matter_id, client_id)
        return {
            **workflow, "status": "awaiting_draft_approval",
            "deadline": {"start_date": start.isoformat(), "estimated_deadline": deadline.isoformat(), "assumption": "按已验证来源所示的一年期间作初步日期推算；中止、中断等情形需人工复核。"},
            "evidence_checklist": checklist,
            "authorities": authorities,
            "approval_prompt": "事实、期限和来源已整理。是否确认基于这些信息生成劳动仲裁申请书草稿？",
        }

    def create_draft(self, matter_id: str, client_id: str, approved: bool) -> Dict:
        """只有用户明确确认且来源验证通过时才持久化草稿。"""
        if approved is not True:
            raise AgentRuntimeError("生成申请书草稿需要用户明确确认", "APPROVAL_REQUIRED")
        analysis = self.analyze(matter_id, client_id)
        if analysis["status"] != "awaiting_draft_approval":
            raise AgentRuntimeError("当前事实或法律来源不足，不能生成草稿", "INVALID_STATE")
        facts = analysis["facts"]
        authority_ids = [item["authority_id"] for item in analysis["authorities"]]
        content = self._draft_text(facts, analysis["deadline"], analysis["authorities"])
        db = SessionLocal()
        try:
            evidence_ids = [row.id for row in db.query(LegalFact.id).filter(LegalFact.matter_id == matter_id).all()]
            artifact = AgentArtifact(
                id=_id("artifact"), matter_id=matter_id, client_id=client_id,
                artifact_type="labor_arbitration_application", title="劳动仲裁申请书（草稿）",
                content=content, status="draft", evidence_refs_json=evidence_ids,
                authority_refs_json=authority_ids,
            )
            db.add(artifact)
            profile = db.get(LaborDisputeProfile, matter_id)
            profile.status = "completed"
            profile.draft_approved = True
            db.commit()
            return {"artifact_id": artifact.id, "title": artifact.title, "status": artifact.status, "content": content, "authority_refs": authority_ids}
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
        db = SessionLocal()
        try:
            rows = db.query(LegalAuthority).filter(LegalAuthority.country_code == "CN").order_by(LegalAuthority.retrieved_at.desc()).all()
            verified = []
            for row in rows:
                text = f"{row.title} {row.provision or ''} {row.text}"
                # 当前期限工具只实现“一年”规则，因此来源必须同时明确主题和期间。
                if "仲裁时效" not in text or "一年" not in text:
                    continue
                result = self.authorities.verify(row.id, effective_at, "CN")
                if result["valid"]:
                    verified.append({"authority_id": row.id, "title": row.title, "provision": row.provision, "source_url": row.source_url})
            return verified
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

期限提示：自 {deadline['start_date']} 起初步推算至 {deadline['estimated_deadline']}；该日期不考虑中止、中断等特殊情形。

已验证来源：
{citations}

声明：本文件仅为待审阅草稿，不代表已向仲裁机构提交，也不替代律师对事实、请求和期限的复核。
"""
