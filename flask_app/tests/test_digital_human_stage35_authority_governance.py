"""阶段 3.5 法源健康、人工复核和审计闭环。"""

import hashlib
import unittest
import uuid
from datetime import datetime, timedelta, timezone

from core.database import SessionLocal
from legal_agent_system.jurisdictions.authority_governance import AuthorityGovernanceService
from legal_agent_system.models import (
    AuthoritySourceReview,
    AuthoritySourceSnapshot,
    AuthoritySyncRun,
)
from legal_agent_system.runtime.errors import AgentRuntimeError
from models.db_models import LegalAuthority


class DigitalHumanStage35AuthorityGovernanceTest(unittest.TestCase):
    def setUp(self):
        suffix = uuid.uuid4().hex
        self.provider = f"authority_governance_fixture_{suffix}"
        self.external_id = f"source_{suffix}"
        self.sync_run_id = f"authority_sync_{suffix}"
        self.previous_id = f"authority_previous_{suffix}"
        self.pending_id = f"authority_pending_{suffix}"
        self.snapshot_id = f"authority_snapshot_{suffix}"
        now = datetime.now(timezone.utc)
        db = SessionLocal()
        try:
            db.add(AuthoritySyncRun(
                id=self.sync_run_id,
                provider=self.provider,
                status="review_required",
                trigger="scheduled",
                requested_by="test_scheduler",
                fetched_count=1,
                imported_count=1,
                review_required_count=1,
                started_at=now,
                completed_at=now,
            ))
            db.add(LegalAuthority(
                id=self.previous_id,
                country_code="CN",
                authority_type="statute",
                title="测试法律",
                provision="第一条",
                text="旧正文",
                source_url="https://www.npc.gov.cn/test-old",
                issuing_body="测试机关",
                status="effective",
                retrieved_at=now - timedelta(days=1),
                content_hash=hashlib.sha256("旧正文".encode()).hexdigest(),
                provider=self.provider,
                external_id=self.external_id,
                canonical_url="https://www.npc.gov.cn/test-old",
                trust_level="trusted",
                version="old",
                last_verified_at=now - timedelta(days=1),
                fresh_until=now,
                retrieval_status="superseded",
            ))
            db.flush()
            db.add(AuthoritySourceSnapshot(
                id=self.snapshot_id,
                sync_run_id=self.sync_run_id,
                provider=self.provider,
                external_id=self.external_id,
                canonical_url="https://www.npc.gov.cn/test-new",
                media_type="text/html",
                source_content_hash=hashlib.sha256(b"new raw").hexdigest(),
                raw_content=b"new raw",
                verification_method="test_exact",
                verification_status="review_required",
                retrieved_at=now,
            ))
            db.flush()
            db.add(LegalAuthority(
                id=self.pending_id,
                country_code="CN",
                authority_type="statute",
                title="测试法律",
                provision="第一条",
                text="新正文",
                source_url="https://www.npc.gov.cn/test-new",
                issuing_body="测试机关",
                status="effective",
                retrieved_at=now,
                content_hash=hashlib.sha256("新正文".encode()).hexdigest(),
                provider=self.provider,
                external_id=self.external_id,
                canonical_url="https://www.npc.gov.cn/test-new",
                trust_level="trusted",
                version="new",
                supersedes_id=self.previous_id,
                last_verified_at=now,
                retrieval_status="review_required",
                source_snapshot_id=self.snapshot_id,
                verification_method="test_exact",
            ))
            db.commit()
        finally:
            db.close()

    def tearDown(self):
        db = SessionLocal()
        try:
            authority_ids = [self.previous_id, self.pending_id]
            db.query(AuthoritySourceReview).filter(
                AuthoritySourceReview.authority_id.in_(authority_ids),
            ).delete(synchronize_session=False)
            db.query(LegalAuthority).filter(
                LegalAuthority.id.in_(authority_ids),
            ).delete(synchronize_session=False)
            db.query(AuthoritySourceSnapshot).filter(
                AuthoritySourceSnapshot.id == self.snapshot_id,
            ).delete(synchronize_session=False)
            db.query(AuthoritySyncRun).filter(
                AuthoritySyncRun.id == self.sync_run_id,
            ).delete(synchronize_session=False)
            db.commit()
        finally:
            db.close()

    def test_pending_version_blocks_until_audited_approval(self):
        service = AuthorityGovernanceService()
        before = service.health(self.provider, [self.external_id])
        self.assertEqual(before["status"], "unavailable")
        self.assertEqual(before["pending_review_count"], 1)
        self.assertEqual(before["latest_sync"]["trigger"], "scheduled")
        pending = service.pending_reviews(self.provider)
        self.assertEqual(pending[0]["supersedes"]["authority_id"], self.previous_id)

        result = service.review(
            self.pending_id,
            "approve",
            "legal_reviewer_01",
            "已对照官网原始快照确认正文变更",
        )

        self.assertEqual(result["authority"]["retrieval_status"], "verified")
        self.assertEqual(result["review"]["decision"], "approved")
        after = service.health(self.provider, [self.external_id])
        self.assertEqual(after["status"], "ready")
        self.assertEqual(after["ready_count"], 1)
        db = SessionLocal()
        try:
            snapshot = db.get(AuthoritySourceSnapshot, self.snapshot_id)
            review = db.query(AuthoritySourceReview).filter_by(
                authority_id=self.pending_id,
            ).one()
            self.assertEqual(snapshot.verification_status, "approved")
            self.assertEqual(review.reviewer_id, "legal_reviewer_01")
        finally:
            db.close()

    def test_reject_requires_reason(self):
        service = AuthorityGovernanceService()
        with self.assertRaises(AgentRuntimeError):
            service.review(self.pending_id, "reject", "legal_reviewer_02")
        result = service.review(
            self.pending_id,
            "reject",
            "legal_reviewer_02",
            "条款定位与官网版本不一致",
        )
        self.assertEqual(result["authority"]["retrieval_status"], "rejected")
        self.assertEqual(result["review"]["decision"], "rejected")


if __name__ == "__main__":
    unittest.main()
