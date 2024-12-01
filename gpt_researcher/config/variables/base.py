from typing import Union
from typing_extensions import TypedDict


class BaseConfig(TypedDict):
    RETRIEVER: str
    EMBEDDING: str
    SIMILARITY_THRESHOLD: float
    FAST_LLM: str
    SMART_LLM: str
    STRATEGIC_LLM: str
    FAST_TOKEN_LIMIT: int
    SMART_TOKEN_LIMIT: int
    BROWSE_CHUNK_MAX_LENGTH: int
    SUMMARY_TOKEN_LIMIT: int
    TEMPERATURE: float
    LLM_TEMPERATURE: float
    USER_AGENT: str
    MAX_SEARCH_RESULTS_PER_QUERY: int
    MEMORY_BACKEND: str
    TOTAL_WORDS: int
    REPORT_FORMAT: str
    CURATE_SOURCES: bool
    MAX_ITERATIONS: int
    AGENT_ROLE: Union[str, None]
    SCRAPER: str
    MAX_SUBTOPICS: int
    REPORT_SOURCE: Union[str, None]
    DOC_PATH: str
