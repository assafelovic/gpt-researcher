from .base import BaseConfig

DEFAULT_CONFIG: BaseConfig = {
    "RETRIEVER": "tavily",
    "EMBEDDING": "openai:text-embedding-3-large",
    "SIMILARITY_THRESHOLD": 0.42,
    "FAST_LLM": "openai:gpt-4.1-mini",
    "SMART_LLM": "openai:gpt-4.1",  # Has support for long responses (2k+ words).
    "STRATEGIC_LLM": "openai:o4-mini",  # Can be used with o1 or o3, please note it will make tasks slower.
    "FAST_TOKEN_LIMIT": 65536,
    "SMART_TOKEN_LIMIT": 65536,
    "STRATEGIC_TOKEN_LIMIT": 65536,
    "BROWSE_CHUNK_MAX_LENGTH": 8192,
    "CURATE_SOURCES": False,
    "SUMMARY_TOKEN_LIMIT": 1500,
    "TEMPERATURE": 0.5,
    "USER_AGENT": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.0.0 Safari/537.36 Edg/119.0.0.0",
    "MAX_SEARCH_RESULTS_PER_QUERY": 10,
    "MEMORY_BACKEND": "local",
    "TOTAL_WORDS": 40000,
    "REPORT_FORMAT": "APA",
    "MAX_ITERATIONS": 10,
    "AGENT_ROLE": None,
    "SCRAPER": "bs",
    "MAX_SCRAPER_WORKERS": 30,
    "MAX_SUBTOPICS": 6,
    "LANGUAGE": "english",
    "REPORT_SOURCE": "web",
    "DOC_PATH": "./my-docs",
    # Deep research specific settings
    "DEEP_RESEARCH_BREADTH": 6,
    "DEEP_RESEARCH_DEPTH": 3,
    "DEEP_RESEARCH_CONCURRENCY": 10,
}
