"""只允许可信 Provider 写入生产法律来源。"""

from urllib.parse import urlparse

from .authority_provider import AuthorityProvider


class TrustedAuthorityImporter:
    def __init__(self, service) -> None:
        self.service = service

    def import_all(self, provider: AuthorityProvider):
        imported = []
        for payload in provider.fetch():
            host = (urlparse(str(payload.canonical_url)).hostname or "").lower()
            if host not in provider.trusted_domains:
                raise ValueError(f"Provider {provider.name} 返回了非白名单域名")
            imported.append(self.service.register_provider(payload.model_dump(mode="json"), provider.name))
        return imported
