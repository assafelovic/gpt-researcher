from langchain_community.retrievers import ArxivRetriever


class ArxivScraper:

    def __init__(self, link, session=None):
        self.link = link
        self.session = session

    def scrape(self):
        """
        The function scrapes relevant documents from Arxiv based on a given link and returns the content
        of the first document.
        
        Returns:
          The code is returning the page content of the first document retrieved by the ArxivRetriever
        for a given query extracted from the link.
        """
        query = self.link.split("/")[-1]
        retriever = ArxivRetriever(load_max_docs=2, doc_content_chars_max=None)
        docs = retriever.invoke(query)

        # ArxivRetriever returns an empty list when the query matches no paper
        # (e.g. a malformed/non-arXiv link or a transient API failure). Indexing
        # docs[0] then raised IndexError and aborted the whole scrape; mirror the
        # other scrapers and degrade to an empty result instead.
        if not docs:
            return "", [], ""

        # Include the published date and author to provide additional context, 
        # aligning with APA-style formatting in the report.
        first = docs[0]
        metadata = first.metadata or {}
        context = (
            f"Published: {metadata.get('Published')}; "
            f"Author: {metadata.get('Authors')}; "
            f"Content: {first.page_content}"
        )
        image = []

        return context, image, metadata.get("Title", "")
