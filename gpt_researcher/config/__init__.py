from typing import TYPE_CHECKING

from .config import Config

if TYPE_CHECKING:
    from typing_extensions import TypedDict

    class BaseConfig(TypedDict):
        AGENT_ROLE: str | None
        BROWSE_CHUNK_MAX_LENGTH: int
        CURATE_SOURCES: bool
        DOC_PATH: str
        EMBEDDING: str
        FAST_LLM: str
        FAST_TOKEN_LIMIT: int
        LANGUAGE: str
        LLM_TEMPERATURE: float
        MAX_ITERATIONS: int
        MAX_SEARCH_RESULTS_PER_QUERY: int
        MAX_SUBTOPICS: int
        MEMORY_BACKEND: str
        REPORT_FORMAT: str
        REPORT_SOURCE: str | None
        RETRIEVER: str
        SCRAPER: str
        SIMILARITY_THRESHOLD: float
        SMART_LLM: str
        SMART_TOKEN_LIMIT: int
        STRATEGIC_LLM: str
        STRATEGIC_TOKEN_LIMIT: int
        SUMMARY_TOKEN_LIMIT: int
        TEMPERATURE: float
        TOTAL_WORDS: int
        USER_AGENT: str


DefaultConfig = Config.default_config_dict()


__all__ = [
    "BaseConfig",
    "Config",
    "DefaultConfig",
]
