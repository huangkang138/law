"""法源运维治理：健康状态、待复核队列和人工决策审计。"""

from __future__ import annotations

import uuid
from datetime import datetime, timedelta, timezone

from core.database import SessionLocal
from legal_agent_system.models import (
    AuthoritySourceReview,
    AuthoritySourceSnapshot,
    AuthoritySyncRun,
)
from legal_agent_system.runtime.errors import AgentRuntimeError
from models.db_models import LegalAuthority

from .authorities import LegalAuthorityService


class AuthorityGovernanceService:
    """只供内部运维与只读健康查询使用，不向 Agent 开放写入能力。"""

    DECISIONS = {"approve": "approved", "reject": "rejected"}

    def health(self, provider: str, expected_external_ids) -> dict:
        expected = list(dict.fromkeys(expected_external_ids))
        now = datetime.now(timezone.utc)
        db = SessionLocal()
        try:
            rows = db.query(LegalAuthority).filter(
                LegalAuthority.provider == provider,
            ).order_by(LegalAuthority.retrieved_at.desc()).all()
            latest_by_external_id = {}
            for row in rows:
                if row.external_id and row.external_id not in latest_by_external_id:
                    latest_by_external_id[row.external_id] = row

            source_states = []
            ready_count = 0
            for external_id in expected:
                row = latest_by_external_id.get(external_id)
                state = self._source_state(row, now)
                ready_count += int(state == "ready")
                source_states.append({
                    "external_id": external_id,
                    "state": state,
                    "authority_id": row.id if row else None,
                    "version": row.version if row else None,
                    "fresh_until": self._iso(row.fresh_until) if row else None,
                })

            latest_sync = db.query(AuthoritySyncRun).filter(
                AuthoritySyncRun.provider == provider,
            ).order_by(AuthoritySyncRun.started_at.desc()).first()
            pending_count = sum(item["state"] == "review_required" for item in source_states)
            missing_count = sum(item["state"] == "missing" for item in source_states)
            stale_count = sum(item["state"] == "stale" for item in source_states)
            failed_count = sum(item["state"] in {"sync_failed", "rejected", "superseded"} for item in source_states)
            status = "ready" if expected and ready_count == len(expected) else "degraded" if ready_count else "unavailable"
            return {
                "status": status,
                "provider": provider,
                "checked_at": now.isoformat(),
                "expected_count": len(expected),
                "ready_count": ready_count,
                "pending_review_count": pending_count,
                "stale_count": stale_count,
                "missing_count": missing_count,
                "failed_count": failed_count,
                "sources": source_states,
                "latest_sync": self._sync_dict(latest_sync),
            }
        finally:
            db.close()

    def pending_reviews(self, provider: str | None = None) -> list[dict]:
        db = SessionLocal()
        try:
            query = db.query(LegalAuthority).filter(
                LegalAuthority.retrieval_status == "review_required",
            )
            if provider:
                query = query.filter(LegalAuthority.provider == provider)
            rows = query.order_by(LegalAuthority.retrieved_at.asc()).all()
            previous_ids = [row.supersedes_id for row in rows if row.supersedes_id]
            previous = {
                row.id: row for row in db.query(LegalAuthority).filter(
                    LegalAuthority.id.in_(previous_ids),
                ).all()
            } if previous_ids else {}
            return [self._pending_dict(row, previous.get(row.supersedes_id)) for row in rows]
        finally:
            db.close()

    def review(
        self,
        authority_id: str,
        decision: str,
        reviewer_id: str,
        notes: str | None = None,
    ) -> dict:
        normalized_decision = self.DECISIONS.get(decision)
        reviewer_id = reviewer_id.strip()
        notes = notes.strip() if notes else None
        if normalized_decision is None:
            raise AgentRuntimeError("复核决定必须是 approve 或 reject", "INVALID_INPUT")
        if not reviewer_id or len(reviewer_id) > 100:
            raise AgentRuntimeError("复核人标识不能为空且不能超过 100 字符", "INVALID_INPUT")
        if not notes:
            raise AgentRuntimeError("法源复核必须填写对照依据或驳回原因", "INVALID_INPUT")

        db = SessionLocal()
        try:
            authority = db.get(LegalAuthority, authority_id)
            if authority is None:
                raise AgentRuntimeError("法律来源不存在", "AUTHORITY_NOT_FOUND")
            if authority.retrieval_status != "review_required":
                raise AgentRuntimeError("该版本不在待复核状态", "INVALID_STATE")

            now = datetime.now(timezone.utc)
            authority.retrieval_status = "verified" if decision == "approve" else "rejected"
            authority.last_verified_at = now if decision == "approve" else authority.last_verified_at
            authority.fresh_until = (
                now + timedelta(days=LegalAuthorityService.FRESHNESS_DAYS)
                if decision == "approve" else now
            )
            if authority.source_snapshot_id:
                snapshot = db.get(AuthoritySourceSnapshot, authority.source_snapshot_id)
                if snapshot:
                    snapshot.verification_status = normalized_decision
            review = AuthoritySourceReview(
                id=f"authority_review_{uuid.uuid4().hex}",
                authority_id=authority.id,
                source_snapshot_id=authority.source_snapshot_id,
                decision=normalized_decision,
                reviewer_id=reviewer_id,
                notes=notes,
                decided_at=now,
            )
            db.add(review)
            db.commit()
            return {
                "authority": LegalAuthorityService._dict(authority),
                "review": self._review_dict(review),
            }
        except Exception:
            db.rollback()
            raise
        finally:
            db.close()

    @staticmethod
    def _source_state(authority: LegalAuthority | None, now: datetime) -> str:
        if authority is None:
            return "missing"
        if authority.retrieval_status != "verified":
            return authority.retrieval_status
        fresh_until = authority.fresh_until
        if fresh_until and fresh_until.tzinfo is None:
            fresh_until = fresh_until.replace(tzinfo=timezone.utc)
        return "ready" if fresh_until and fresh_until > now else "stale"

    @classmethod
    def _pending_dict(cls, authority: LegalAuthority, previous: LegalAuthority | None) -> dict:
        return {
            "authority_id": authority.id,
            "provider": authority.provider,
            "external_id": authority.external_id,
            "title": authority.title,
            "provision": authority.provision,
            "version": authority.version,
            "content_hash": authority.content_hash,
            "source_snapshot_id": authority.source_snapshot_id,
            "canonical_url": authority.canonical_url,
            "verification_method": authority.verification_method,
            "candidate_text": authority.text,
            "retrieved_at": cls._iso(authority.retrieved_at),
            "supersedes": {
                "authority_id": previous.id,
                "version": previous.version,
                "content_hash": previous.content_hash,
                "text": previous.text,
            } if previous else None,
        }

    @classmethod
    def _sync_dict(cls, run: AuthoritySyncRun | None) -> dict | None:
        if run is None:
            return None
        return {
            "run_id": run.id,
            "status": run.status,
            "trigger": run.trigger,
            "requested_by": run.requested_by,
            "fetched_count": run.fetched_count,
            "imported_count": run.imported_count,
            "unchanged_count": run.unchanged_count,
            "review_required_count": run.review_required_count,
            "failed_count": run.failed_count,
            "error_code": run.error_code,
            "started_at": cls._iso(run.started_at),
            "completed_at": cls._iso(run.completed_at),
        }

    @classmethod
    def _review_dict(cls, review: AuthoritySourceReview) -> dict:
        return {
            "review_id": review.id,
            "authority_id": review.authority_id,
            "source_snapshot_id": review.source_snapshot_id,
            "decision": review.decision,
            "reviewer_id": review.reviewer_id,
            "notes": review.notes,
            "decided_at": cls._iso(review.decided_at),
        }

    @staticmethod
    def _iso(value: datetime | None) -> str | None:
        return value.isoformat() if value else None
