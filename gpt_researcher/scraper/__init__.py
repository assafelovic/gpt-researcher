from __future__ import annotations

from .arxiv.arxiv import ArxivScraper
from .beautiful_soup.beautiful_soup import BeautifulSoupScraper
from .browser.browser import BrowserScraper
from .pymupdf.pymupdf import PyMuPDFScraper
from .scraper import Scraper
from .tavily_extract.tavily_extract import TavilyExtract
from .web_base_loader.web_base_loader import WebBaseLoaderScraper

__all__ = [
    "BeautifulSoupScraper",
    "WebBaseLoaderScraper",
    "ArxivScraper",
    "PyMuPDFScraper",
    "BrowserScraper",
    "TavilyExtract",
    "Scraper",
]
