"""材料持久化、分片、事实定位、时间线和证据清单。"""

import hashlib
import re
import uuid
from typing import Dict, List

from core.database import SessionLocal
from models.db_models import (
    AgentDocument, DigitalHumanSession, DocumentFragment,
    LegalFact, Matter, MatterJurisdiction,
)

from legal_agent_system.runtime.errors import AgentRuntimeError


def _id(prefix: str) -> str:
    return f"{prefix}_{uuid.uuid4().hex}"


def _hash(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


class MaterialService:
    """只在已授权 Matter 内处理材料，并始终校验 client_id 归属。"""

    MAX_CHARACTERS = 200_000
    FRAGMENT_SIZE = 1_000

    def create_matter(
        self,
        client_id: str,
        goal: str,
        session_id: str | None = None,
        matter_id: str | None = None,
    ) -> Dict:
        """创建独立材料工作区，不触发阶段 1 的模拟 Runtime。"""
        goal = goal.strip() if isinstance(goal, str) else ""
        if not goal:
            raise AgentRuntimeError("案件目标不能为空", "INVALID_INPUT")
        db = SessionLocal()
        try:
            if session_id:
                session = db.get(DigitalHumanSession, session_id)
                if session is None:
                    raise AgentRuntimeError("数字人会话不存在", "SESSION_NOT_FOUND")
                if session.user_id != client_id:
                    raise AgentRuntimeError("无权关联该数字人会话", "FORBIDDEN")
            if matter_id:
                existing = db.get(Matter, matter_id)
                if existing is not None:
                    if existing.client_id != client_id or existing.session_id != session_id:
                        raise AgentRuntimeError("Matter 幂等键归属冲突", "FORBIDDEN")
                    return {
                        "matter_id": existing.id,
                        "title": existing.title,
                        "goal": existing.goal,
                        "session_id": existing.session_id,
                    }
            matter = Matter(
                id=matter_id or _id("matter"), client_id=client_id, title=goal[:60],
                goal=goal, session_id=session_id, status="active",
            )
            db.add(matter)
            db.commit()
            return {
                "matter_id": matter.id, "title": matter.title,
                "goal": matter.goal, "session_id": matter.session_id,
            }
        except Exception:
            db.rollback()
            raise
        finally:
            db.close()

    def list_matters(self, client_id: str) -> List[Dict]:
        """列出当前匿名客户端的案件工作区，供关闭面板后恢复。"""
        db = SessionLocal()
        try:
            matters = db.query(Matter).filter(
                Matter.client_id == client_id, Matter.status == "active",
            ).order_by(Matter.updated_at.desc(), Matter.created_at.desc()).all()
            return [{
                "matter_id": item.id, "title": item.title, "goal": item.goal,
                "session_id": item.session_id,
                "created_at": item.created_at.isoformat() if item.created_at else None,
                "updated_at": item.updated_at.isoformat() if item.updated_at else None,
            } for item in matters]
        finally:
            db.close()

    def get_matter(self, matter_id: str, client_id: str) -> Dict:
        """返回案件摘要和已确认法域，供前端恢复正确步骤。"""
        db = SessionLocal()
        try:
            matter = self._matter(db, matter_id, client_id)
            jurisdiction = db.query(MatterJurisdiction).filter(
                MatterJurisdiction.matter_id == matter_id,
                MatterJurisdiction.status == "confirmed",
                MatterJurisdiction.confirmed_by_user.is_(True),
            ).first()
            return {
                "matter_id": matter.id, "title": matter.title, "goal": matter.goal,
                "session_id": matter.session_id,
                "jurisdiction": None if jurisdiction is None else {
                    "country_code": jurisdiction.country_code,
                    "subdivision_code": jurisdiction.subdivision_code,
                    "language": jurisdiction.language,
                    "effective_at": jurisdiction.effective_at.isoformat(),
                    "confirmed_by_user": True,
                },
            }
        finally:
            db.close()

    def delete_matter(self, matter_id: str, client_id: str) -> None:
        """删除当前客户端所属 Matter，依靠外键级联清理材料和衍生事实。"""
        db = SessionLocal()
        try:
            matter = self._matter(db, matter_id, client_id)
            db.delete(matter)
            db.commit()
        except Exception:
            db.rollback()
            raise
        finally:
            db.close()

    def get_confirmed_jurisdiction(self, matter_id: str, client_id: str) -> Dict:
        """读取用户已确认法域；真实法律工具执行前必须调用。"""
        db = SessionLocal()
        try:
            self._matter(db, matter_id, client_id)
            jurisdiction = db.query(MatterJurisdiction).filter(
                MatterJurisdiction.matter_id == matter_id,
                MatterJurisdiction.status == "confirmed",
                MatterJurisdiction.confirmed_by_user.is_(True),
            ).first()
            if jurisdiction is None:
                raise AgentRuntimeError("请先确认案件适用法域", "JURISDICTION_CONFIRMATION_REQUIRED")
            return {"country_code": jurisdiction.country_code, "effective_at": jurisdiction.effective_at}
        finally:
            db.close()

    @staticmethod
    def _matter(db, matter_id: str, client_id: str) -> Matter:
        """读取 Matter 并执行浏览器匿名身份隔离。"""
        matter = db.get(Matter, matter_id)
        if matter is None:
            raise AgentRuntimeError("Matter 不存在", "MATTER_NOT_FOUND")
        if matter.client_id != client_id:
            raise AgentRuntimeError("无权访问该 Matter", "FORBIDDEN")
        return matter

    def ingest_text(self, matter_id: str, client_id: str, filename: str, text: str, media_type: str) -> Dict:
        """保存授权文本并按字符偏移切片，避免工具读取无关材料全文。"""
        text = text.strip() if isinstance(text, str) else ""
        if not text:
            raise AgentRuntimeError("材料内容不能为空", "INVALID_INPUT")
        if len(text) > self.MAX_CHARACTERS:
            raise AgentRuntimeError("材料超过 20 万字符限制", "MATERIAL_TOO_LARGE")

        db = SessionLocal()
        try:
            self._matter(db, matter_id, client_id)
            content_hash = _hash(text)
            existing = db.query(AgentDocument).filter(
                AgentDocument.matter_id == matter_id,
                AgentDocument.client_id == client_id,
                AgentDocument.content_hash == content_hash,
            ).first()
            if existing:
                fragment_count = db.query(DocumentFragment).filter(DocumentFragment.document_id == existing.id).count()
                return {
                    "document_id": existing.id, "filename": existing.filename,
                    "content_hash": existing.content_hash, "character_count": existing.character_count,
                    "fragment_count": fragment_count, "deduplicated": True,
                }
            document = AgentDocument(
                id=_id("doc"), matter_id=matter_id, client_id=client_id,
                filename=(filename or "未命名材料")[:255], media_type=media_type or "text/plain",
                content=text, content_hash=content_hash, character_count=len(text),
            )
            db.add(document)
            db.flush()

            fragments = []
            for sequence, start in enumerate(range(0, len(text), self.FRAGMENT_SIZE), start=1):
                content = text[start:start + self.FRAGMENT_SIZE]
                fragment = DocumentFragment(
                    id=_id("frag"), document_id=document.id, sequence=sequence,
                    start_offset=start, end_offset=start + len(content), content=content,
                    content_hash=_hash(content),
                )
                db.add(fragment)
                fragments.append(fragment)
            db.commit()
            return {
                "document_id": document.id, "filename": document.filename,
                "content_hash": document.content_hash, "character_count": len(text),
                "fragment_count": len(fragments),
            }
        except Exception:
            db.rollback()
            raise
        finally:
            db.close()

    def extract_facts(self, matter_id: str, client_id: str, document_id: str) -> List[Dict]:
        """从材料句子中提取候选事实，并保留片段及字符位置。"""
        db = SessionLocal()
        try:
            self._matter(db, matter_id, client_id)
            document = db.get(AgentDocument, document_id)
            if document is None or document.matter_id != matter_id or document.client_id != client_id:
                raise AgentRuntimeError("材料不存在或无权访问", "FORBIDDEN")

            existing_facts = db.query(LegalFact).filter(LegalFact.document_id == document_id).all()
            if existing_facts:
                fragments = {item.id: item for item in db.query(DocumentFragment).filter(DocumentFragment.document_id == document_id).all()}
                return [self._fact_dict(fact, fragments[fact.fragment_id]) for fact in existing_facts]

            # 阶段 2 使用确定性候选提取：含日期、金额或“事实：”标记的句子。
            sentence_pattern = re.compile(r"[^。！？\n]+[。！？]?|[^。！？\n]+$")
            signal_pattern = re.compile(r"事实[:：]|\d{4}[年/-]\d{1,2}|\d+(?:\.\d+)?元")
            results = []
            for match in sentence_pattern.finditer(document.content):
                sentence = match.group().strip()
                if not sentence or not signal_pattern.search(sentence):
                    continue
                fragment = (
                    db.query(DocumentFragment)
                    .filter(DocumentFragment.document_id == document.id, DocumentFragment.start_offset <= match.start(), DocumentFragment.end_offset >= match.end())
                    .first()
                )
                if fragment is None:
                    continue
                fact = LegalFact(
                    id=_id("fact"), matter_id=matter_id, document_id=document.id,
                    fragment_id=fragment.id, fact_type="material_statement", fact_text=sentence,
                    confidence=0.7, start_offset=match.start(), end_offset=match.end(),
                )
                db.add(fact)
                results.append(self._fact_dict(fact, fragment))
            db.commit()
            return results
        except Exception:
            db.rollback()
            raise
        finally:
            db.close()

    def build_timeline(self, matter_id: str, client_id: str) -> List[Dict]:
        """从已定位事实中提取日期，形成可回溯的基础时间线。"""
        db = SessionLocal()
        try:
            self._matter(db, matter_id, client_id)
            facts = db.query(LegalFact).filter(LegalFact.matter_id == matter_id).all()
            date_pattern = re.compile(r"(\d{4})[年/-](\d{1,2})[月/-]?(\d{1,2})?日?")
            timeline = []
            for fact in facts:
                match = date_pattern.search(fact.fact_text)
                if match:
                    month, day = int(match.group(2)), int(match.group(3) or 1)
                    timeline.append({"date": f"{match.group(1)}-{month:02d}-{day:02d}", "fact_id": fact.id, "event": fact.fact_text})
            return sorted(timeline, key=lambda item: item["date"])
        finally:
            db.close()

    def evidence_checklist(self, matter_id: str, client_id: str) -> Dict:
        """根据已上传材料生成已有证据与通用缺口，不作实体法律判断。"""
        db = SessionLocal()
        try:
            self._matter(db, matter_id, client_id)
            documents = db.query(AgentDocument).filter(AgentDocument.matter_id == matter_id, AgentDocument.client_id == client_id).all()
            facts = db.query(LegalFact).filter(LegalFact.matter_id == matter_id).count()
            return {
                "available": [{"document_id": item.id, "filename": item.filename} for item in documents],
                "missing": [] if documents else ["尚未上传任何材料"],
                "located_fact_count": facts,
                "warning": "清单仅反映当前已授权材料，不代表诉讼证据充分性。",
            }
        finally:
            db.close()

    @staticmethod
    def _fact_dict(fact: LegalFact, fragment: DocumentFragment) -> Dict:
        """输出事实及其最小材料引用，不向调用方传递材料全文。"""
        return {
            "fact_id": fact.id, "fact_type": fact.fact_type, "fact_text": fact.fact_text,
            "confidence": fact.confidence,
            "material_ref": {
                "document_id": fact.document_id, "fragment_id": fact.fragment_id,
                "start_offset": fact.start_offset, "end_offset": fact.end_offset,
                "page_number": fragment.page_number, "quote": fact.fact_text,
            },
        }
