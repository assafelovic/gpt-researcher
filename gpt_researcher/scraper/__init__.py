from __future__ import annotations

from gpt_researcher.scraper.arxiv.arxiv import ArxivScraper
from gpt_researcher.scraper.beautiful_soup.beautiful_soup import BeautifulSoupScraper
from gpt_researcher.scraper.browser.browser import BrowserScraper
from gpt_researcher.scraper.browser.nodriver_scraper import NoDriverScraper
from gpt_researcher.scraper.firecrawl.firecrawl import FireCrawl
from gpt_researcher.scraper.pymupdf.pymupdf import PyMuPDFScraper
from gpt_researcher.scraper.tavily_extract.tavily_extract import TavilyExtract
from gpt_researcher.scraper.web_base_loader.web_base_loader import WebBaseLoaderScraper

__all__ = [
    "ArxivScraper",
    "BeautifulSoupScraper",
    "BrowserScraper",
    "FireCrawl",
    "NoDriverScraper",
    "PyMuPDFScraper",
    "TavilyExtract",
    "WebBaseLoaderScraper",
]
