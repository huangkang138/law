"""法域能力注册中心。"""

from dataclasses import dataclass
from typing import Dict, List

from legal_agent_system.runtime.errors import AgentRuntimeError


@dataclass(frozen=True)
class JurisdictionPackage:
    """一个法域包的稳定能力声明。"""

    country_code: str
    name: str
    legal_system: str
    default_language: str
    authority_types: List[str]


class JurisdictionRegistry:
    """按国家代码加载法域能力，禁止未注册法域静默降级。"""

    def __init__(self) -> None:
        self._packages: Dict[str, JurisdictionPackage] = {}

    def register(self, package: JurisdictionPackage) -> None:
        if package.country_code in self._packages:
            raise ValueError(f"法域已注册: {package.country_code}")
        self._packages[package.country_code] = package

    def get(self, country_code: str) -> JurisdictionPackage:
        try:
            return self._packages[country_code]
        except KeyError as exc:
            raise AgentRuntimeError(f"暂不支持法域: {country_code}", "JURISDICTION_UNSUPPORTED") from exc

    def list_packages(self) -> List[JurisdictionPackage]:
        return list(self._packages.values())


_registry = JurisdictionRegistry()
_registry.register(JurisdictionPackage(
    country_code="CN", name="中华人民共和国", legal_system="civil_law",
    default_language="zh-CN", authority_types=["statute", "regulation", "judicial_interpretation", "guidance"],
))


def get_jurisdiction_registry() -> JurisdictionRegistry:
    """获取共享法域注册中心。"""
    return _registry
