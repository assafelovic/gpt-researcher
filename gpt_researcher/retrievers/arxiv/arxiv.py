import arxiv


class ArxivSearch:
    """
    Arxiv API Retriever
    """
    def __init__(self, query, area=None, start_date=None, end_date=None):
        self.arxiv = arxiv
        self.query = query
        self.area = area
        self.start_date = start_date.strftime("%Y%m%d") if start_date else None
        self.end_date = end_date.strftime("%Y%m%d") if end_date else None

    def search(self, max_results=5):
        """
        Performs the search
        :param query:
        :param max_results:
        :return:
        """
        arxiv_gen = list(arxiv.Client().results(
        self.arxiv.Search(
            query= self.query +
            " AND " if self.query else "" +
            "(" + self.area + ")" if self.area else "" +
            (" AND submittedDate:[" + self.start_date + "* TO " + self.end_date + "*]" if (self.start_date is not None) and (self.end_date is not None) else ""), 
            max_results=max_results,
            sort_by=arxiv.SortCriterion.SubmittedDate if self.start_date and self.end_date else arxiv.SortCriterion.Relevance,
        ).search))
        
        return arxiv_gen