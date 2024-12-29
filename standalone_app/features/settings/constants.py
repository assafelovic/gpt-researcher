"""Constants for the settings module."""

from __future__ import annotations

from typing import TYPE_CHECKING

from toga.style import Pack
from toga.style.pack import CENTER, COLUMN, ROW  # pyright: ignore[reportPrivateImportUsage]

if TYPE_CHECKING:
    from standalone_app.features.settings.types import BaseConfig

# Default configuration
DEFAULT_CONFIG: BaseConfig = {
    "RETRIEVER": "tavily",
    "EMBEDDING": "openai:text-embedding-3-small",
    "SIMILARITY_THRESHOLD": 0.42,
    "FAST_LLM": "openai:gpt-4o-mini",
    "SMART_LLM": "openai:gpt-4o-2024-11-20",
    "STRATEGIC_LLM": "openai:gpt-4o",  # Can be used with gpt-o1
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

# Color palette
COLORS = {
    "primary": "#007AFF",
    "secondary": "#5856D6",
    "success": "#34C759",
    "danger": "#FF3B30",
    "warning": "#FF9500",
    "info": "#5856D6",
    "light": "#F2F2F7",
    "dark": "#1C1C1E",
    "text": "#000000",
    "text_secondary": "#666666",
    "background": "#F2F2F7",
    "card": "#F2F2F7",
}

# Common styles
STYLES = {
    "main_container": Pack(
        direction=COLUMN,
        padding=5,
        background_color=COLORS["background"],
        flex=1,
    ),
    "card": Pack(
        direction=COLUMN,
        padding=3,
        background_color=COLORS["card"],
        flex=1,
    ),
    "section": Pack(
        direction=COLUMN,
        padding=(0, 0, 6, 0),
    ),
    "section_label": Pack(
        padding=(0, 0, 3, 0),
        font_size=16,
        font_weight="bold",
        color=COLORS["text"],
        flex=1,
    ),
    "row": Pack(
        direction=ROW,
        padding=(0, 0, 6, 0),
        alignment="center",
        flex=1,  # Allow rows to grow
    ),
    "label": Pack(
        padding=(0, 6, 0, 0),
        font_size=14,
        color=COLORS["text"],
        flex=1,
    ),
    "input": Pack(
        flex=1,
        padding=1,
        height=35,
    ),
    "selection": Pack(
        flex=1,
        padding=1,
        height=35,
    ),
    "input_group": Pack(
        direction=ROW,
        padding=0,
        flex=1,
        alignment="center",
    ),
    "button_primary": Pack(
        padding=3,
        background_color=COLORS["primary"],
        color=COLORS["card"],
        font_weight="bold",
        flex=1,
    ),
    "button_secondary": Pack(
        padding=3,
        background_color=COLORS["secondary"],
        color=COLORS["card"],
        font_weight="bold",
        flex=1,
    ),
    "button_success": Pack(
        padding=3,
        background_color=COLORS["success"],
        color=COLORS["card"],
        font_weight="bold",
        flex=1,
    ),
    "button_danger": Pack(
        padding=3,
        background_color=COLORS["danger"],
        color=COLORS["card"],
        font_weight="bold",
        flex=1,
    ),
    "button_warning": Pack(
        padding=3,
        background_color=COLORS["warning"],
        color=COLORS["card"],
        font_weight="bold",
        flex=1,
    ),
    "divider": Pack(
        height=1,
        padding=(3, 0),
        background_color="#E5E5EA",
        flex=1,
    ),
}

# Main app styles
APP_STYLES = {
    **STYLES,
    "main_container": Pack(
        direction=COLUMN,
        padding=20,
        background_color=COLORS["background"],
    ),
    "input_container": Pack(
        direction=ROW,
        padding=5,
        alignment=CENTER,
        background_color=COLORS["card"],
    ),
    "query_input": Pack(
        flex=1,
        padding_right=5,
        width=400,
        height=40,
        padding=10,
        font_size=14,
        background_color=COLORS["background"],
    ),
    "research_button": Pack(
        padding_left=5,
        width=120,
        height=40,
        background_color=COLORS["primary"],
        color=COLORS["card"],
        font_weight="bold",
        font_size=14,
    ),
    "settings_button": Pack(
        padding_left=5,
        width=40,
        height=40,
        background_color=COLORS["background"],
        color=COLORS["text"],
        font_weight="bold",
        font_size=16,
    ),
    "status_label": Pack(
        padding=(10, 5),
        alignment=CENTER,
        font_size=14,
        color=COLORS["text_secondary"],
    ),
    "results_container": Pack(
        flex=1,
        padding=10,
        background_color=COLORS["card"],
    ),
    "results_content": Pack(
        flex=1,
        padding=10,
        height=400,
        font_size=14,
        background_color=COLORS["background"],
    ),
}


# API Provider URLs and test endpoints
API_PROVIDER_URLS = {
    "openai": "https://platform.openai.com/api-keys",
    "tavily": "https://tavily.com/#api-key",
    "anthropic": "https://console.anthropic.com/account/keys",
    "google": "https://console.cloud.google.com/apis/credentials",
    "bing": "https://www.microsoft.com/en-us/bing/apis/bing-web-search-api",
    "searchapi": "https://www.searchapi.io/docs/google",
    "serpapi": "https://serpapi.com/dashboard",
    "serper": "https://serper.dev/api-key",
    "exa": "https://exa.ai/api-access",
    "ncbi": "https://www.ncbi.nlm.nih.gov/account/settings/",
    "langchain": "https://smith.langchain.com/settings",
    "cohere": "https://dashboard.cohere.ai/api-keys",
    "perplexity": "https://docs.perplexity.ai/",
    "huggingface": "https://huggingface.co/settings/tokens",
    "metaphor": "https://dashboard.metaphor.systems/",
    "you": "https://you.com/api/",
    "browserless": "https://cloud.browserless.io/account/",
    "prodia": "https://app.prodia.com/api",
    "arxiv": "https://arxiv.org/help/api/",
}

API_TEST_ENDPOINTS = {
    "openai": "https://api.openai.com/v1/models",
    "tavily": "https://api.tavily.com/search",
    "anthropic": "https://api.anthropic.com/v1/messages",
    "google": "https://www.googleapis.com/customsearch/v1",
    "bing": "https://api.bing.microsoft.com/v7.0/search",
    "searchapi": "https://www.searchapi.io/api/v1/search",
    "serpapi": "https://serpapi.com/search",
    "serper": "https://api.serper.dev/search",
    "exa": "https://api.exa.ai/search",
    "ncbi": "https://eutils.ncbi.nlm.nih.gov/entrez/eutils/esearch.fcgi",
    "langchain": "https://api.smith.langchain.com/runs",
    "cohere": "https://api.cohere.ai/v1/models",
    "perplexity": "https://api.perplexity.ai/chat/completions",
    "huggingface": "https://huggingface.co/api/models",
    "metaphor": "https://api.metaphor.systems/search",
    "you": "https://api.you.com/api/search",
    "browserless": "https://chrome.browserless.io/content",
    "prodia": "https://api.prodia.com/v1/models",
    "arxiv": "http://export.arxiv.org/api/query",
    # Free LLM Provider URLs
    "cloudflare": "https://developers.cloudflare.com/workers-ai/get-started/",
    "groq": "https://console.groq.com/keys",
    "openrouter": "https://openrouter.ai/keys",
    "google_ai_studio": "https://makersuite.google.com/app/apikey",
    "huggingface_serverless": "https://huggingface.co/settings/tokens",
    "ollama": "https://ollama.ai/download",
    "ovh": "https://www.ovhcloud.com/en/public-cloud/ai-tools/",
    "scaleway": "https://console.scaleway.com/project/credentials",
}


class ValidationStatus:
    """Validation status constants for API key inputs."""

    NONE = ""  # Not validated yet
    VALID = "✓"  # Valid API key
    INVALID = "✗"  # Invalid API key
    LOADING = "..."  # Validation in progress
