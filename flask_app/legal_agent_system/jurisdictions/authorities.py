"""法律来源登记与引用有效性校验。"""

import hashlib
import uuid
from datetime import datetime, timedelta, timezone
from typing import Dict, Optional
from urllib.parse import urlparse

from core.database import SessionLocal
from models.db_models import LegalAuthority

from legal_agent_system.runtime.errors import AgentRuntimeError
from .registry import get_jurisdiction_registry


class LegalAuthorityService:
    """保存可追溯来源；不负责联网检索，也不把未知来源包装为有效法律。"""

    VALID_STATUSES = {"effective", "repealed", "amended", "unknown"}

    def register_test(self, data: Dict) -> Dict:
        """仅为自动化测试登记 `.invalid` 来源，禁止承载真实法律内容。"""
        hostname = (urlparse(str(data.get("source_url", ""))).hostname or "").lower()
        if not hostname.endswith(".invalid"):
            raise AgentRuntimeError("测试来源必须使用 .invalid 保留域名", "TEST_AUTHORITY_ONLY")
        payload = {**data, "provider": "test_fixture", "external_id": data.get("external_id") or f"test-{uuid.uuid4().hex}", "canonical_url": data.get("source_url"), "trust_level": "test", "version": data.get("version", "1"), "retrieval_status": "verified"}
        return self._register(payload)

    FRESHNESS_DAYS = 7

    def register_provider(self, data: Dict, provider: str) -> Dict:
        """写入官方快照解析结果；正文变化必须人工复核后才能使用。"""
        payload = {
            **data, "provider": provider,
            "source_url": str(data.get("canonical_url")),
            "canonical_url": str(data.get("canonical_url")),
            "trust_level": "trusted",
        }
        return self._register(payload)

    def _register(self, data: Dict) -> Dict:
        """内部持久化入口；生产来源后续只能由可信 Provider 调用。"""
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
            latest = None
            if data.get("external_id"):
                latest = db.query(LegalAuthority).filter(
                    LegalAuthority.provider == data.get("provider"),
                    LegalAuthority.external_id == data.get("external_id"),
                ).order_by(LegalAuthority.retrieved_at.desc()).first()
                if latest and latest.version == str(data.get("version", "1")):
                    latest.retrieved_at = self._datetime(data.get("retrieved_at")) or datetime.now(timezone.utc)
                    latest.last_verified_at = latest.retrieved_at
                    latest.source_snapshot_id = data.get("source_snapshot_id") or latest.source_snapshot_id
                    latest.verification_method = data.get("verification_method") or latest.verification_method
                    if latest.retrieval_status == "verified":
                        latest.fresh_until = latest.last_verified_at + timedelta(days=self.FRESHNESS_DAYS)
                    db.commit()
                    result = self._dict(latest)
                    result["_change_type"] = "unchanged"
                    return result
            retrieved_at = self._datetime(data.get("retrieved_at")) or datetime.now(timezone.utc)
            changed = latest is not None
            authority = LegalAuthority(
                id=f"authority_{uuid.uuid4().hex}", country_code=country_code,
                subdivision_code=data.get("subdivision_code"), authority_type=authority_type,
                title=data["title"].strip(), provision=data.get("provision"), text=text,
                source_url=data["source_url"].strip(), issuing_body=data["issuing_body"].strip(),
                published_at=self._datetime(data.get("published_at")),
                effective_from=self._datetime(data.get("effective_from")),
                effective_to=self._datetime(data.get("effective_to")), status=status,
                retrieved_at=retrieved_at,
                content_hash=hashlib.sha256(text.encode("utf-8")).hexdigest(),
                provider=data.get("provider", "legacy"), external_id=data.get("external_id"),
                canonical_url=data.get("canonical_url") or data["source_url"], trust_level=data.get("trust_level", "untrusted"),
                version=str(data.get("version", "1")), supersedes_id=latest.id if changed else data.get("supersedes_id"),
                last_verified_at=retrieved_at,
                fresh_until=None if changed else retrieved_at + timedelta(days=self.FRESHNESS_DAYS),
                retrieval_status="review_required" if changed else "verified",
                source_snapshot_id=data.get("source_snapshot_id"),
                verification_method=data.get("verification_method"),
            )
            if changed:
                latest.retrieval_status = "superseded"
                latest.fresh_until = retrieved_at
            db.add(authority)
            db.commit()
            result = self._dict(authority)
            result["_change_type"] = "changed" if changed else "imported"
            return result
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
            if authority.trust_level not in {"trusted", "test"}:
                valid = False
                warnings.append("来源未通过可信 Provider 验证")
            if authority.retrieval_status != "verified":
                valid = False
                warnings.append("来源同步状态不是 verified")
            now = datetime.now(timezone.utc)
            fresh_until = authority.fresh_until
            if fresh_until and fresh_until.tzinfo is None:
                fresh_until = fresh_until.replace(tzinfo=timezone.utc)
            if not fresh_until or now > fresh_until:
                valid = False
                warnings.append("来源已超过官网核验新鲜度期限")
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
            "provider": authority.provider, "external_id": authority.external_id,
            "canonical_url": authority.canonical_url, "trust_level": authority.trust_level,
            "version": authority.version, "last_verified_at": authority.last_verified_at.isoformat() if authority.last_verified_at else None,
            "fresh_until": authority.fresh_until.isoformat() if authority.fresh_until else None,
            "retrieval_status": authority.retrieval_status,
            "source_snapshot_id": authority.source_snapshot_id,
            "verification_method": authority.verification_method,
        }

    def approve_version(self, authority_id: str) -> Dict:
        """内部人工复核入口；不通过 HTTP 或 Agent 工具公开。"""
        db = SessionLocal()
        try:
            authority = db.get(LegalAuthority, authority_id)
            if authority is None:
                raise AgentRuntimeError("法律来源不存在", "AUTHORITY_NOT_FOUND")
            if authority.retrieval_status != "review_required":
                raise AgentRuntimeError("该版本不在待复核状态", "INVALID_STATE")
            now = datetime.now(timezone.utc)
            authority.retrieval_status = "verified"
            authority.last_verified_at = now
            authority.fresh_until = now + timedelta(days=self.FRESHNESS_DAYS)
            db.commit()
            return self._dict(authority)
        finally:
            db.close()

    def search(self, country_code: str, effective_at: datetime, terms) -> list:
        """小语料使用结构化过滤和关键词匹配，返回已验证来源。"""
        db = SessionLocal()
        try:
            rows = db.query(LegalAuthority).filter(LegalAuthority.country_code == country_code, LegalAuthority.status == "effective", LegalAuthority.trust_level.in_(["trusted", "test"]), LegalAuthority.retrieval_status == "verified").order_by(LegalAuthority.retrieved_at.desc()).all()
            results = []
            for row in rows:
                haystack = f"{row.title} {row.provision or ''} {row.text}"
                if terms and not all(term in haystack for term in terms):
                    continue
                verified = self.verify(row.id, effective_at, country_code)
                if verified["valid"]:
                    results.append(self._dict(row))
            return results
        finally:
            db.close()

    def has_fresh_sources(self, provider: str, external_ids) -> bool:
        """避免每个 HTTP 请求访问官网；超过新鲜度后才触发同步。"""
        expected = set(external_ids)
        if not expected:
            return False
        db = SessionLocal()
        try:
            now = datetime.now(timezone.utc)
            rows = db.query(LegalAuthority).filter(
                LegalAuthority.provider == provider,
                LegalAuthority.external_id.in_(expected),
                LegalAuthority.retrieval_status == "verified",
                LegalAuthority.fresh_until.isnot(None),
                LegalAuthority.fresh_until > now,
            ).all()
            return {row.external_id for row in rows} == expected
        finally:
            db.close()
