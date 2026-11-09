"""Compatibility import for the former PyMuPDF-backed scraper.

Use PyPDFScraper for new code. The legacy name now uses pypdf and does not
require installing PyMuPDF.
"""

from ..pypdf.pypdf import PyPDFScraper

PyMuPDFScraper = PyPDFScraper
