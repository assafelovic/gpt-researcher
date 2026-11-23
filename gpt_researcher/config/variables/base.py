from typing import Union, List, Dict, Any
from typing_extensions import TypedDict


class BaseConfig(TypedDict):
    RETRIEVER: str
    EMBEDDING: str
    SIMILARITY_THRESHOLD: float
    CONTEXT_FILTER: str
    FAST_LLM: str
    SMART_LLM: str
    STRATEGIC_LLM: str
    FAST_TOKEN_LIMIT: int
    SMART_TOKEN_LIMIT: int
    STRATEGIC_TOKEN_LIMIT: int
    BROWSE_CHUNK_MAX_LENGTH: int
    SUMMARY_TOKEN_LIMIT: int
    TEMPERATURE: float
    USER_AGENT: str
    MAX_SEARCH_RESULTS_PER_QUERY: int
    MEMORY_BACKEND: str
    TOTAL_WORDS: int
    REPORT_FORMAT: str
    CURATE_SOURCES: bool
    MAX_ITERATIONS: int
    LANGUAGE: str
    AGENT_ROLE: Union[str, None]
    SCRAPER: str
    MAX_SCRAPER_WORKERS: int
    SCRAPER_RATE_LIMIT_DELAY: float
    MAX_SUBTOPICS: int
    REPORT_SOURCE: Union[str, None]
    DOC_PATH: str
    PROMPT_FAMILY: str
    LLM_KWARGS: dict
    EMBEDDING_KWARGS: dict
    VERBOSE: bool
    DEEP_RESEARCH_CONCURRENCY: int
    DEEP_RESEARCH_DEPTH: int
    DEEP_RESEARCH_BREADTH: int
    MCP_SERVERS: List[Dict[str, Any]]
    MCP_AUTO_TOOL_SELECTION: bool
    MCP_USE_LLM_ARGS: bool
    MCP_ALLOWED_ROOT_PATHS: List[str]
    MCP_STRATEGY: str
    REASONING_EFFORT: str
    # Image generation settings
    IMAGE_GENERATION_MODEL: Union[str, None]
    IMAGE_GENERATION_MAX_IMAGES: int
    IMAGE_GENERATION_ENABLED: bool
    IMAGE_GENERATION_STYLE: str  # Image style: "dark", "light", or "auto"
    IMAGE_GENERATION_PROVIDER: str  # Image provider: "google" or "modelslab"

    # Vision / image understanding settings (inject VLM caption/OCR of
    # scraped images into the research context)
    VISION_ENABLED: bool
    VISION_LLM: str  # provider:model, e.g. "openai:gpt-5.4-mini"
    VISION_MAX_IMAGES: int
    VISION_MAX_IMAGES_PER_SOURCE: int
    VISION_MAX_IMAGE_BYTES: int
    VISION_TIMEOUT: float
    VISION_EMBED_IN_CONTEXT: bool