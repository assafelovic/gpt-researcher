from langchain_community.retrievers import ArxivRetriever

from gpt_researcher.scraper.pdf.pdf import PDFScraper


def scrape_pdf(url) -> str:
    """Scrape a pdf

    Args:
        url (str): The url of the pdf to scrape

    Returns:
        str: The text scraped from the pdf
    """
    content, _, _ = PDFScraper(url).scrape()
    return content


def scrape_pdf_with_arxiv(query) -> str:
    """Scrape a pdf with arxiv
    default document length of 70000 about ~15 pages or None for no limit

    Args:
        query (str): The query to search for

    Returns:
        str: The text scraped from the pdf
    """
    retriever = ArxivRetriever(load_max_docs=2, doc_content_chars_max=None)
    docs = retriever.get_relevant_documents(query=query)
    return docs[0].page_content