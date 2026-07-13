"""ArXiv paper scraper using the maintained `arxiv` Client API.

Avoids langchain_community.ArxivRetriever, which still calls the removed
`arxiv.Search.results()` method (broken for arxiv>=2.2).
"""

from __future__ import annotations

import re
from typing import Any


_ID_RE = re.compile(
    r"(?:arxiv\.org/(?:abs|pdf|html)/)?(?P<id>\d{4}\.\d{4,5}(?:v\d+)?|[a-z\-]+/\d{7})(?:\.pdf)?",
    re.IGNORECASE,
)


def _paper_id_from_link(link: str) -> str:
    """Extract an arXiv id from a URL or bare id string."""
    if not link:
        return ""
    m = _ID_RE.search(link.strip())
    if m:
        return m.group("id")
    # last path segment fallback (legacy behavior)
    return link.rstrip("/").split("/")[-1].removesuffix(".pdf")


class ArxivScraper:
    def __init__(self, link, session=None):
        self.link = link
        self.session = session

    def scrape(self):
        """Fetch paper abstract/content via arxiv.Client.

        Returns:
            (context, images, title) matching other scrapers.
        """
        import arxiv

        paper_id = _paper_id_from_link(self.link)
        client = arxiv.Client()
        search = arxiv.Search(id_list=[paper_id], max_results=1)
        try:
            paper = next(client.results(search))
        except StopIteration as exc:
            raise ValueError(f"No arXiv paper found for id {paper_id!r}") from exc

        authors = ", ".join(a.name for a in (paper.authors or []))
        published = paper.published.date().isoformat() if paper.published else ""
        summary = paper.summary or ""
        title = paper.title or paper_id

        context = (
            f"Published: {published}; Author: {authors}; Content: {summary}"
        )
        image: list[Any] = []
        return context, image, title
