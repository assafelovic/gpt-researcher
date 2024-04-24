from itertools import islice
from duckduckgo_search import DDGS


class Duckduckgo:
    """
    Duckduckgo API Retriever
    """
    def __init__(self, query):
        self.ddg = DDGS()
        self.query = query

    def search(self, max_results=5):
        """
        Performs the search
        :param query:
        :param max_results:
        :return:
        """
        ddgs_gen = self.ddg.text(self.query, region='wt-wt', max_results=max_results)
        return ddgs_gen