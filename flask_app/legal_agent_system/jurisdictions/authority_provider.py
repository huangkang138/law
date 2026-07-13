"""可信法律来源 Provider 协议与首批中国劳动来源。"""

from datetime import datetime
from typing import Iterable, Protocol

from pydantic import BaseModel, Field, HttpUrl


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
    version: str = "1"
    effective_from: datetime | None = None
    effective_to: datetime | None = None
    topic_tags: list[str] = Field(default_factory=list)


class AuthorityProvider(Protocol):
    name: str
    trusted_domains: frozenset[str]

    def fetch(self) -> Iterable[AuthorityPayload]: ...


class OfficialCnLaborProvider:
    """首批离线清单；正文与 URL 来自全国人大和人社部官方页面。"""

    name = "official_cn_labor"
    trusted_domains = frozenset({"www.npc.gov.cn", "chinajob.mohrss.gov.cn", "www.mohrss.gov.cn"})

    def fetch(self) -> Iterable[AuthorityPayload]:
        return [
            AuthorityPayload(
                external_id="npc-labor-arbitration-law-27", country_code="CN", authority_type="statute",
                title="中华人民共和国劳动争议调解仲裁法", provision="第二十七条",
                text="劳动争议申请仲裁的时效期间为一年。仲裁时效期间从当事人知道或者应当知道其权利被侵害之日起计算。劳动关系存续期间因拖欠劳动报酬发生争议的，不受前述一年期间限制；劳动关系终止的，应当自终止之日起一年内提出。",
                canonical_url="https://www.npc.gov.cn/npc/c2/c183/c198/201905/t20190522_28233.html",
                issuing_body="全国人民代表大会常务委员会", version="2008-05-01",
                effective_from=datetime.fromisoformat("2008-05-01T00:00:00+00:00"), topic_tags=["仲裁时效", "欠薪"],
            ),
            AuthorityPayload(
                external_id="mohrss-arbitration-rules-26-28", country_code="CN", authority_type="regulation",
                title="劳动人事争议仲裁办案规则", provision="第二十六条至第二十八条",
                text="申请仲裁的时效期间为一年；主张权利、请求救济或对方同意履行会导致时效中断并重新计算；因不可抗力等正当理由不能申请的，时效中止，原因消除后继续计算。",
                canonical_url="https://chinajob.mohrss.gov.cn/h5/c/2022-07-15/356204.shtml",
                issuing_body="人力资源和社会保障部", version="2017-07-01",
                effective_from=datetime.fromisoformat("2017-07-01T00:00:00+00:00"), topic_tags=["仲裁时效", "中断", "中止"],
            ),
        ]
