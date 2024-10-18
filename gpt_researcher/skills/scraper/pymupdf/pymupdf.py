from langchain_community.document_loaders import PyMuPDFLoader


class PyMuPDFScraper:

    def __init__(self, link, session=None):
        self.link = link
        self.session = session

    def scrape(self) -> str:
        """
        The `scrape` function uses PyMuPDFLoader to load a document from a given link and returns it as
        a string.
        
        Returns:
          The `scrape` method is returning a string representation of the `doc` object, which is loaded
        using PyMuPDFLoader from the provided link.
        """
        loader = PyMuPDFLoader(self.link)
        doc = loader.load()
        return str(doc)
