"""法域包注册入口。"""

from .registry import JurisdictionRegistry, get_jurisdiction_registry
from .service import MatterJurisdictionService

__all__ = ["JurisdictionRegistry", "get_jurisdiction_registry", "MatterJurisdictionService"]
