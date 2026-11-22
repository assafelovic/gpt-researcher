from .beautiful_soup.beautiful_soup import BeautifulSoupScraper
from .web_base_loader.web_base_loader import WebBaseLoaderScraper
from .arxiv.arxiv import ArxivScraper
from .pdf.pdf import PDFScraper
from .browser.browser import BrowserScraper
from .browser.nodriver_scraper import NoDriverScraper
from .tavily_extract.tavily_extract import TavilyExtract
from .firecrawl.firecrawl import FireCrawl
from .scraper import Scraper

PyMuPDFScraper = PDFScraper  # Backward-compatible name from before PyMuPDF was dropped. :-)

__all__ = [
    "BeautifulSoupScraper",
    "WebBaseLoaderScraper",
    "ArxivScraper",
    "PDFScraper",
    "PyMuPDFScraper",
    "BrowserScraper",
    "NoDriverScraper",
    "TavilyExtract",
    "Scraper",
    "FireCrawl",
]
