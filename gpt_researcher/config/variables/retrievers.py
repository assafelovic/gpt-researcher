from typing_extensions import TypedDict


class RetrieversConfig(TypedDict):
    """Configuration for different retriever types."""
    ARXIV: str
    BING: str
    CUSTOM: str
    DUCKDUCKGO: str
    EXA: str
    GOOGLE: str
    SEARCHAPI: str
    SEARX: str
    SEMANTIC_SCHOLAR: str
    SERPAPI: str
    SERPER: str
    TAVILY: str
    PUBMED_CENTRAL: str


VALID_RETRIEVERS: RetrieversConfig = {
    "ARXIV": "arxiv",
    "BING": "bing",
    "CUSTOM": "custom",
    "DUCKDUCKGO": "duckduckgo",
    "EXA": "exa",
    "GOOGLE": "google",
    "SEARCHAPI": "searchapi",
    "SEARX": "searx",
    "SEMANTIC_SCHOLAR": "semantic_scholar",
    "SERPAPI": "serpapi",
    "SERPER": "serper",
    "TAVILY": "tavily",
    "PUBMED_CENTRAL": "pubmed_central",
}
