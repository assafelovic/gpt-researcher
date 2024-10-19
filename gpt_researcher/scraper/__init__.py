
from .beautiful_soup.beautiful_soup import BeautifulSoupScraper
from .web_base_loader.web_base_loader import WebBaseLoaderScraper
from .arxiv.arxiv import ArxivScraper
from .pymupdf.pymupdf import PyMuPDFScraper
from .browser.browser import BrowserScraper
from .scraper import Scraper

__all__ = [
    "BeautifulSoupScraper",
    "WebBaseLoaderScraper",
    "ArxivScraper",
    "PyMuPDFScraper",
    "BrowserScraper",
    "Scraper"
]