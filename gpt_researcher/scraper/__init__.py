
from .beautiful_soup.beautiful_soup import BeautifulSoupScraper
from .newspaper.newspaper import NewspaperScraper
from .web_base_loader.web_base_loader import WebBaseLoaderScraper
from .arxiv.arxiv import ArxivScraper
from .pymupdf.pymupdf import PyMuPDFScraper

__all__ = [
    "BeautifulSoupScraper",
    "NewspaperScraper",
    "WebBaseLoaderScraper",
    "ArxivScraper",
    "PyMuPDFScraper"
]