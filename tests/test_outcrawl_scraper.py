"""Tests for the Outcrawl scraper (SCRAPER="outcrawl")."""

import unittest
from unittest.mock import MagicMock, patch

from gpt_researcher.scraper import Outcrawl, Scraper
from gpt_researcher.scraper.outcrawl import outcrawl as outcrawl_module


def _response(status=200, payload=None):
    response = MagicMock()
    response.status_code = status
    response.json.return_value = payload if payload is not None else {}
    return response


class OutcrawlScraperTests(unittest.TestCase):
    def setUp(self):
        env = patch.dict("os.environ", {"OUTCRAWL_API_KEY": "oc-test"})
        env.start()
        self.addCleanup(env.stop)

    def test_missing_api_key_raises(self):
        with patch.dict("os.environ", {}, clear=True):
            with self.assertRaises(Exception) as ctx:
                Outcrawl("https://example.com")
        self.assertIn("OUTCRAWL_API_KEY", str(ctx.exception))

    def test_scrape_returns_markdown_and_title(self):
        payload = {
            "url": "https://example.com/",
            "statusCode": 200,
            "markdown": "# Hello\n\nBody text.",
            "metadata": {"title": "Example Domain"},
        }
        with patch.object(outcrawl_module.requests, "post", return_value=_response(200, payload)) as post:
            content, images, title = Outcrawl("https://example.com").scrape()

        post.assert_called_once_with(
            "https://api.outcrawl.ai/v1/scrape",
            headers={
                "Authorization": "Bearer oc-test",
                "Content-Type": "application/json",
            },
            json={"url": "https://example.com", "formats": ["markdown"]},
            timeout=120,
        )
        self.assertEqual(content, "# Hello\n\nBody text.")
        self.assertEqual(title, "Example Domain")
        self.assertEqual(images, [])

    def test_scrape_works_without_session_and_with_missing_fields(self):
        payload = {"statusCode": 200}
        with patch.object(outcrawl_module.requests, "post", return_value=_response(200, payload)):
            self.assertEqual(Outcrawl("https://example.com", session=None).scrape(), ("", [], ""))

    def test_http_error_returns_empty_result(self):
        with patch.object(outcrawl_module.requests, "post", return_value=_response(401)):
            self.assertEqual(Outcrawl("https://example.com").scrape(), ("", [], ""))

    def test_non_200_page_status_returns_empty_result(self):
        payload = {"statusCode": 404, "markdown": "Not found"}
        with patch.object(outcrawl_module.requests, "post", return_value=_response(200, payload)):
            self.assertEqual(Outcrawl("https://example.com").scrape(), ("", [], ""))

    def test_request_exception_returns_empty_result(self):
        with patch.object(outcrawl_module.requests, "post", side_effect=RuntimeError("boom")):
            self.assertEqual(Outcrawl("https://example.com").scrape(), ("", [], ""))

    def test_image_extraction_uses_session(self):
        payload = {"statusCode": 200, "markdown": "text", "metadata": {"title": "T"}}
        session = MagicMock()
        session.get.return_value = MagicMock(content=b"<html><body><img src='/a.png'></body></html>", encoding="utf-8")
        with patch.object(outcrawl_module.requests, "post", return_value=_response(200, payload)), patch.object(
            outcrawl_module, "get_relevant_images", return_value=["https://example.com/a.png"]
        ):
            _, images, _ = Outcrawl("https://example.com", session=session).scrape()
        self.assertEqual(images, ["https://example.com/a.png"])

    def test_scraper_selects_outcrawl(self):
        s = Scraper(urls=["https://example.com"], user_agent="ua", scraper="outcrawl", worker_pool=None)
        self.assertIs(s.get_scraper("https://example.com/article"), Outcrawl)


if __name__ == "__main__":
    unittest.main()
