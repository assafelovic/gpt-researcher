from .base import BaseConfig

DEFAULT_CONFIG: BaseConfig = {
    "RETRIEVER": "tavily",
    "EMBEDDING": "openai:text-embedding-3-small",
    "SIMILARITY_THRESHOLD": 0.42,
    "FAST_LLM": "openai:gpt-4o-mini",
    "SMART_LLM": "openai:gpt-4o-2024-11-20",
    "STRATEGIC_LLM": "openai:gpt-4o", # Can be used with gpt-o1
    "FAST_TOKEN_LIMIT": 2000,
    "SMART_TOKEN_LIMIT": 4000,
    "STRATEGIC_TOKEN_LIMIT": 4000,
    "BROWSE_CHUNK_MAX_LENGTH": 8192,
    "CURATE_SOURCES": False,
    "SUMMARY_TOKEN_LIMIT": 700,
    "TEMPERATURE": 0.4,
    "LLM_TEMPERATURE": 0.55,
    "USER_AGENT": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.0.0 Safari/537.36 Edg/119.0.0.0",
    "MAX_SEARCH_RESULTS_PER_QUERY": 5,
    "MEMORY_BACKEND": "local",
    "TOTAL_WORDS": 1000,
    "REPORT_FORMAT": "APA",
    "MAX_ITERATIONS": 4,
    "AGENT_ROLE": None,
    "SCRAPER": "bs",
    "MAX_SUBTOPICS": 3,
    "LANGUAGE": "english",
    "REPORT_SOURCE": "web",
    "DOC_PATH": "./my-docs"
}
