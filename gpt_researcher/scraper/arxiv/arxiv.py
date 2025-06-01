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

        # Include the published date and author to provide additional context, 
        # aligning with APA-style formatting in the report.
        context = f"Published: {docs[0].metadata['Published']}; Author: {docs[0].metadata['Authors']}; Content: {docs[0].page_content}"
        image = []

        return context, image, docs[0].metadata["Title"]
