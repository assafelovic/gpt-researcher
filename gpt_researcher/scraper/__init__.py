from .arxiv.arxiv import ArxivScraper
from .beautiful_soup.beautiful_soup import BeautifulSoupScraper
from .browser.browser import BrowserScraper
from .browser.nodriver_scraper import NoDriverScraper
from .firecrawl.firecrawl import FireCrawl
from .pymupdf.pymupdf import PyMuPDFScraper
from .tavily_extract.tavily_extract import TavilyExtract
from .web_base_loader.web_base_loader import WebBaseLoaderScraper
from .scrapy_scraper.scrapy_scraper import ScrapyScraper

__all__ = [
    "ArxivScraper",
    "BeautifulSoupScraper",
    "BrowserScraper",
    "FireCrawl",
    "NoDriverScraper",
    "PyMuPDFScraper",
    "TavilyExtract",
    "WebBaseLoaderScraper",
    "ScrapyScraper",
]
