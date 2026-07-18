"""Regression tests for Scraper's anti-bot/word-list content-quality checks.

Authoritative sources were found by search but returned anti-bot/challenge
pages when scraped (Anubis proof-of-work challenges, Cloudflare,
ResearchGate's "Temporarily Unavailable") -- and those challenge pages were
then ingested as if they were the article's real content, since they return
HTTP 200 with a real (often large) body, so neither an exception nor the
existing len(content) < 100 check catches them. Separately, raw
word-list/vocabulary-dump .txt files (plain lists of unrelated words, no
prose) scrape cleanly and then dominate the returned context, since they
lexically match almost any query.

_looks_like_block_page/_looks_like_word_list are unit-tested directly; the
full extract_data_from_url path is exercised with a scraper backend
replaced by a canned stub, to confirm the method actually treats a match as
a fetch failure (raw_content: None), the same shape it already returns for
too-short content.
"""

import random
import unittest

from gpt_researcher.scraper.scraper import (
    Scraper,
    _looks_like_block_page,
    _looks_like_word_list,
)


class LooksLikeBlockPageTests(unittest.TestCase):
    def test_anubis_challenge_detected(self):
        text = (
            "Making sure you're not a bot!  Checking your browser. "
            "Anubis uses a Proof-of-Work scheme "
        ) * 20
        self.assertTrue(_looks_like_block_page(text))

    def test_researchgate_unavailable_detected(self):
        text = "ResearchGate - Temporarily Unavailable. We're sorry for the inconvenience." * 10
        self.assertTrue(_looks_like_block_page(text))

    def test_cloudflare_detected(self):
        text = "Attention Required! | Cloudflare\nSorry, you have been blocked."
        self.assertTrue(_looks_like_block_page(text))

    def test_normal_article_not_detected(self):
        text = "This is a normal article about Catala, a domain-specific language for tax law."
        self.assertFalse(_looks_like_block_page(text))

    def test_case_insensitive(self):
        text = "MAKING SURE YOU'RE NOT A BOT! " * 5
        self.assertTrue(_looks_like_block_page(text))


class LooksLikeWordListTests(unittest.TestCase):
    def test_synthetic_word_list_detected(self):
        random.seed(42)
        words = ["".join(random.choices("abcdefghijklmnop", k=random.randint(3, 9))) for _ in range(180_000)]
        text = " ".join(words)
        self.assertGreater(len(text), 1_000_000)
        self.assertTrue(_looks_like_word_list(text))

    def test_legitimate_long_prose_not_detected(self):
        sentence = (
            "GPT Researcher conducts autonomous web research by decomposing a "
            "query into sub-questions, retrieving sources, and synthesizing a "
            "cited report. "
        )
        text = sentence * 3000
        self.assertGreater(len(text), 200_000)
        self.assertFalse(_looks_like_word_list(text))

    def test_short_content_never_flagged(self):
        # Even a short string with zero punctuation must not be flagged --
        # the size threshold guards against false positives on short pages.
        self.assertFalse(_looks_like_word_list("soa tenses kea ashdown 890 autographs"))


class ExtractDataFromUrlContentQualityTests(unittest.IsolatedAsyncioTestCase):
    class _StubBackend:
        """Stands in for a real scraper backend (BeautifulSoupScraper, etc.)."""

        def __init__(self, link, session):
            pass

        def scrape(self):
            return self._canned_content, [], "Stub Title"

    async def _extract_with_canned_content(self, canned_content: str) -> dict:
        scraper = Scraper(urls=["https://example.com"], user_agent="ua", scraper="bs", worker_pool=_FakeWorkerPool())
        stub_cls = type(
            "StubBackend",
            (self._StubBackend,),
            {"_canned_content": canned_content},
        )
        scraper.get_scraper = lambda link: stub_cls
        return await scraper.extract_data_from_url("https://example.com/x", scraper.session)

    async def test_anti_bot_page_treated_as_fetch_failure(self):
        text = (
            "Making sure you're not a bot!  Checking your browser. "
            "Anubis uses a Proof-of-Work scheme "
        ) * 20
        result = await self._extract_with_canned_content(text)
        self.assertIsNone(result["raw_content"])

    async def test_word_list_treated_as_fetch_failure(self):
        random.seed(42)
        words = ["".join(random.choices("abcdefghijklmnop", k=random.randint(3, 9))) for _ in range(180_000)]
        text = " ".join(words)
        result = await self._extract_with_canned_content(text)
        self.assertIsNone(result["raw_content"])

    async def test_legitimate_content_preserved(self):
        text = "This is a normal article about Catala, a domain-specific language for tax law. " * 5
        result = await self._extract_with_canned_content(text)
        self.assertEqual(result["raw_content"], text)


class _FakeWorkerPool:
    """Minimal stand-in: extract_data_from_url only uses throttle()/executor,
    and the stub backend's scrape() runs synchronously and fast enough that
    the real ThreadPoolExecutor isn't needed."""

    class _NullThrottle:
        async def __aenter__(self):
            return self

        async def __aexit__(self, *exc):
            return False

    def throttle(self):
        return self._NullThrottle()

    @property
    def executor(self):
        return None


if __name__ == "__main__":
    unittest.main()
