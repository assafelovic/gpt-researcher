"""Regression tests for Scraper's anti-bot/word-list content-quality checks.

Authoritative sources were found by search but returned anti-bot/challenge
pages when scraped (Anubis proof-of-work challenges, Cloudflare,
ResearchGate's "Temporarily Unavailable", OpenReview's bot-check) -- and
those challenge pages were then ingested as if they were the article's real
content, since they return HTTP 200 with a real (often large) body, so
neither an exception nor the too-short-content check below catches them.
Separately, raw word-list/vocabulary-dump .txt files (plain lists of
unrelated words, no prose) scrape cleanly and then dominate the returned
context, since they lexically match almost any query.

Two further junk shapes: sub-1KB stub bodies -- a "Documents download
module" UI page (218 bytes), a Cloudflare 520 error page (924 bytes), a
truncated arXiv HTML page (815 bytes) -- all counted as real sources despite
being far too short to be one; and CDN/HTTP error pages whose <title>
states the failure outright (e.g. "520: Web server is returning an unknown
error") even when a padded body clears the length check.

_looks_like_block_page/_looks_like_word_list/_looks_like_error_title are
unit-tested directly; the full extract_data_from_url path is exercised with
a scraper backend replaced by a canned stub, to confirm the method actually
treats a match as a fetch failure (raw_content: None), the same shape it
already returns for too-short content.
"""

import random
import unittest

from gpt_researcher.scraper.scraper import (
    Scraper,
    _looks_like_block_page,
    _looks_like_error_title,
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

    def test_openreview_bot_check_detected(self):
        text = "Verifying your browser — Complete the check below to continue to OpenReview."
        self.assertTrue(_looks_like_block_page(text))

    def test_normal_article_not_detected(self):
        text = "This is a normal article about Catala, a domain-specific language for tax law."
        self.assertFalse(_looks_like_block_page(text))

    def test_case_insensitive(self):
        text = "MAKING SURE YOU'RE NOT A BOT! " * 5
        self.assertTrue(_looks_like_block_page(text))

    def test_generic_phrases_do_not_false_positive_on_ordinary_news(self):
        # Regression: markers must be anchored to their actual source wording,
        # not bare generic phrases a real article can plausibly contain.
        text = (
            "Regional water utility says services will be temporarily "
            'unavailable in the downtown area starting Monday for scheduled '
            'maintenance. "Just a moment, please," the utility spokesperson '
            "said, noting repairs should finish by evening."
        ) * 5
        self.assertFalse(_looks_like_block_page(text))

    def test_marker_beyond_prefix_window_not_detected(self):
        # Block pages are checked via a size-bounded prefix (they're always
        # short); a marker string appearing far into a large legitimate
        # document (e.g. quoting or discussing an anti-bot system) must not
        # retroactively flag the whole thing.
        padding = "Ordinary article content discussing web scraping history. " * 200
        self.assertGreater(len(padding), 5_000)
        text = padding + "This page happens to mention: anubis uses a proof-of-work scheme."
        self.assertFalse(_looks_like_block_page(text))

    def test_marker_within_prefix_window_still_detected(self):
        # Same marker as above, but within the checked prefix -- must still
        # be caught (confirms the prefix limit didn't disable detection
        # entirely).
        text = "anubis uses a proof-of-work scheme. " + ("Padding. " * 10)
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

    def test_legitimate_cjk_prose_not_detected(self):
        # Regression: CJK prose uses fullwidth sentence terminators (。！？),
        # never ASCII ".", "!", "?" -- counting only ASCII punctuation would
        # misclassify any long-form Chinese/Japanese/Korean article as a
        # word list purely for lacking Latin punctuation.
        sentence = "GPT研究员通过将查询分解为子问题、检索来源并综合成引用报告来进行自主网络研究。"
        text = sentence * 6000
        self.assertGreater(len(text), 200_000)
        self.assertFalse(_looks_like_word_list(text))


class LooksLikeErrorTitleTests(unittest.TestCase):
    def test_cloudflare_520_title_detected(self):
        # Real example (issue #20): site-name-prefixed title, not anchored
        # to the start of the string.
        title = "ieu-monitoring.com | 520: Web server is returning an unknown error"
        self.assertTrue(_looks_like_error_title(title))

    def test_case_insensitive(self):
        title = "Example.com | 502: WEB SERVER IS RETURNING an error"
        self.assertTrue(_looks_like_error_title(title))

    def test_empty_title_not_flagged(self):
        self.assertFalse(_looks_like_error_title(""))
        self.assertFalse(_looks_like_error_title(None))

    def test_ui_component_title_not_flagged_by_this_check(self):
        # "Documents download module" is real junk (issue #20) but is
        # caught by the length threshold, not by title wording -- a title
        # naming a UI component isn't safely generalizable without risking
        # false positives on legitimate short titles.
        self.assertFalse(_looks_like_error_title("Documents download module"))

    def test_numbered_legal_title_not_flagged(self):
        # Regression: this tool retrieves EU/regulatory documents, where
        # "Article 404: ..." or "Rule 520: ..." style numbered-provision
        # titles are plausible real content. A generic "starts with 3
        # digits + colon" regex would misfire here; only the specific
        # error-page phrase does the matching.
        title = "Article 404: Requirements for the Placement of Construction Products"
        self.assertFalse(_looks_like_error_title(title))


class ExtractDataFromUrlContentQualityTests(unittest.IsolatedAsyncioTestCase):
    class _StubBackend:
        """Stands in for a real scraper backend (BeautifulSoupScraper, etc.)."""

        def __init__(self, link, session):
            pass

        def scrape(self):
            return self._canned_content, [], self._canned_title

    async def _extract_with_canned_content(self, canned_content: str, canned_title: str = "Stub Title") -> dict:
        scraper = Scraper(urls=["https://example.com"], user_agent="ua", scraper="bs", worker_pool=_FakeWorkerPool())
        stub_cls = type(
            "StubBackend",
            (self._StubBackend,),
            {"_canned_content": canned_content, "_canned_title": canned_title},
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
        text = "This is a normal article about Catala, a domain-specific language for tax law. " * 20
        self.assertGreater(len(text), 1_000)
        result = await self._extract_with_canned_content(text)
        self.assertEqual(result["raw_content"], text)

    async def test_sub_1kb_stub_treated_as_fetch_failure(self):
        # Real examples from issue #20: a 218-byte "Documents download
        # module" UI stub and an 815-byte truncated arXiv page were both
        # counted as sources despite being far too short to be one.
        text = "Documents download module. " * 7  # ~200 chars, well under 1KB
        self.assertLess(len(text), 1_000)
        result = await self._extract_with_canned_content(text, canned_title="Documents download module")
        self.assertIsNone(result["raw_content"])

    async def test_content_just_under_threshold_rejected(self):
        text = "x" * 999
        result = await self._extract_with_canned_content(text)
        self.assertIsNone(result["raw_content"])

    async def test_content_at_threshold_accepted(self):
        text = "x" * 1_000
        result = await self._extract_with_canned_content(text)
        self.assertEqual(result["raw_content"], text)

    async def test_error_titled_page_rejected_even_when_padded_past_length_check(self):
        # A Cloudflare-style error page whose body is padded with footer/
        # branding boilerplate past the length threshold -- the title check
        # must catch it independently of body length.
        padded_body = "Cloudflare Ray ID and performance/security branding footer text. " * 30
        self.assertGreater(len(padded_body), 1_000)
        result = await self._extract_with_canned_content(
            padded_body,
            canned_title="ieu-monitoring.com | 520: Web server is returning an unknown error",
        )
        self.assertIsNone(result["raw_content"])


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
