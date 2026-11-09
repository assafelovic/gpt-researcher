import logging

from ...arxiv.arxiv import _ID_RE, _paper_id_from_link
from ...pypdf.pypdf import PyPDFScraper


def scrape_pdf_with_pypdf(url, session=None) -> str:
    """Extract PDF text through the same backend as the main scraper."""
    return PyPDFScraper(url, session).scrape()[0]


# Preserve the old helper import without retaining the old dependency.
scrape_pdf_with_pymupdf = scrape_pdf_with_pypdf


def scrape_pdf_with_arxiv(query, session=None) -> str:
    """Resolve an arXiv paper ID, URL or query and extract its PDF with pypdf.

    LangChain's ArxivRetriever loads PDFs with fitz internally; using the
    arxiv client for metadata keeps this browser path independent of PyMuPDF.
    """
    paper_id = _paper_id_from_link(query)
    if not paper_id:
        return ""

    import arxiv

    try:
        search = (
            arxiv.Search(id_list=[paper_id], max_results=1)
            if _ID_RE.fullmatch(paper_id)
            else arxiv.Search(query=query, max_results=1)
        )
        paper = next(arxiv.Client().results(search), None)
        if paper is not None and paper.pdf_url:
            return scrape_pdf_with_pypdf(paper.pdf_url, session)
    except Exception as exc:
        logging.getLogger(__name__).warning("Error loading arXiv PDF %s: %s", query, exc)
    return ""
