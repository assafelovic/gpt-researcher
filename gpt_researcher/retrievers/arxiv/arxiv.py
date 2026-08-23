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
        try:
            arxiv_gen = list(arxiv.Client().results(
                self.arxiv.Search(
                    query=self.query,
                    max_results=max_results,
                    sort_by=self.sort,
                )
            ))
        except Exception as e:
            print(f"Error: {e}. Failed fetching arXiv sources. Resulting in empty response.")
            return []

        search_result = []
        for result in arxiv_gen:
            # Incomplete arxiv.Result objects can surface None for title/pdf_url
            # /summary. Skip entries without a usable href; default other fields
            # so a single partial hit cannot crash the normalizer.
            href = getattr(result, "pdf_url", None) or getattr(result, "entry_id", None)
            if not href:
                continue
            title = getattr(result, "title", None) or ""
            body = getattr(result, "summary", None) or ""
            search_result.append({
                "title": title,
                "href": href,
                "body": body,
            })

        return search_result
