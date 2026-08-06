import unittest

from evals.chinese_reliability.source_validator import (
    FetchResponse,
    SourceValidator,
    deduplicate_urls,
    normalize_url,
)


class SourceValidatorTests(unittest.IsolatedAsyncioTestCase):
    def test_normalize_url_removes_tracking_and_fragment_but_keeps_content_query(self):
        url = (
            "HTTPS://Example.COM:443/report/?id=42&utm_source=newsletter"
            "&fbclid=tracking#section"
        )

        self.assertEqual(normalize_url(url), "https://example.com/report?id=42")

    def test_deduplicate_urls_preserves_first_seen_order(self):
        urls = [
            "https://example.com/report?utm_source=a",
            "https://example.com/report#details",
            "https://example.com/other",
        ]

        self.assertEqual(
            deduplicate_urls(urls),
            ["https://example.com/report", "https://example.com/other"],
        )

    async def test_validate_many_classifies_valid_blocked_and_short_pages(self):
        async def fetcher(url: str, timeout_seconds: float) -> FetchResponse:
            if url.endswith("/valid"):
                return FetchResponse(url, 200, b"x" * 250)
            if url.endswith("/blocked"):
                return FetchResponse(url, 403, b"blocked")
            return FetchResponse(url, 200, b"too short")

        validator = SourceValidator(fetcher=fetcher, min_content_bytes=200)
        results = await validator.validate_many(
            [
                "https://example.com/valid",
                "https://example.com/blocked",
                "https://example.com/short",
            ]
        )

        self.assertEqual(
            [result.status for result in results],
            ["valid", "blocked", "invalid"],
        )
        self.assertEqual(results[0].content_length, 250)
        self.assertEqual(results[1].reason, "http_403")
        self.assertEqual(results[2].reason, "content_too_short")

    async def test_validate_many_records_redirected_final_url(self):
        async def fetcher(url: str, timeout_seconds: float) -> FetchResponse:
            return FetchResponse("https://example.com/final", 200, b"y" * 220)

        results = await SourceValidator(fetcher=fetcher).validate_many(
            ["https://example.com/redirect"]
        )

        self.assertEqual(results[0].status, "valid")
        self.assertEqual(results[0].final_url, "https://example.com/final")

    async def test_validate_many_counts_malformed_url_as_invalid(self):
        async def fetcher(url: str, timeout_seconds: float) -> FetchResponse:
            return FetchResponse(url, 200, b"z" * 220)

        results = await SourceValidator(fetcher=fetcher).validate_many(
            ["not-an-absolute-url", "https://example.com/valid"]
        )

        self.assertEqual(len(results), 2)
        self.assertEqual(results[0].status, "invalid")
        self.assertEqual(results[0].reason, "invalid_url")
        self.assertEqual(results[1].status, "valid")


if __name__ == "__main__":
    unittest.main()
