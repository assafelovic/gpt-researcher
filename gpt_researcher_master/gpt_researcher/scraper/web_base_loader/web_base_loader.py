
class WebBaseLoaderScraper:

    def __init__(self, link, session=None):
        self.link = link
        self.session = session

    def scrape(self) -> str:
        """
        This Python function scrapes content from a webpage using a WebBaseLoader object and returns the
        concatenated page content.
        
        Returns:
          The `scrape` method is returning a string variable named `content` which contains the
        concatenated page content from the documents loaded by the `WebBaseLoader`. If an exception
        occurs during the process, an error message is printed and an empty string is returned.
        """
        try:
            from langchain_community.document_loaders import WebBaseLoader
            loader = WebBaseLoader(self.link)
            loader.requests_kwargs = {"verify": False}
            docs = loader.load()
            content = ""

            for doc in docs:
                content += doc.page_content

            return content

        except Exception as e:
            print("Error! : " + str(e))
            return ""
