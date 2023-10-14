"""Configuration class to store the state of bools for different scripts access."""
import os

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


def check_config_setup() -> None:
    cfg = Config()
    check_openai_api_key(cfg)
    check_tavily_api_key(cfg)


def check_openai_api_key(cfg) -> None:
    """Check if the OpenAI API key is set in config.py or as an environment variable."""
    if not cfg.openai_api_key:
        print(
            Fore.RED
            + "Please set your OpenAI API key in .env or as an environment variable."
        )
        print("You can get your key from https://platform.openai.com/account/api-keys")
        exit(1)


def check_tavily_api_key(cfg) -> None:
    """Check if the Tavily Search API key is set in config.py or as an environment variable."""
    tavily_api_key = os.getenv("TAVILY_API_KEY")
    if not tavily_api_key and cfg.search_api == "tavily":
        print(
            Fore.RED
            + "Please set your Tavily Search API key in .env or as an environment variable 'TAVILY_API_KEY'.\n"
            + "Alternatively, you can change the 'search_api' value in config.py to 'duckduckgo'"
        )
        print("You can get your key from https://app.tavily.com")
        exit(1)
