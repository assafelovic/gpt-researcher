"""Select the arXiv backend only for URLs hosted by arXiv."""

import pytest

from gpt_researcher.scraper import ArxivScraper, BeautifulSoupScraper
from gpt_researcher.scraper.scraper import Scraper


@pytest.mark.parametrize(
    "url",
    [
        "https://example.com/articles/arxiv.org/2601.12345",
        "https://example.com/article?source=https://arxiv.org/abs/2601.12345",
        "https://example.com/article#arxiv.org",
        "https://notarxiv.org/abs/2601.12345",
        "https://arxiv.org.example.com/abs/2601.12345",
        "https://arxiv.org@example.com/abs/2601.12345",
        "https://arxiv.org.example.com./abs/2601.12345",
    ],
)
def test_arxiv_mentions_on_other_hosts_use_configured_scraper(url):
    scraper = Scraper([], "test-agent", "bs", worker_pool=None)
    assert scraper.get_scraper(url) is BeautifulSoupScraper


@pytest.mark.parametrize(
    "url",
    [
        "https://arxiv.org/abs/2601.12345",
        "https://export.arxiv.org/abs/2601.12345",
        "https://ARXIV.ORG/abs/2601.12345",
        "https://arxiv.org./abs/2601.12345",
        "https://export.arxiv.org./abs/2601.12345",
    ],
)
def test_arxiv_hostnames_use_arxiv_scraper(url):
    scraper = Scraper([], "test-agent", "bs", worker_pool=None)
    assert scraper.get_scraper(url) is ArxivScraper
