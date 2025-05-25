from __future__ import annotations

from typing_extensions import TypedDict


class BaseConfig(TypedDict):
    RETRIEVER: str
    EMBEDDING: str
    EMBEDDING_FALLBACKS: str
    SIMILARITY_THRESHOLD: float
    FAST_LLM: str
    SMART_LLM: str
    STRATEGIC_LLM: str
    FAST_LLM_FALLBACKS: str
    SMART_LLM_FALLBACKS: str
    STRATEGIC_LLM_FALLBACKS: str
    FAST_TOKEN_LIMIT: int
    SMART_TOKEN_LIMIT: int
    STRATEGIC_TOKEN_LIMIT: int
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
    LANGUAGE: str
    AGENT_ROLE: str | None
    SCRAPER: str
    MAX_SUBTOPICS: int
    REPORT_SOURCE: str | None
    DOC_PATH: str
    PROMPT_FAMILY: str
    LLM_KWARGS: dict
    EMBEDDING_KWARGS: dict
    DEEP_RESEARCH_CONCURRENCY: int
    DEEP_RESEARCH_DEPTH: int
    DEEP_RESEARCH_BREADTH: int
