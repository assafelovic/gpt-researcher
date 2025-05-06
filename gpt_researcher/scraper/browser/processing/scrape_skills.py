from __future__ import annotations

from langchain_community.document_loaders import PyMuPDFLoader
from langchain_community.retrievers import ArxivRetriever


def scrape_pdf_with_pymupdf(url) -> str:
    """Scrape a pdf with pymupdf.

    Args:
        url (str): The url of the pdf to scrape

    Returns:
        str: The text scraped from the pdf
    """
    loader = PyMuPDFLoader(url)
    doc = loader.load()
    return str(doc)


def scrape_pdf_with_arxiv(
    query: str,
    load_max_docs: int = 2,
    get_full_documents: bool = True,
    arxiv_search: str | None = None,
    arxiv_exceptions: str | None = None,
) -> str:
    """Scrape a pdf with arxiv.

    Default document length of 70000 about ~15 pages or None for no limit.

    Args:
        query (str): The query to search for
        load_max_docs (int): The maximum number of documents to load
        get_full_documents (bool): Whether to return full document text or snippets
        arxiv_search (str | None): The search query to use
        arxiv_exceptions (str | None): The exceptions to use

    Returns:
        str: The text scraped from the pdf
    """
    retriever = ArxivRetriever(
        load_max_docs=load_max_docs,
        get_full_documents=get_full_documents,
        arxiv_search=arxiv_search,
        arxiv_exceptions=arxiv_exceptions,
    )
    docs = retriever.get_relevant_documents(query=query)
    return docs[0].page_content
