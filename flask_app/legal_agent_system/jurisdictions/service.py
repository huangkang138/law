"""Matter 法域上下文持久化服务。"""

import uuid
from datetime import datetime, timezone

from core.database import SessionLocal
from models.db_models import Matter, MatterJurisdiction

from legal_agent_system.runtime.errors import AgentRuntimeError
from .registry import get_jurisdiction_registry


class MatterJurisdictionService:
    """登记用户确认的法域，不根据地理位置自动推定适用法律。"""

    def confirm(self, matter_id: str, client_id: str, data):
        country_code = str(data.get("country_code", "")).upper()
        package = get_jurisdiction_registry().get(country_code)
        if data.get("confirmed_by_user") is not True:
            raise AgentRuntimeError("法域必须由用户明确确认", "JURISDICTION_CONFIRMATION_REQUIRED")

        effective_at = datetime.fromisoformat(str(data.get("effective_at", "")).replace("Z", "+00:00"))
        if effective_at.tzinfo is None:
            effective_at = effective_at.replace(tzinfo=timezone.utc)
        db = SessionLocal()
        try:
            matter = db.get(Matter, matter_id)
            if matter is None:
                raise AgentRuntimeError("Matter 不存在", "MATTER_NOT_FOUND")
            if matter.client_id != client_id:
                raise AgentRuntimeError("无权访问该 Matter", "FORBIDDEN")
            db.query(MatterJurisdiction).filter(
                MatterJurisdiction.matter_id == matter_id,
                MatterJurisdiction.status == "confirmed",
            ).update({"status": "rejected"}, synchronize_session=False)
            jurisdiction = MatterJurisdiction(
                id=f"jurisdiction_{uuid.uuid4().hex}", matter_id=matter_id,
                country_code=country_code, subdivision_code=data.get("subdivision_code"),
                legal_system=package.legal_system, governing_law=data.get("governing_law"),
                forum=data.get("forum"), language=data.get("language", package.default_language),
                effective_at=effective_at, confidence=1.0, confirmed_by_user=True,
                status="confirmed", basis_json=["user_confirmation"],
            )
            db.add(jurisdiction)
            db.commit()
            return {
                "jurisdiction_id": jurisdiction.id, "country_code": country_code,
                "subdivision_code": jurisdiction.subdivision_code,
                "legal_system": jurisdiction.legal_system, "language": jurisdiction.language,
                "effective_at": jurisdiction.effective_at.isoformat(), "confirmed_by_user": True,
            }
        except Exception:
            db.rollback()
            raise
        finally:
            db.close()
