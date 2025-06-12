import arxiv


class ArxivSearch:
    """
    Arxiv API Retriever
    """
    def __init__(self, query, sort='Relevance', query_domains=None):
        self.arxiv = arxiv
        self.query = query
        assert sort in ['Relevance', 'SubmittedDate'], "Invalid sort criterion"
        self.sort = arxiv.SortCriterion.SubmittedDate if sort == 'SubmittedDate' else arxiv.SortCriterion.Relevance
        

    def search(self, max_results=5):
        """
        Performs the search
        :param query:
        :param max_results:
        :return:
        """

        arxiv_gen = list(arxiv.Client().results(
        self.arxiv.Search(
            query= self.query, #+
            max_results=max_results,
            sort_by=self.sort,
        )))

        search_result = []

        for result in arxiv_gen:

            search_result.append({
                "title": result.title,
                "href": result.pdf_url,
                "body": result.summary,
            })
        
        return search_result