"""官方法律来源获取协议与中国劳动法源适配器。"""

from __future__ import annotations

import hashlib
import re
from dataclasses import dataclass
from datetime import datetime, timezone
from html.parser import HTMLParser
from typing import Iterable, Protocol
from urllib.parse import urlparse

import httpx
from pydantic import BaseModel, Field, HttpUrl


class AuthorityProviderError(RuntimeError):
    """官方来源获取或解析失败；失败时不得退回内置法条。"""


class AuthorityPayload(BaseModel):
    external_id: str
    country_code: str = Field(pattern=r"^[A-Z]{2}$")
    authority_type: str
    title: str
    provision: str
    text: str
    canonical_url: HttpUrl
    issuing_body: str
    status: str = "effective"
    version: str
    effective_from: datetime | None = None
    effective_to: datetime | None = None
    topic_tags: list[str] = Field(default_factory=list)
    retrieved_at: datetime
    media_type: str
    source_content_hash: str
    raw_content: bytes = Field(repr=False)
    etag: str | None = None
    last_modified: str | None = None
    verification_method: str = "official_https_exact_provision"


class AuthorityProvider(Protocol):
    name: str
    trusted_domains: frozenset[str]

    def fetch(self) -> Iterable[AuthorityPayload]: ...


@dataclass(frozen=True)
class OfficialSourceSpec:
    external_id: str
    authority_type: str
    title: str
    provision: str
    canonical_url: str
    fallback_urls: tuple[str, ...]
    issuing_body: str
    effective_from: str
    article_numbers: tuple[str, ...]
    topic_tags: tuple[str, ...]


@dataclass(frozen=True)
class RetrievedSource:
    content: bytes
    media_type: str
    final_url: str
    retrieved_at: datetime
    etag: str | None
    last_modified: str | None


class OfficialSourceClient(Protocol):
    def get(self, url: str, trusted_domains: frozenset[str]) -> RetrievedSource: ...


class HttpOfficialSourceClient:
    """有大小、HTTPS 和重定向域名限制的官方来源客户端。"""

    def __init__(self, timeout_seconds: float = 12, max_bytes: int = 10 * 1024 * 1024) -> None:
        self.timeout_seconds = timeout_seconds
        self.max_bytes = max_bytes

    def get(self, url: str, trusted_domains: frozenset[str]) -> RetrievedSource:
        self._validate_url(url, trusted_domains)
        with httpx.Client(
            timeout=self.timeout_seconds,
            follow_redirects=True,
            headers={"User-Agent": "YYS-Law-AuthoritySync/1.0"},
        ) as client:
            response = client.get(url)
        response.raise_for_status()
        self._validate_url(str(response.url), trusted_domains)
        content = response.content
        if not content or len(content) > self.max_bytes:
            raise AuthorityProviderError("官方来源内容为空或超过大小限制")
        media_type = response.headers.get("content-type", "application/octet-stream").split(";", 1)[0].lower()
        if media_type not in {"text/html", "text/plain", "application/pdf"}:
            raise AuthorityProviderError(f"不支持的官方来源类型: {media_type}")
        return RetrievedSource(
            content=content,
            media_type=media_type,
            final_url=str(response.url),
            retrieved_at=datetime.now(timezone.utc),
            etag=response.headers.get("etag"),
            last_modified=response.headers.get("last-modified"),
        )

    @staticmethod
    def _validate_url(url: str, trusted_domains: frozenset[str]) -> None:
        parsed = urlparse(url)
        if parsed.scheme != "https" or (parsed.hostname or "").lower() not in trusted_domains:
            raise AuthorityProviderError("官方来源必须使用白名单 HTTPS 域名")


class _VisibleTextParser(HTMLParser):
    def __init__(self) -> None:
        super().__init__(convert_charrefs=True)
        self.parts: list[str] = []
        self.hidden_depth = 0

    def handle_starttag(self, tag: str, _attrs) -> None:
        if tag in {"script", "style", "noscript"}:
            self.hidden_depth += 1

    def handle_endtag(self, tag: str) -> None:
        if tag in {"script", "style", "noscript"} and self.hidden_depth:
            self.hidden_depth -= 1

    def handle_data(self, data: str) -> None:
        if not self.hidden_depth:
            self.parts.append(data)


def _document_text(source: RetrievedSource) -> str:
    if source.media_type == "application/pdf":
        try:
            import fitz
        except ImportError as exc:
            raise AuthorityProviderError("缺少 PDF 解析依赖 PyMuPDF") from exc
        document = fitz.open(stream=source.content, filetype="pdf")
        text = "\n".join(page.get_text("text") for page in document)
    else:
        decoded = source.content.decode("utf-8", errors="replace")
        if source.media_type == "text/html":
            parser = _VisibleTextParser()
            parser.feed(decoded)
            text = "\n".join(parser.parts)
        else:
            text = decoded
    lines = []
    for line in text.splitlines():
        normalized = re.sub(r"\s+", "", line)
        if normalized:
            lines.append(normalized)
    return "\n".join(lines)


def _extract_articles(text: str, article_numbers: tuple[str, ...]) -> str:
    extracted: list[str] = []
    for number in article_numbers:
        marker = f"第{number}条"
        heading_starts = [
            match.start()
            for match in re.finditer(rf"(?m)^{re.escape(marker)}", text)
        ]
        starts = heading_starts or [
            match.start()
            for match in re.finditer(re.escape(marker), text)
        ]
        if not starts:
            raise AuthorityProviderError(f"官方原文缺少预期条款: {marker}")
        candidates = []
        for start in starts:
            remaining = text[start + len(marker):]
            boundary_pattern = (
                r"(?m)^第[一二三四五六七八九十百零〇两]+条"
                if heading_starts
                else r"第[一二三四五六七八九十百零〇两]+条"
            )
            next_match = re.search(boundary_pattern, remaining)
            end = start + len(marker) + next_match.start() if next_match else len(text)
            candidates.append(text[start:end].strip())
        article = max(candidates, key=len)
        if len(article) < len(marker) + 8:
            raise AuthorityProviderError(f"官方条款内容异常短: {marker}")
        extracted.append(article)
    return "\n".join(extracted)


class OfficialCnLaborProvider:
    """实时读取全国人大和人社部官方原文，不提供内置正文降级。"""

    name = "official_cn_labor"
    trusted_domains = frozenset({
        "www.npc.gov.cn",
        "flk.npc.gov.cn",
        "rsj.sh.gov.cn",
        "chinajob.mohrss.gov.cn",
        "www.mohrss.gov.cn",
        "www.samr.gov.cn",
        "fgk.chinatax.gov.cn",
    })
    sources = (
        OfficialSourceSpec(
            external_id="npc-labor-arbitration-law-27",
            authority_type="statute",
            title="中华人民共和国劳动争议调解仲裁法",
            provision="第二十七条",
            canonical_url="https://www.npc.gov.cn/npc/c2/c183/c198/201905/t20190522_28233.html",
            fallback_urls=("https://rsj.sh.gov.cn/tgjfl_17254/20200617/t0035_1388236.html",),
            issuing_body="全国人民代表大会常务委员会",
            effective_from="2008-05-01T00:00:00+00:00",
            article_numbers=("二十七",),
            topic_tags=("仲裁时效", "欠薪"),
        ),
        OfficialSourceSpec(
            external_id="mohrss-arbitration-rules-26-28",
            authority_type="regulation",
            title="劳动人事争议仲裁办案规则",
            provision="第二十六条至第二十八条",
            canonical_url="https://www.mohrss.gov.cn/xxgk2020/gzk/gz/202112/P020211229545889175624.pdf",
            fallback_urls=("https://chinajob.mohrss.gov.cn/h5/c/2022-07-15/356204.shtml",),
            issuing_body="人力资源和社会保障部",
            effective_from="2017-07-01T00:00:00+00:00",
            article_numbers=("二十六", "二十七", "二十八"),
            topic_tags=("仲裁时效", "中断", "中止"),
        ),
        OfficialSourceSpec(
            external_id="samr-labor-contract-law-substantive",
            authority_type="statute",
            title="中华人民共和国劳动合同法",
            provision="第七条、第十条、第十九条至第二十一条、第三十条、第三十八条至第四十二条、第四十六条至第四十八条、第八十五条、第八十七条",
            canonical_url="https://www.samr.gov.cn/zw/zfxxgk/fdzdgknr/bgt/art/2023/art_0abfdd261c03417b949df19d869add8d.html",
            fallback_urls=("https://fgk.chinatax.gov.cn/zcfgk/c100009/c5193025/content.html",),
            issuing_body="全国人民代表大会常务委员会",
            effective_from="2013-07-01T00:00:00+00:00",
            article_numbers=(
                "七", "十", "十九", "二十", "二十一", "三十",
                "三十八", "三十九", "四十", "四十一", "四十二",
                "四十六", "四十七", "四十八", "八十五", "八十七",
            ),
            topic_tags=("劳动关系", "劳动合同", "试用期", "欠薪", "劳动报酬", "解除", "经济补偿", "违法解除", "赔偿金"),
        ),
        OfficialSourceSpec(
            external_id="samr-labor-law-wages",
            authority_type="statute",
            title="中华人民共和国劳动法",
            provision="第四十四条、第五十条、第九十一条",
            canonical_url="https://www.samr.gov.cn/zw/zfxxgk/fdzdgknr/bgt/art/2023/art_d9aa750028b14b99a776cb93726a360d.html",
            fallback_urls=("https://www.npc.gov.cn/zgrdw/npc/zt/2006-03/20/content_347911.htm",),
            issuing_body="全国人民代表大会常务委员会",
            effective_from="2018-12-29T00:00:00+00:00",
            article_numbers=("四十四", "五十", "九十一"),
            topic_tags=("欠薪", "工资支付", "劳动报酬", "加班费", "延长工作时间"),
        ),
    )

    def __init__(self, client: OfficialSourceClient | None = None) -> None:
        self.client = client or HttpOfficialSourceClient()
        self.last_errors: list[str] = []

    def fetch(self) -> Iterable[AuthorityPayload]:
        payloads: list[AuthorityPayload] = []
        self.last_errors = []
        for spec in self.sources:
            source = None
            provision_text = None
            errors = []
            for source_url in (spec.canonical_url, *spec.fallback_urls):
                try:
                    source = self.client.get(source_url, self.trusted_domains)
                    text = _document_text(source)
                    if spec.title not in text:
                        raise AuthorityProviderError(f"官方页面标题不匹配: {spec.title}")
                    provision_text = _extract_articles(text, spec.article_numbers)
                    break
                except Exception as exc:
                    errors.append(
                        f"{urlparse(source_url).hostname}: {self._error_label(exc)}"
                    )
                    source = None
            if source is None:
                self.last_errors.append(f"{spec.external_id}: {'; '.join(errors)}")
                continue
            content_hash = hashlib.sha256(source.content).hexdigest()
            authority_version = hashlib.sha256(
                f"{spec.external_id}\n{spec.provision}\n{provision_text}\n{spec.effective_from}".encode("utf-8")
            ).hexdigest()[:16]
            payloads.append(AuthorityPayload(
                external_id=spec.external_id,
                country_code="CN",
                authority_type=spec.authority_type,
                title=spec.title,
                provision=spec.provision,
                text=provision_text,
                canonical_url=source.final_url,
                issuing_body=spec.issuing_body,
                effective_from=datetime.fromisoformat(spec.effective_from),
                topic_tags=list(spec.topic_tags),
                version=authority_version,
                retrieved_at=source.retrieved_at,
                media_type=source.media_type,
                source_content_hash=content_hash,
                raw_content=source.content,
                etag=source.etag,
                last_modified=source.last_modified,
            ))
        if not payloads:
            raise AuthorityProviderError(f"所有官方来源均不可用: {'; '.join(self.last_errors)}")
        return payloads

    @staticmethod
    def _error_label(exc: Exception) -> str:
        if isinstance(exc, AuthorityProviderError):
            return f"AuthorityProviderError({str(exc)[:200]})"
        if isinstance(exc, httpx.HTTPStatusError):
            return f"HTTPStatusError({exc.response.status_code})"
        return type(exc).__name__
