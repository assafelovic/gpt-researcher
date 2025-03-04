from .arxiv.arxiv import ArxivScraper
from .beautiful_soup.beautiful_soup import BeautifulSoupScraper
from .browser.browser import BrowserScraper
from .pymupdf.pymupdf import PyMuPDFScraper
from .scraper import Scraper
from .browser.nodriver_scraper import NoDriverScraper
from .tavily_extract.tavily_extract import TavilyExtract
from .web_base_loader.web_base_loader import WebBaseLoaderScraper
from .firecrawl.firecrawl import FireCrawl

__all__ = [
    "ArxivScraper",
    "BeautifulSoupScraper",
    "BrowserScraper",
    "FireCrawl",
    "NoDriverScraper",
    "PyMuPDFScraper",
    "Scraper",
    "TavilyExtract",
    "WebBaseLoaderScraper",
]
