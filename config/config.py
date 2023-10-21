"""Configuration class to store the state of bools for different scripts access."""
import os
import sys
import openai
from colorama import Fore
from dotenv import load_dotenv

from config.singleton import Singleton

load_dotenv(verbose=True)

class Config(metaclass=Singleton):
    """
    Configuration class to store the state of bools for different scripts access.
    """

    def __init__(self) -> None:
        """Initialize the Config class"""
        self.debug_mode = False
        self.allow_downloads = False

        self.selenium_web_browser = os.getenv("USE_WEB_BROWSER", "chrome")
        self.search_api = os.getenv("SEARCH_API", "tavily")
        self.llm_provider = os.getenv("LLM_PROVIDER", "ChatOpenAI")
        self.fast_llm_model = os.getenv("FAST_LLM_MODEL", "gpt-3.5-turbo-16k")
        self.smart_llm_model = os.getenv("SMART_LLM_MODEL", "gpt-4")
        self.fast_token_limit = int(os.getenv("FAST_TOKEN_LIMIT", 2000))
        self.smart_token_limit = int(os.getenv("SMART_TOKEN_LIMIT", 4000))
        self.browse_chunk_max_length = int(os.getenv("BROWSE_CHUNK_MAX_LENGTH", 8192))
        self.summary_token_limit = int(os.getenv("SUMMARY_TOKEN_LIMIT", 700))

        self.openai_api_key = os.getenv("OPENAI_API_KEY")
        self.temperature = float(os.getenv("TEMPERATURE", "1"))

        self.user_agent = os.getenv(
            "USER_AGENT",
            "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_4) AppleWebKit/537.36"
            " (KHTML, like Gecko) Chrome/83.0.4103.97 Safari/537.36",
        )

        self.memory_backend = os.getenv("MEMORY_BACKEND", "local")
        # Initialize the OpenAI API client
        openai.api_key = self.openai_api_key

    def set_fast_llm_model(self, value: str) -> None:
        """Set the fast LLM model value."""
        self.fast_llm_model = value

    def set_smart_llm_model(self, value: str) -> None:
        """Set the smart LLM model value."""
        self.smart_llm_model = value

    def set_fast_token_limit(self, value: int) -> None:
        """Set the fast token limit value."""
        self.fast_token_limit = value

    def set_smart_token_limit(self, value: int) -> None:
        """Set the smart token limit value."""
        self.smart_token_limit = value

    def set_browse_chunk_max_length(self, value: int) -> None:
        """Set the browse_website command chunk max length value."""
        self.browse_chunk_max_length = value

    def set_openai_api_key(self, value: str) -> None:
        """Set the OpenAI API key value."""
        self.openai_api_key = value

    def set_debug_mode(self, value: bool) -> None:
        """Set the debug mode value."""
        self.debug_mode = value

class APIKeyError(Exception):
    """
    Exception raised when an API key is not set in config.py or as an environment variable.
    """
    def __init__(self, service_name: str):
        self.service_name = service_name

    def __str__(self):
        if self.service_name == "Tavily":
            service_env = "TAVILY_API_KEY"
            link = "https://app.tavily.com"
        elif self.service_name == "GoogleSerp":
            service_env = "SERP_API_KEY"
            link = "https://serper.dev/"
        elif self.service_name == "Google":
            service_env = "Google_API_KEY and GOOGLE_CX"
            link = "https://developers.google.com/custom-search/v1/overview"
        elif self.service_name == "Searx":
            service_env = "SEARX_URL"
            link = "https://searx.space/"
        elif self.service_name == "OpenAI":
            link = "https://platform.openai.com/account/api-keys"
            return (
                Fore.RED
                + "Please set your OpenAI API key in .env or as an environment variable.\n"
                + "You can get your key from https://platform.openai.com/account/api-keys"
            )

        return (
            Fore.RED
            + f"Please set your {self.service_name} API key in .env or as an environment variable '{service_env}'.\n"
            + f"You can get your key from {link} \n"
            + "Alternatively, you can change the 'search_api' value in config.py to 'duckduckgo'."
        )

def check_config_setup() -> None:
    cfg = Config()
    check_openai_api_key(cfg)
    if cfg.search_api == "tavily":
        check_tavily_api_key(cfg)
    elif cfg.search_api == "googleAPI":
        check_google_api_key(cfg)
    elif cfg.search_api == "googleSerp":
        check_serp_api_key(cfg)
    elif cfg.search_api == "searx":
        check_searx_url(cfg)

def check_openai_api_key(cfg) -> None:
    """Check if the OpenAI API key is set in config.py or as an environment variable."""
    if not cfg.openai_api_key:
        raise APIKeyError("OpenAI")

def check_tavily_api_key(cfg) -> None:
    """Check if the Tavily Search API key is set in config.py or as an environment variable."""
    tavily_api_key = os.getenv("TAVILY_API_KEY")
    if not tavily_api_key and cfg.search_api == "tavily":
        raise APIKeyError("Tavily")

def check_google_api_key(cfg) -> None:
    """Check if the Google API key is set in config.py or as an environment variable."""
    google_api_key = os.getenv("GOOGLE_API_KEY")
    google_cx = os.getenv("GOOGLE_CX")
    if not google_api_key and not google_cx and cfg.search_api == "googleAPI":
        raise APIKeyError("Google")

def check_serp_api_key(cfg) -> None:
    """Check if the SERP API key is set in config.py or as an environment variable."""
    serp_api_key = os.getenv("SERP_API_KEY")
    if not serp_api_key and cfg.search_api == "googleSerp":
        raise APIKeyError("GoogleSerp")

def check_searx_url(cfg) -> None:
    """Check if the Searx URL is set in config.py or as an environment variable."""
    searx_url = os.getenv("SEARX_URL")
    if not searx_url and cfg.search_api == "searx":
        raise APIKeyError("Searx")