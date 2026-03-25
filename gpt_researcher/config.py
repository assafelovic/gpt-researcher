"""
GPT Researcher Configuration
默认中文配置
"""

# 默认语言配置
DEFAULT_LANGUAGE = "zh_CN"
DEFAULT_LOCALE = "zh_CN.UTF-8"

# Retriever providers
RETRIEVER_PROVIDER = "duckduckgo"  # Options: tavily, google, bing, serpapi, serper, duckduckgo, searx

# LLM providers
FAST_LLM_PROVIDER = "avian"
FAST_LLM_MODEL = "z-ai/glm-5"
SMART_LLM_PROVIDER = "avian"
SMART_LLM_MODEL = "z-ai/glm-5"

# Embeddings providers
EMBEDDING_PROVIDER = "avian"  # Options: openai, cohere, google, huggingface, azure_openai, avian
