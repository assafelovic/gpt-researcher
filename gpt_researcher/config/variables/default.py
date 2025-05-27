from __future__ import annotations

from gpt_researcher.config.variables.base import BaseConfig

DEFAULT_CONFIG: BaseConfig = {
    "RETRIEVER": "tavily",
    "EMBEDDING": "openai:text-embedding-3-small",
    "EMBEDDING_FALLBACKS": "auto",  # Comma-separated list of model names or "auto" for automatic free models
    "SIMILARITY_THRESHOLD": 0.42,
    #    "FAST_LLM": "openrouter:mistralai/mistral-small-3.1-24b-instruct:free",
    #    "SMART_LLM": "openrouter:google/gemini-2.0-flash-exp:free",
    #    "STRATEGIC_LLM": "openrouter:moonshotai/kimi-vl-a3b-thinking:free",
    #    "FAST_LLM": "openai:gpt-4o-mini",
    #    "SMART_LLM": "openai:gpt-4o-2024-11-20",  # Has support for long responses (2k+ words).
    #    "STRATEGIC_LLM": "openai:o3-mini",  # Can be used with gpt-o1 or gpt-o3
    "FAST_LLM": "auto",  # Will use first fallback when empty or "auto"
    "SMART_LLM": "auto",
    "STRATEGIC_LLM": "auto",
    "FAST_LLM_FALLBACKS": "openrouter:mistralai/mistral-small-3.1-24b-instruct:free,openrouter:google/gemma-3n-e4b-it:free,openrouter:mistralai/devstral-small:free,openrouter:meta-llama/llama-4-maverick:free,openrouter:google/gemma-3-27b-it:free,openrouter:shisa-ai/shisa-v2-llama3.3-70b:free,openrouter:meta-llama/llama-3.3-8b-instruct:free,openrouter:google/gemma-3-27b-it:free,openrouter:google/gemma-3-12b-it:free,openrouter:mistralai/mistral-small-3.1-24b-instruct:free,openrouter:mistralai/mistral-small-24b-instruct-2501:free,openrouter:meta-llama/llama-3.1-8b-instruct:free,openrouter:qwen/qwen3-8b:free,openrouter:qwen/qwen-2.5-vl-7b-instruct:free,openrouter:google/gemma-3-4b-it:free,openrouter:opengvlab/internvl3-2b:free,openrouter:google/gemma-2-9b-it:free,openrouter:google/gemma-3-1b-it:free,openrouter:mistralai/mistral-7b-instruct:free,openrouter:qwen/qwen-2.5-7b-instruct:free,openrouter:meta-llama/llama-3.2-11b-vision-instruct:free,openrouter:meta-llama/llama-3.2-3b-instruct:free,openrouter:meta-llama/llama-3.2-1b-instruct:free",
    "SMART_LLM_FALLBACKS": "openrouter:google/gemini-2.0-flash-exp:free,openrouter:qwen/qwen3-235b-a22b:free,openrouter:meta-llama/llama-4-maverick:free,openrouter:qwen/qwen3-32b:free,openrouter:qwen/qwen3-30b-a3b:free,openrouter:deepseek/deepseek-chat:free,openrouter:deepseek/deepseek-v3-base:free,openrouter:meta-llama/llama-3.3-70b-instruct:free,openrouter:deepseek/deepseek-chat-v3-0324:free,openrouter:meta-llama/llama-3.1-405b:free,openrouter:qwen/qwen-2.5-72b-instruct:free,openrouter:qwen/qwen2.5-vl-32b-instruct:free,openrouter:featherless/qwerky-72b:free,openrouter:cognitivecomputations/dolphin3.0-mistral-24b:free,openrouter:nousresearch/deephermes-3-mistral-24b-preview:free,openrouter:deepseek/deepseek-prover-v2:free,openrouter:thudm/glm-z1-32b:free,openrouter:thudm/glm-4-32b:free,openrouter:nvidia/llama-3.1-nemotron-ultra-253b-v1:free,openrouter:nvidia/llama-3.3-nemotron-super-49b-v1:free,openrouter:qwen/qwen2.5-vl-72b-instruct:free,openrouter:rekaai/reka-flash-3:free,openrouter:mistralai/mistral-nemo:free,openrouter:qwen/qwen-2.5-coder-32b-instruct:free",
    "STRATEGIC_LLM_FALLBACKS": "openrouter:tngtech/deepseek-r1t-chimera:free,openrouter:microsoft/mai-ds-r1:free,openrouter:meta-llama/llama-4-scout:free,openrouter:moonshotai/kimi-vl-a3b-thinking:free,openrouter:microsoft/phi-4-reasoning-plus:free,openrouter:microsoft/phi-4-reasoning:free,openrouter:deepseek/deepseek-r1:free,openrouter:deepseek/deepseek-r1-zero:free,openrouter:qwen/qwq-32b:free,openrouter:deepseek/deepseek-r1-distill-llama-70b:free,openrouter:arliai/qwq-32b-arliai-rpr-v1:free,openrouter:cognitivecomputations/dolphin3.0-r1-mistral-24b:free,openrouter:deepseek/deepseek-r1-distill-qwen-32b:free,openrouter:open-r1/olympiccoder-32b:free,openrouter:moonshotai/moonlight-16b-a3b-instruct:free,openrouter:deepseek/deepseek-r1-distill-qwen-14b:free",
    #    "FAST_LLM_FALLBACKS": "auto",  # Comma-separated list of model names or "auto" for automatic free models
    #    "SMART_LLM_FALLBACKS": "auto",  # Comma-separated list of model names or "auto" for automatic free models
    #    "STRATEGIC_LLM_FALLBACKS": "auto",  # Comma-separated list of model names or "auto" for automatic free models
    "FAST_TOKEN_LIMIT": 2000,
    "SMART_TOKEN_LIMIT": 4000,
    "STRATEGIC_TOKEN_LIMIT": 4000,
    "BROWSE_CHUNK_MAX_LENGTH": 8192,
    "CURATE_SOURCES": False,
    "SUMMARY_TOKEN_LIMIT": 700,
    "TEMPERATURE": 0.55,
    "LLM_TEMPERATURE": 0.55,
    "USER_AGENT": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.0.0 Safari/537.36 Edg/119.0.0.0",
    "MAX_SEARCH_RESULTS_PER_QUERY": 5,
    "MEMORY_BACKEND": "local",
    "TOTAL_WORDS": 1200,
    "REPORT_FORMAT": "APA",
    "MAX_ITERATIONS": 4,
    "AGENT_ROLE": None,
    "SCRAPER": "bs",
    "MAX_SCRAPER_WORKERS": 15,
    "MAX_SUBTOPICS": 3,
    "LANGUAGE": "english",
    "REPORT_SOURCE": "web",
    "DOC_PATH": "./my-docs",
    "PROMPT_FAMILY": "default",
    "LLM_KWARGS": {},
    "EMBEDDING_KWARGS": {},
    "VERBOSE": True,
    # Deep research specific settings
    "DEEP_RESEARCH_BREADTH": 3,
    "DEEP_RESEARCH_DEPTH": 2,
    "DEEP_RESEARCH_CONCURRENCY": 4,
    # MCP retriever specific settings
    "MCP_SERVERS": [],  # List of predefined MCP server configurations
    "MCP_AUTO_TOOL_SELECTION": True,  # Whether to automatically select the best tool for a query
    "MCP_ALLOWED_ROOT_PATHS": [],  # List of allowed root paths for local file access
    # RAG (Retrieval-Augmented Generation) settings
    "ENABLE_RAG_REPORT_GENERATION": True,  # Enable RAG-based report generation for large contexts
    "RAG_CHUNK_SIZE": 2000,  # Size of text chunks for vector storage
    "RAG_CHUNK_OVERLAP": 200,  # Overlap between chunks
    "RAG_MAX_CHUNKS_PER_SECTION": 10,  # Maximum chunks to retrieve per report section
}
