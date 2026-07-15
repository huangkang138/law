"""官方法源同步编排：批次审计、原始快照和版本写入。"""

from __future__ import annotations

import uuid
from datetime import datetime, timezone
from urllib.parse import urlparse

from core.database import SessionLocal
from legal_agent_system.models import AuthoritySourceSnapshot, AuthoritySyncRun
from models.db_models import LegalAuthority

from .authority_provider import AuthorityProvider


class TrustedAuthorityImporter:
    """只允许可信 Provider 写入，任何失败都记录且不使用内置正文降级。"""

    def __init__(self, service) -> None:
        self.service = service

    def import_all(self, provider: AuthorityProvider):
        run_id = f"authority_sync_{uuid.uuid4().hex}"
        self._create_run(run_id, provider.name)
        try:
            payloads = list(provider.fetch())
            results = []
            counts = {"fetched_count": len(payloads), "imported_count": 0, "unchanged_count": 0, "review_required_count": 0}
            for payload in payloads:
                host = (urlparse(str(payload.canonical_url)).hostname or "").lower()
                if host not in provider.trusted_domains:
                    raise ValueError(f"Provider {provider.name} 返回了非白名单域名")
                snapshot_id = self._save_snapshot(run_id, provider.name, payload)
                data = payload.model_dump(mode="json", exclude={"raw_content"})
                data["source_snapshot_id"] = snapshot_id
                result = self.service.register_provider(data, provider.name)
                self._link_snapshot(snapshot_id, result["authority_id"], result["retrieval_status"])
                change_type = result.pop("_change_type", "imported")
                counts["unchanged_count" if change_type == "unchanged" else "imported_count"] += 1
                if result["retrieval_status"] == "review_required":
                    counts["review_required_count"] += 1
                results.append(result)
            status = "review_required" if counts["review_required_count"] else "completed"
            self._finish_run(run_id, status, counts)
            return results
        except Exception as exc:
            self._fail_run(run_id, exc)
            raise

    @staticmethod
    def _create_run(run_id: str, provider: str) -> None:
        db = SessionLocal()
        try:
            db.add(AuthoritySyncRun(id=run_id, provider=provider, status="running", started_at=datetime.now(timezone.utc)))
            db.commit()
        finally:
            db.close()

    @staticmethod
    def _save_snapshot(run_id: str, provider: str, payload) -> str:
        db = SessionLocal()
        try:
            snapshot = AuthoritySourceSnapshot(
                id=f"authority_snapshot_{uuid.uuid4().hex}", sync_run_id=run_id,
                provider=provider, external_id=payload.external_id,
                canonical_url=str(payload.canonical_url), media_type=payload.media_type,
                source_content_hash=payload.source_content_hash, raw_content=payload.raw_content,
                etag=payload.etag, last_modified=payload.last_modified,
                verification_method=payload.verification_method,
                verification_status="fetched", retrieved_at=payload.retrieved_at,
            )
            db.add(snapshot)
            db.commit()
            return snapshot.id
        finally:
            db.close()

    @staticmethod
    def _link_snapshot(snapshot_id: str, authority_id: str, status: str) -> None:
        db = SessionLocal()
        try:
            snapshot = db.get(AuthoritySourceSnapshot, snapshot_id)
            snapshot.authority_id = authority_id
            snapshot.verification_status = status
            db.commit()
        finally:
            db.close()

    @staticmethod
    def _finish_run(run_id: str, status: str, counts: dict) -> None:
        db = SessionLocal()
        try:
            run = db.get(AuthoritySyncRun, run_id)
            run.status = status
            run.completed_at = datetime.now(timezone.utc)
            for key, value in counts.items():
                setattr(run, key, value)
            db.commit()
        finally:
            db.close()

    @staticmethod
    def _fail_run(run_id: str, exc: Exception) -> None:
        db = SessionLocal()
        try:
            run = db.get(AuthoritySyncRun, run_id)
            run.status = "failed"
            run.error_code = type(exc).__name__
            run.error_message = str(exc)[:1000]
            run.completed_at = datetime.now(timezone.utc)
            snapshots = db.query(AuthoritySourceSnapshot).filter(
                AuthoritySourceSnapshot.sync_run_id == run_id,
            ).all()
            authority_ids = [row.authority_id for row in snapshots if row.authority_id]
            snapshot_ids = [row.id for row in snapshots]
            if authority_ids:
                db.query(LegalAuthority).filter(LegalAuthority.id.in_(authority_ids)).update({
                    LegalAuthority.retrieval_status: "sync_failed",
                    LegalAuthority.fresh_until: datetime.now(timezone.utc),
                }, synchronize_session=False)
            if snapshot_ids:
                db.query(LegalAuthority).filter(LegalAuthority.source_snapshot_id.in_(snapshot_ids)).update({
                    LegalAuthority.retrieval_status: "sync_failed",
                    LegalAuthority.fresh_until: datetime.now(timezone.utc),
                }, synchronize_session=False)
            db.commit()
        finally:
            db.close()
