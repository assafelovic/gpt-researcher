from gpt_researcher.config.configurations.retrievers_config import RetrieversConfig, VALID_RETRIEVERS
from gpt_researcher.config.configurations.base_config import BaseConfig


class DefaultConfig(BaseConfig):
    VALID_RETRIEVERS: RetrieversConfig


DEFAULT_CONFIG: DefaultConfig = {
    "RETRIEVER": "tavily",
    "EMBEDDING_PROVIDER": "openai",
    "SIMILARITY_THRESHOLD": 0.42,
    "LLM_PROVIDER": "openai",
    "OLLAMA_BASE_URL": None,
    "DEFAULT_LLM_MODEL": "gpt-4o-mini",
    "FAST_LLM_MODEL": "gpt-4o-mini",
    "SMART_LLM_MODEL": "gpt-4o-2024-08-06",
    "FAST_TOKEN_LIMIT": 2000,
    "SMART_TOKEN_LIMIT": 4000,
    "BROWSE_CHUNK_MAX_LENGTH": 8192,
    "SUMMARY_TOKEN_LIMIT": 700,
    "TEMPERATURE": 0.4,
    "LLM_TEMPERATURE": 0.55,
    "USER_AGENT": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.0.0 Safari/537.36 Edg/119.0.0.0",
    "MAX_SEARCH_RESULTS_PER_QUERY": 5,
    "MEMORY_BACKEND": "local",
    "TOTAL_WORDS": 900,
    "REPORT_FORMAT": "APA",
    "MAX_ITERATIONS": 3,
    "AGENT_ROLE": None,
    "SCRAPER": "bs",
    "MAX_SUBTOPICS": 3,
    "REPORT_SOURCE": None,
    "DOC_PATH": "./my-docs",
    "VALID_RETRIEVERS": VALID_RETRIEVERS
}
