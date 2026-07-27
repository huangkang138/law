"""阶段 3.5 官方法源下载、解析与安全边界的无数据库测试。"""

import unittest
import time
from types import SimpleNamespace
from datetime import datetime, timezone

from legal_agent_system.jurisdictions.authority_provider import (
    AuthorityProviderError,
    HttpOfficialSourceClient,
    OfficialCnLaborProvider,
    RetrievedSource,
    _extract_articles,
)
from legal_agent_system.runtime.executor import PolicyToolExecutor
from legal_agent_system.runtime.schemas import ToolResult


class FakeOfficialSourceClient:
    def __init__(self, contents: dict[str, bytes]) -> None:
        self.contents = contents

    def get(self, url: str, _trusted_domains) -> RetrievedSource:
        return RetrievedSource(
            content=self.contents[url], media_type="text/html", final_url=url,
            retrieved_at=datetime(2026, 7, 13, tzinfo=timezone.utc),
            etag='"fixture"', last_modified="Mon, 13 Jul 2026 00:00:00 GMT",
        )


class DigitalHumanStage35AuthorityProviderTest(unittest.TestCase):
    def test_provider_extracts_exact_articles_and_keeps_raw_snapshot(self):
        law = "中华人民共和国劳动争议调解仲裁法 第二十六条前条。第二十七条申请仲裁的时效期间为一年。第二十八条后条。"
        rules = "劳动人事争议仲裁办案规则 第二十五条前条。第二十六条申请仲裁的时效期间为一年。第二十七条主张权利导致时效中断并重新计算。第二十八条因不可抗力不能申请时仲裁时效中止。第二十九条后条。"
        specs = OfficialCnLaborProvider.sources
        added_sources = {
            spec.canonical_url: self._document_for(spec).encode()
            for spec in specs[2:]
        }
        provider = OfficialCnLaborProvider(FakeOfficialSourceClient({
            specs[0].canonical_url: law.encode(), specs[1].canonical_url: rules.encode(),
            **added_sources,
        }))

        payloads = list(provider.fetch())

        self.assertEqual(len(payloads), len(specs))
        self.assertTrue(payloads[0].text.startswith("第二十七条"))
        self.assertNotIn("第二十八条", payloads[0].text)
        self.assertIn("第二十六条", payloads[1].text)
        self.assertIn("第二十八条", payloads[1].text)
        self.assertNotIn("第二十九条", payloads[1].text)
        self.assertEqual(payloads[0].raw_content, law.encode())
        self.assertEqual(len(payloads[0].source_content_hash), 64)
        self.assertNotEqual(payloads[0].version, payloads[0].source_content_hash[:16])
        self.assertIn("第四十七条", payloads[2].text)
        self.assertIn("第五十条", payloads[3].text)

    def test_provider_fails_closed_when_expected_article_is_missing(self):
        specs = OfficialCnLaborProvider.sources
        provider = OfficialCnLaborProvider(FakeOfficialSourceClient({
            specs[0].canonical_url: "中华人民共和国劳动争议调解仲裁法 无正文".encode(),
            specs[1].canonical_url: "劳动人事争议仲裁办案规则 无正文".encode(),
        }))
        with self.assertRaises(AuthorityProviderError):
            list(provider.fetch())

    def test_provider_keeps_successful_sources_and_reports_partial_failures(self):
        spec = OfficialCnLaborProvider.sources[0]
        provider = OfficialCnLaborProvider(FakeOfficialSourceClient({
            spec.canonical_url: self._document_for(spec).encode(),
        }))

        payloads = list(provider.fetch())

        self.assertEqual([item.external_id for item in payloads], [spec.external_id])
        self.assertEqual(len(provider.last_errors), len(OfficialCnLaborProvider.sources) - 1)

    def test_authority_version_ignores_page_chrome_but_tracks_extracted_provision(self):
        spec = OfficialCnLaborProvider.sources[0]
        document = self._document_for(spec)
        first = list(OfficialCnLaborProvider(FakeOfficialSourceClient({
            spec.canonical_url: document.encode(),
        })).fetch())[0]
        second = list(OfficialCnLaborProvider(FakeOfficialSourceClient({
            spec.canonical_url: f"动态导航内容{document}".encode(),
        })).fetch())[0]
        self.assertNotEqual(first.source_content_hash, second.source_content_hash)
        self.assertEqual(first.text, second.text)
        self.assertEqual(first.version, second.version)

    def test_http_client_rejects_non_https_and_untrusted_hosts(self):
        trusted = frozenset({"www.npc.gov.cn"})
        with self.assertRaises(AuthorityProviderError):
            HttpOfficialSourceClient._validate_url("http://www.npc.gov.cn/law", trusted)
        with self.assertRaises(AuthorityProviderError):
            HttpOfficialSourceClient._validate_url("https://example.com/law", trusted)

    def test_article_extraction_skips_toc_and_ignores_inline_article_refs(self):
        text = (
            "中华人民共和国劳动合同法\n"
            "第三十九条\n第四十条\n"
            "第三十九条劳动者存在法定情形时可以解除，正文提及本法第四十条但不能在此截断。\n"
            "第四十条下一条完整正文内容。"
        )

        extracted = _extract_articles(text, ("三十九",))

        self.assertIn("正文提及本法第四十条但不能在此截断", extracted)

    def test_tool_timeout_is_uncertain_and_never_auto_retried(self):
        attempts = []

        def slow_handler(call_id, _arguments, attempt):
            attempts.append(attempt)
            time.sleep(0.05)
            return ToolResult(tool_call_id=call_id, success=True, data={})

        definition = SimpleNamespace(
            input_schema={"required": []}, supported_jurisdictions=["CN"],
            requires_approval=False, max_retries=2, timeout_seconds=0.001,
        )
        result = PolicyToolExecutor().execute(definition, slow_handler, {}, "CN")
        self.assertEqual(result.error_code, "TOOL_TIMEOUT_UNCERTAIN")
        self.assertFalse(result.retryable)
        self.assertEqual(attempts, [1])

    @staticmethod
    def _document_for(spec) -> str:
        articles = "".join(
            f"第{number}条这是用于验证精确条款抽取的测试正文内容。"
            for number in spec.article_numbers
        )
        return f"{spec.title}{articles}第一百条测试结束条款。"


if __name__ == "__main__":
    unittest.main()
