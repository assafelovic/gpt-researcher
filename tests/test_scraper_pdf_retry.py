"""Regression tests for extensionless-PDF detection and retry.

PDFs served from institutional repository download endpoints (DSpace/
EPrints-style, e.g. "scholarspace.manoa.hawaii.edu/bitstreams/<uuid>/
download") have no ".pdf" suffix, so Scraper.get_scraper() routes them to
a text/HTML backend instead of PyMuPDFScraper. That backend has no way to
decode the PDF body and returns its raw bytes (FlateDecode streams, xref
tables, /Annot objects) as if it were real page text -- silently: no
exception, a normal-looking content_length, unusable content.

_looks_like_unextracted_pdf is unit-tested directly; the retry path is
exercised through extract_data_from_url with both the originally-dispatched
backend and PyMuPDFScraper replaced by stubs, to confirm the method
actually retries and recovers, or falls back to a fetch-failure shape if
the retry also fails.
"""

import unittest

from gpt_researcher.scraper.scraper import Scraper, _looks_like_unextracted_pdf


class LooksLikeUnextractedPdfTests(unittest.TestCase):
    def test_pdf_magic_bytes_detected(self):
        self.assertTrue(_looks_like_unextracted_pdf("%PDF-1.4\n%\xe2\xe3\xcf\xd3\n" + "x" * 200))

    def test_structural_tokens_detected(self):
        text = (
            "\xff\xd8V Kg-\xcd\xa5 ... endstream\nendobj\n"
            "38 0 obj\n<< /Type /Annot /BS 3782 0 R /AP 3783 0 R >>\nendobj\n"
            "xref\n0001355793 00000 n trailer\n"
        )
        self.assertTrue(_looks_like_unextracted_pdf(text))

    def test_single_incidental_token_not_flagged(self):
        # A single overlapping word (e.g. an article that happens to
        # mention a "trailer") must not alone trigger this -- it requires
        # at least two independent structural markers.
        text = "The movie trailer was released online ahead of the premiere. " * 10
        self.assertFalse(_looks_like_unextracted_pdf(text))

    def test_normal_prose_not_flagged(self):
        text = "This is a normal article about Catala, a domain-specific language for tax law."
        self.assertFalse(_looks_like_unextracted_pdf(text))


class _NullLogger:
    def warning(self, *a, **k):
        pass

    def info(self, *a, **k):
        pass


class _FakeWorkerPool:
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


class ExtractDataFromUrlPdfRetryTests(unittest.IsolatedAsyncioTestCase):
    """Drives the real extract_data_from_url/_retry_as_pdf path, with
    get_scraper() and the module-level PyMuPDFScraper name replaced by
    stubs -- no real network or PDF parsing involved."""

    PDF_GARBAGE = (
        "\xff\xd8V Kg-\xcd\xa5 ... endstream\nendobj\n"
        "38 0 obj\n<< /Type /Annot /BS 3782 0 R /AP 3783 0 R >>\nendobj\n"
        "xref\n0001355793 00000 n trailer\n"
    ) * 5

    def _scraper(self):
        return Scraper(urls=["https://example.com"], user_agent="ua", scraper="bs", worker_pool=_FakeWorkerPool())

    async def test_retries_and_recovers_via_pymupdf(self):
        scraper = self._scraper()
        scraper.logger = _NullLogger()

        wrong_backend = type(
            "WrongBackend",
            (),
            {
                "__init__": lambda self, link, session: None,
                "scrape": lambda self: (ExtractDataFromUrlPdfRetryTests.PDF_GARBAGE, [], ""),
            },
        )
        clean_pdf_text = "This is the real, cleanly-extracted PDF text. " * 10
        pymupdf_stub = type(
            "PyMuPDFStub",
            (),
            {
                "__init__": lambda self, link, session: None,
                "scrape": lambda self: (clean_pdf_text, [], "Recovered Title"),
            },
        )

        scraper.get_scraper = lambda link: wrong_backend

        import gpt_researcher.scraper.scraper as scraper_module

        original_pymupdf = scraper_module.PyMuPDFScraper
        scraper_module.PyMuPDFScraper = pymupdf_stub
        try:
            result = await scraper.extract_data_from_url("https://repo.example.edu/bitstream/x/download", scraper.session)
        finally:
            scraper_module.PyMuPDFScraper = original_pymupdf

        self.assertEqual(result["raw_content"], clean_pdf_text)
        self.assertEqual(result["title"], "Recovered Title")

    async def test_retry_failure_falls_back_to_fetch_failure_shape(self):
        scraper = self._scraper()
        scraper.logger = _NullLogger()

        wrong_backend = type(
            "WrongBackend",
            (),
            {
                "__init__": lambda self, link, session: None,
                "scrape": lambda self: (ExtractDataFromUrlPdfRetryTests.PDF_GARBAGE, [], ""),
            },
        )
        pymupdf_stub_fails = type(
            "PyMuPDFStubFails",
            (),
            {
                "__init__": lambda self, link, session: None,
                "scrape": lambda self: ("", [], ""),
            },
        )

        scraper.get_scraper = lambda link: wrong_backend

        import gpt_researcher.scraper.scraper as scraper_module

        original_pymupdf = scraper_module.PyMuPDFScraper
        scraper_module.PyMuPDFScraper = pymupdf_stub_fails
        try:
            result = await scraper.extract_data_from_url("https://repo.example.edu/bitstream/x/download", scraper.session)
        finally:
            scraper_module.PyMuPDFScraper = original_pymupdf

        self.assertIsNone(result["raw_content"])

    async def test_legitimate_content_not_retried(self):
        scraper = self._scraper()
        scraper.logger = _NullLogger()

        good_backend = type(
            "GoodBackend",
            (),
            {
                "__init__": lambda self, link, session: None,
                "scrape": lambda self: ("A normal article with real prose content. " * 10, [], "Title"),
            },
        )
        scraper.get_scraper = lambda link: good_backend

        result = await scraper.extract_data_from_url("https://example.com/article", scraper.session)
        self.assertIn("normal article", result["raw_content"])

    async def test_retry_recovering_still_unextracted_pdf_is_rejected(self):
        # PyMuPDFScraper "recovers" >100 chars, but it's still raw PDF
        # structure (e.g. an encrypted or malformed PDF) -- must not be
        # accepted just because it cleared the length check.
        scraper = self._scraper()
        scraper.logger = _NullLogger()

        wrong_backend = type(
            "WrongBackend",
            (),
            {
                "__init__": lambda self, link, session: None,
                "scrape": lambda self: (ExtractDataFromUrlPdfRetryTests.PDF_GARBAGE, [], ""),
            },
        )
        pymupdf_stub_still_garbage = type(
            "PyMuPDFStubStillGarbage",
            (),
            {
                "__init__": lambda self, link, session: None,
                "scrape": lambda self: (ExtractDataFromUrlPdfRetryTests.PDF_GARBAGE, [], "Untitled"),
            },
        )
        scraper.get_scraper = lambda link: wrong_backend

        import gpt_researcher.scraper.scraper as scraper_module

        original_pymupdf = scraper_module.PyMuPDFScraper
        scraper_module.PyMuPDFScraper = pymupdf_stub_still_garbage
        try:
            result = await scraper.extract_data_from_url(
                "https://repo.example.edu/bitstream/x/download", scraper.session
            )
        finally:
            scraper_module.PyMuPDFScraper = original_pymupdf

        self.assertIsNone(result["raw_content"])

    async def test_retry_recovering_block_page_is_rejected(self):
        # The retry can land on an anti-bot page just as easily as the
        # original request did -- must be checked, not just length.
        scraper = self._scraper()
        scraper.logger = _NullLogger()

        wrong_backend = type(
            "WrongBackend",
            (),
            {
                "__init__": lambda self, link, session: None,
                "scrape": lambda self: (ExtractDataFromUrlPdfRetryTests.PDF_GARBAGE, [], ""),
            },
        )
        block_page_text = "Please verify you are a human. " * 20
        pymupdf_stub_block_page = type(
            "PyMuPDFStubBlockPage",
            (),
            {
                "__init__": lambda self, link, session: None,
                "scrape": lambda self: (block_page_text, [], "Untitled"),
            },
        )
        scraper.get_scraper = lambda link: wrong_backend

        import gpt_researcher.scraper.scraper as scraper_module

        original_pymupdf = scraper_module.PyMuPDFScraper
        scraper_module.PyMuPDFScraper = pymupdf_stub_block_page
        try:
            result = await scraper.extract_data_from_url(
                "https://repo.example.edu/bitstream/x/download", scraper.session
            )
        finally:
            scraper_module.PyMuPDFScraper = original_pymupdf

        self.assertIsNone(result["raw_content"])


if __name__ == "__main__":
    unittest.main()
