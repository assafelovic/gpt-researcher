from unittest.mock import Mock

from gpt_researcher.scraper.browser.browser import BrowserScraper


class _FailingDriver:
    def quit(self):
        raise RuntimeError("browser already disconnected")


def test_quit_failure_does_not_mask_result_or_skip_cookie_cleanup():
    scraper = BrowserScraper.__new__(BrowserScraper)
    scraper.url = "https://example.com"
    scraper.driver = _FailingDriver()
    scraper.setup_driver = Mock()
    scraper._visit_google_and_save_cookies = Mock()
    scraper._load_saved_cookies = Mock()
    scraper._add_header = Mock()
    scraper.scrape_text_with_selenium = Mock(
        return_value=("page content", [], "Page title")
    )
    scraper._cleanup_cookie_file = Mock()

    result = scraper.scrape()

    assert result == ("page content", [], "Page title")
    scraper._cleanup_cookie_file.assert_called_once_with()
