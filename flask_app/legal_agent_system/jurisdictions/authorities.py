"""法律来源登记与引用有效性校验。"""

import hashlib
import uuid
from datetime import datetime, timezone
from typing import Dict, Optional

from core.database import SessionLocal
from models.db_models import LegalAuthority

from legal_agent_system.runtime.errors import AgentRuntimeError
from .registry import get_jurisdiction_registry


class LegalAuthorityService:
    """保存可追溯来源；不负责联网检索，也不把未知来源包装为有效法律。"""

    VALID_STATUSES = {"effective", "repealed", "amended", "unknown"}

    def register(self, data: Dict) -> Dict:
        """登记外部适配器提供的来源元数据和内容哈希。"""
        country_code = str(data.get("country_code", "")).upper()
        package = get_jurisdiction_registry().get(country_code)
        authority_type = data.get("authority_type")
        if authority_type not in package.authority_types:
            raise AgentRuntimeError("该法域不支持此来源类型", "AUTHORITY_TYPE_UNSUPPORTED")
        status = data.get("status", "unknown")
        if status not in self.VALID_STATUSES:
            raise AgentRuntimeError("无效的法律来源状态", "INVALID_INPUT")
        required = ["title", "text", "source_url", "issuing_body"]
        if any(not str(data.get(key, "")).strip() for key in required):
            raise AgentRuntimeError("法律来源缺少必要字段", "INVALID_INPUT")

        text = data["text"].strip()
        db = SessionLocal()
        try:
            authority = LegalAuthority(
                id=f"authority_{uuid.uuid4().hex}", country_code=country_code,
                subdivision_code=data.get("subdivision_code"), authority_type=authority_type,
                title=data["title"].strip(), provision=data.get("provision"), text=text,
                source_url=data["source_url"].strip(), issuing_body=data["issuing_body"].strip(),
                published_at=self._datetime(data.get("published_at")),
                effective_from=self._datetime(data.get("effective_from")),
                effective_to=self._datetime(data.get("effective_to")), status=status,
                retrieved_at=datetime.now(timezone.utc),
                content_hash=hashlib.sha256(text.encode("utf-8")).hexdigest(),
            )
            db.add(authority)
            db.commit()
            return self._dict(authority)
        except Exception:
            db.rollback()
            raise
        finally:
            db.close()

    def verify(self, authority_id: str, effective_at: datetime, country_code: str) -> Dict:
        """校验法域、状态、适用日期和内容哈希，无法确认时明确降级。"""
        db = SessionLocal()
        try:
            authority = db.get(LegalAuthority, authority_id)
            if authority is None:
                raise AgentRuntimeError("法律来源不存在", "AUTHORITY_NOT_FOUND")
            warnings = []
            valid = True
            if authority.country_code != country_code:
                valid = False
                warnings.append("来源法域与任务法域不一致")
            if authority.status != "effective":
                valid = False
                warnings.append(f"来源状态为 {authority.status}，不能作为确定依据")
            if authority.effective_from and effective_at < authority.effective_from:
                valid = False
                warnings.append("查询日期早于来源生效日期")
            if authority.effective_to and effective_at > authority.effective_to:
                valid = False
                warnings.append("查询日期晚于来源有效期")
            current_hash = hashlib.sha256(authority.text.encode("utf-8")).hexdigest()
            if current_hash != authority.content_hash:
                valid = False
                warnings.append("来源内容哈希校验失败")
            return {"authority_id": authority.id, "valid": valid, "warnings": warnings, "authority": self._dict(authority)}
        finally:
            db.close()

    @staticmethod
    def _datetime(value: Optional[str]):
        if not value:
            return None
        parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
        return parsed if parsed.tzinfo else parsed.replace(tzinfo=timezone.utc)

    @staticmethod
    def _dict(authority: LegalAuthority) -> Dict:
        return {
            "authority_id": authority.id, "country_code": authority.country_code,
            "authority_type": authority.authority_type, "title": authority.title,
            "provision": authority.provision, "source_url": authority.source_url,
            "issuing_body": authority.issuing_body, "status": authority.status,
            "effective_from": authority.effective_from.isoformat() if authority.effective_from else None,
            "effective_to": authority.effective_to.isoformat() if authority.effective_to else None,
            "retrieved_at": authority.retrieved_at.isoformat(), "content_hash": authority.content_hash,
        }
