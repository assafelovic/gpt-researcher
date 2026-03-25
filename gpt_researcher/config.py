"""
GPT Researcher Configuration
默认中文配置
"""

# 默认语言配置
DEFAULT_LANGUAGE = "zh_CN"
DEFAULT_LOCALE = "zh_CN.UTF-8"

# Retriever providers
RETRIEVER_PROVIDER = "tavily"  # Options: tavily, google, bing, serpapi, serper, duckduckgo, searx

# LLM providers
FAST_LLM_PROVIDER = "openai"
FAST_LLM_MODEL = "gpt-4o-mini"
SMART_LLM_PROVIDER = "openai"
SMART_LLM_MODEL = "gpt-4o"

# Embeddings providers
EMBEDDING_PROVIDER = "openai"  # Options: openai, cohere, google, huggingface, azure_openai
