from __future__ import annotations

import json
import os
import warnings
from contextlib import suppress
from datetime import timedelta
from typing import Any, ClassVar, Dict, List, Self, Union, get_args, get_origin

# Import fallback logic from the new module
from gpt_researcher.config.fallback_logic import set_llm_attributes
from gpt_researcher.config.variables.base import BaseConfig
from gpt_researcher.config.variables.default import DEFAULT_CONFIG
from gpt_researcher.llm_provider import GenericLLMProvider
from gpt_researcher.llm_provider.generic.base import ReasoningEfforts
from gpt_researcher.retrievers.utils import get_all_retriever_names

with suppress(ImportError):
    from litellm import _logging  # pyright: ignore[reportMissingImports]
    _logging._turn_on_debug()


def _log_config_section(
    section_name: str,
    message: str,
    level: str = "INFO",
    verbose: bool = True,
) -> None:
    """Helper function for consistent config logging."""
    if not verbose:
        return
    from colorama import Fore, Style
    colors: dict[str, str] = {
        "DEBUG": Fore.LIGHTBLACK_EX,
        "INFO": Fore.CYAN,
        "WARN": Fore.YELLOW,
        "ERROR": Fore.RED,
        "SUCCESS": Fore.GREEN,
    }
    color: str = colors.get(level, Fore.WHITE)
    print(f"{color}[{level}] {section_name}: {message}{Style.RESET_ALL}")


class Config:
    """Config class for GPT Researcher."""

    CONFIG_DIR: ClassVar[str] = os.path.join(os.path.dirname(__file__), "variables")
    DefaultConfig: ClassVar[Self] | None = None

    # Class-level caching for fallback providers
    _cached_fast_llm_fallback_providers: ClassVar[list[GenericLLMProvider]] = []
    _cached_smart_llm_fallback_providers: ClassVar[list[GenericLLMProvider]] = []
    _cached_strategic_llm_fallback_providers: ClassVar[list[GenericLLMProvider]] = []
    _fallbacks_initialized: ClassVar[bool] = False

    def __new__(cls, *args, **kwargs) -> Self:
        if cls.DefaultConfig is None:
            cls.DefaultConfig = super().__new__(cls)
        if not args and not kwargs:
            return cls.DefaultConfig
        if args and args[0] == "default":
            return cls.DefaultConfig
        if kwargs and kwargs.get("config_path") == "default":
            return cls.DefaultConfig
        return super().__new__(cls)

    def __init__(
        self,
        config_path: str | None = None,
    ):
        """Initialize the config class."""
        self.config_path: str | None = config_path

        # Initialize lists for instantiated fallback providers
        self.fast_llm_fallback_providers: list[GenericLLMProvider] = []
        self.smart_llm_fallback_providers: list[GenericLLMProvider] = []
        self.strategic_llm_fallback_providers: list[GenericLLMProvider] = []

        # Initialize private attributes for LLM configurations
        self._smart_llm: str = ""
        self._smart_llm_model: str | None = None
        self._smart_llm_provider: str | None = None
        self._fast_llm: str = ""
        self._fast_llm_model: str | None = None
        self._fast_llm_provider: str | None = None
        self._strategic_llm: str = ""
        self._strategic_llm_model: str | None = None
        self._strategic_llm_provider: str | None = None

        config_to_use: BaseConfig = self.load_config(config_path)
        self._set_attributes(config_to_use)
        self._set_embedding_attributes()
        set_llm_attributes(self)
        self._handle_deprecated_attributes()
        if config_to_use["REPORT_SOURCE"] != "web":
            self._set_doc_path(config_to_use)

        # MCP support configuration
        self.mcp_servers: list[str] = config_to_use.get("MCP_SERVERS", [])

        # Allowed root paths for MCP servers
        self.mcp_allowed_root_paths: list[str] = config_to_use.get("MCP_ALLOWED_ROOT_PATHS", []) or []

    # Smart LLM properties
    @property
    def smart_llm(self) -> str:
        """Get the smart LLM configuration."""
        return self._smart_llm

    @smart_llm.setter
    def smart_llm(self, value: str) -> None:
        """Set the smart LLM configuration."""
        self._smart_llm = value
        self._smart_llm_provider, self._smart_llm_model = self.parse_llm(value)

    @property
    def smart_llm_model(self) -> str | None:
        """Get the smart LLM model."""
        return self._smart_llm_model

    @smart_llm_model.setter
    def smart_llm_model(self, value: str | None) -> None:
        """Set the smart LLM model."""
        self._smart_llm_model = value
        if self._smart_llm_provider and value:
            self._smart_llm = f"{self._smart_llm_provider}:{value}"
        elif not value:
            self._smart_llm = ""

    @property
    def smart_llm_provider(self) -> str | None:
        """Get the smart LLM provider."""
        return self._smart_llm_provider

    @smart_llm_provider.setter
    def smart_llm_provider(self, value: str | None) -> None:
        """Set the smart LLM provider."""
        self._smart_llm_provider = value
        if value and self._smart_llm_model:
            self._smart_llm = f"{value}:{self._smart_llm_model}"
        elif not value:
            self._smart_llm = ""

    # Fast LLM properties
    @property
    def fast_llm(self) -> str:
        """Get the fast LLM configuration."""
        return self._fast_llm

    @fast_llm.setter
    def fast_llm(self, value: str) -> None:
        """Set the fast LLM configuration."""
        self._fast_llm = value
        self._fast_llm_provider, self._fast_llm_model = self.parse_llm(value)

    @property
    def fast_llm_model(self) -> str | None:
        """Get the fast LLM model."""
        return self._fast_llm_model

    @fast_llm_model.setter
    def fast_llm_model(self, value: str | None) -> None:
        """Set the fast LLM model."""
        self._fast_llm_model = value
        if self._fast_llm_provider and value:
            self._fast_llm = f"{self._fast_llm_provider}:{value}"
        elif not value:
            self._fast_llm = ""

    @property
    def fast_llm_provider(self) -> str | None:
        """Get the fast LLM provider."""
        return self._fast_llm_provider

    @fast_llm_provider.setter
    def fast_llm_provider(self, value: str | None) -> None:
        """Set the fast LLM provider."""
        self._fast_llm_provider = value
        if value and self._fast_llm_model:
            self._fast_llm = f"{value}:{self._fast_llm_model}"
        elif not value:
            self._fast_llm = ""

    # Strategic LLM properties
    @property
    def strategic_llm(self) -> str:
        """Get the strategic LLM configuration."""
        return self._strategic_llm

    @strategic_llm.setter
    def strategic_llm(self, value: str) -> None:
        """Set the strategic LLM configuration."""
        self._strategic_llm = value
        self._strategic_llm_provider, self._strategic_llm_model = self.parse_llm(value)

    @property
    def strategic_llm_model(self) -> str | None:
        """Get the strategic LLM model."""
        return self._strategic_llm_model

    @strategic_llm_model.setter
    def strategic_llm_model(self, value: str | None) -> None:
        """Set the strategic LLM model."""
        self._strategic_llm_model = value
        if self._strategic_llm_provider and value:
            self._strategic_llm = f"{self._strategic_llm_provider}:{value}"
        elif not value:
            self._strategic_llm = ""

    @property
    def strategic_llm_provider(self) -> str | None:
        """Get the strategic LLM provider."""
        return self._strategic_llm_provider

    @strategic_llm_provider.setter
    def strategic_llm_provider(self, value: str | None) -> None:
        """Set the strategic LLM provider."""
        self._strategic_llm_provider = value
        if value and self._strategic_llm_model:
            self._strategic_llm = f"{value}:{self._strategic_llm_model}"
        elif not value:
            self._strategic_llm = ""

    def _parse_default_config(self) -> None:
        self.embedding_kwargs: dict[str, Any] = DEFAULT_CONFIG.get("EMBEDDING_KWARGS", {}) or {}
        self.agent_role: str | None = DEFAULT_CONFIG.get("AGENT_ROLE", None) or None
        self.browse_chunk_max_length: int = DEFAULT_CONFIG.get("BROWSE_CHUNK_MAX_LENGTH", 8192) or 8192
        self.cache_expiry_time: timedelta = DEFAULT_CONFIG.get("CACHE_EXPIRY_TIME", timedelta(days=2)) or timedelta(days=2)
        self.curate_sources: bool = DEFAULT_CONFIG.get("CURATE_SOURCES", False) or False
        self.deep_research_breadth: int = DEFAULT_CONFIG.get("DEEP_RESEARCH_BREADTH", 3) or 3
        self.deep_research_concurrency: int = DEFAULT_CONFIG.get("DEEP_RESEARCH_CONCURRENCY", 4) or 4
        self.deep_research_depth: int = DEFAULT_CONFIG.get("DEEP_RESEARCH_DEPTH", 2) or 2
        self.doc_path: str = DEFAULT_CONFIG.get("DOC_PATH", "./my-docs") or "./my-docs"
        self.language: str = DEFAULT_CONFIG.get("LANGUAGE", "english") or "english"
        self.max_iterations: int = DEFAULT_CONFIG.get("MAX_ITERATIONS", 3) or 3
        self.max_scraper_workers: int = DEFAULT_CONFIG.get("MAX_SCRAPER_WORKERS", 15) or 15
        self.max_search_results_per_query: int = DEFAULT_CONFIG.get("MAX_SEARCH_RESULTS_PER_QUERY", 5) or 5
        self.max_subtopics: int = DEFAULT_CONFIG.get("MAX_SUBTOPICS", 3) or 3
        self.prompt_family: str = DEFAULT_CONFIG.get("PROMPT_FAMILY", "default") or "default"
        self.report_format: str = DEFAULT_CONFIG.get("REPORT_FORMAT", "APA") or "APA"
        self.report_source: str = DEFAULT_CONFIG.get("REPORT_SOURCE", "web") or "web"
        # Handle RETRIEVER with default value
        retriever_env: str = os.environ.get("RETRIEVER", DEFAULT_CONFIG.get("RETRIEVER", "tavily")) or "tavily"
        try:
            self.retrievers: list[str] = self.parse_retrievers(retriever_env)
        except ValueError as e:
            print(f"Warning: {e.__class__.__name__}: {e}. Defaulting to 'tavily' retriever.")
            self.retrievers = ["tavily"]
        self.scraper: str = DEFAULT_CONFIG.get("SCRAPER", "bs") or "bs"
        self.similarity_threshold: float = DEFAULT_CONFIG.get("SIMILARITY_THRESHOLD", 0.42) or 0.42
        self.total_words: int = DEFAULT_CONFIG.get("TOTAL_WORDS", 1200) or 1200
        self.user_agent: str = (
            DEFAULT_CONFIG.get(
                "USER_AGENT",
                "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.0.0 Safari/537.36 Edg/119.0.0.0",
            )
            or "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.0.0 Safari/537.36 Edg/119.0.0.0"
        )
        self.verbose: bool = DEFAULT_CONFIG.get("VERBOSE", True) or True

        self.mcp_allowed_root_paths: list[str] = DEFAULT_CONFIG.get("MCP_ALLOWED_ROOT_PATHS", []) or []
        self.mcp_auto_tool_selection: bool = DEFAULT_CONFIG.get("MCP_AUTO_TOOL_SELECTION", True) or True
        self.mcp_servers: list[str] = DEFAULT_CONFIG.get("MCP_SERVERS", []) or []

        self.memory_backend: str = DEFAULT_CONFIG.get("MEMORY_BACKEND", "local") or "local"
        self.embedding_fallback_list: list[str] | str = DEFAULT_CONFIG.get("EMBEDDING_FALLBACKS", "auto") or "auto"
        self.embedding: str = DEFAULT_CONFIG.get("EMBEDDING", "openai:text-embedding-3-small") or "openai:text-embedding-3-small"

        self.fast_llm_fallbacks: list[str] | str = DEFAULT_CONFIG.get("FAST_LLM_FALLBACKS", "auto") or "auto"
        self.fast_llm = DEFAULT_CONFIG.get("FAST_LLM", "") or ""
        self.fast_token_limit: int = DEFAULT_CONFIG.get("FAST_TOKEN_LIMIT", 3000) or 3000
        self.smart_llm_fallbacks: list[str] | str = DEFAULT_CONFIG.get("SMART_LLM_FALLBACKS", "auto") or "auto"
        self.smart_llm = DEFAULT_CONFIG.get("SMART_LLM", "") or ""
        self.smart_token_limit: int = DEFAULT_CONFIG.get("SMART_TOKEN_LIMIT", 6000) or 6000
        self.strategic_llm_fallbacks: list[str] | str = DEFAULT_CONFIG.get("STRATEGIC_LLM_FALLBACKS", "auto") or "auto"
        self.strategic_llm = DEFAULT_CONFIG.get("STRATEGIC_LLM", "") or ""
        self.strategic_token_limit: int = DEFAULT_CONFIG.get("STRATEGIC_TOKEN_LIMIT", 4000) or 4000

        self.llm_kwargs: dict[str, Any] = DEFAULT_CONFIG.get("LLM_KWARGS", {}) or {}
        self.llm_temperature: float = DEFAULT_CONFIG.get("LLM_TEMPERATURE", 0.55) or 0.55
        self.summary_token_limit: int = DEFAULT_CONFIG.get("SUMMARY_TOKEN_LIMIT", 700) or 700
        self.temperature: float = DEFAULT_CONFIG.get("TEMPERATURE", 0.4) or 0.4

    def _set_attributes(
        self,
        config: dict[str, Any] | BaseConfig,
    ) -> None:
        self._parse_default_config()
        for key, value in config.items():
            env_value: str | None = os.getenv(key)
            if env_value is not None:
                # Handle ForwardRef objects from __future__ annotations
                type_hint = BaseConfig.__annotations__.get(key)
                if type_hint is not None:
                    # Resolve ForwardRef if needed
                    if hasattr(type_hint, "__forward_arg__"):  # ForwardRef object
                        # Get the string representation and try to resolve it
                        try:
                            import typing
                            if hasattr(typing, "get_type_hints"):
                                resolved_hints: dict[str, Any] = typing.get_type_hints(BaseConfig)
                                type_hint: Any = resolved_hints.get(key, str)  # Default to str if not found
                            else:
                                type_hint = str  # Fallback to str
                        except (NameError, AttributeError, TypeError):
                            type_hint = str  # Fallback to str if resolution fails

                    value: Any = self.convert_env_value(key, env_value, type_hint)
                else:
                    # If no type hint found, keep the env_value as string
                    value = env_value
            setattr(self, key.casefold(), value)

    def _set_embedding_attributes(self) -> None:
        self.embedding_provider, self.embedding_model = self.parse_embedding(self.embedding)
        self.embedding_fallback_list = []

    def _handle_deprecated_attributes(self) -> None:
        if os.getenv("EMBEDDING_PROVIDER") is not None:
            warnings.warn(
                "EMBEDDING_PROVIDER is deprecated and will be removed soon. Use EMBEDDING instead.",
                FutureWarning,
                stacklevel=2,
            )
            self.embedding_provider: str | None = (os.environ["EMBEDDING_PROVIDER"] or self.embedding_provider or "").strip() or None

            match os.environ["EMBEDDING_PROVIDER"]:
                case "ollama":
                    self.embedding_model: str | None = (os.environ["OLLAMA_EMBEDDING_MODEL"] or "").strip() or None
                case "custom":
                    self.embedding_model = (os.environ["OPENAI_EMBEDDING_MODEL"] or "").strip() or None
                case "openai":
                    self.embedding_model = "text-embedding-3-large"
                case "azure_openai":
                    self.embedding_model = "text-embedding-3-large"
                case "huggingface":
                    self.embedding_model = "sentence-transformers/all-MiniLM-L6-v2"
                case "gigachat":
                    self.embedding_model = "Embeddings"
                case "google_genai":
                    self.embedding_model = "text-embedding-004"
                case _:
                    raise Exception("Embedding provider not found.")

        _deprecation_warning = "LLM_PROVIDER, FAST_LLM_MODEL and SMART_LLM_MODEL are deprecated and will be removed soon. Use FAST_LLM and SMART_LLM instead."
        if os.getenv("LLM_PROVIDER") is not None:
            warnings.warn(_deprecation_warning, FutureWarning, stacklevel=2)
            self.fast_llm_provider = (os.environ["LLM_PROVIDER"] or self.fast_llm_provider or "").strip()
            self.smart_llm_provider = (os.environ["LLM_PROVIDER"] or self.smart_llm_provider or "").strip()
            self.strategic_llm_provider = (os.environ["LLM_PROVIDER"] or self.strategic_llm_provider or "").strip()
        if os.getenv("FAST_LLM_MODEL") is not None:
            warnings.warn(_deprecation_warning, FutureWarning, stacklevel=2)
            self.fast_llm_model = (os.environ["FAST_LLM_MODEL"] or self.fast_llm_model or "").strip() or None
        if os.getenv("SMART_LLM_MODEL") is not None:
            warnings.warn(_deprecation_warning, FutureWarning, stacklevel=2)
            self.smart_llm_model = (os.environ["SMART_LLM_MODEL"] or self.smart_llm_model or "").strip() or None
        if os.getenv("STRATEGIC_LLM_MODEL") is not None:
            warnings.warn(_deprecation_warning, FutureWarning, stacklevel=2)
            self.strategic_llm_model = (os.environ["STRATEGIC_LLM_MODEL"] or self.strategic_llm_model or "").strip() or None

    def _set_doc_path(self, config: dict[str, Any] | BaseConfig) -> None:
        self.doc_path: str = config["DOC_PATH"]
        if self.doc_path and self.doc_path.strip():
            try:
                self.validate_doc_path()
                _log_config_section("DOC PATH", f"Document path validated: '{self.doc_path}'")
            except Exception as e:
                _log_config_section("DOC PATH", f"Error validating doc_path: {e.__class__.__name__}: {e}. Using default", "WARN")
                self.doc_path = DEFAULT_CONFIG["DOC_PATH"]

    @classmethod
    def load_config(cls, config_path: str | None) -> BaseConfig:
        """Load a configuration by name."""
        # Merge with default config to ensure all keys are present
        copied_default_cfg: BaseConfig | dict[str, Any] = DEFAULT_CONFIG.copy()

        if config_path is None or not config_path.strip():
            _log_config_section("CONFIG", "No config file specified, using defaults", "WARN")
            return copied_default_cfg

        # config_path = os.path.join(cls.CONFIG_DIR, config_path)
        if not os.path.exists(config_path):
            if config_path.strip().casefold() != "default":
                _log_config_section("CONFIG", f"Configuration not found at '{config_path}', using defaults", "WARN")
                if not config_path.casefold().endswith(".json"):
                    _log_config_section("CONFIG", f"Did you mean: '{config_path}.json'?")
            return copied_default_cfg

        with open(config_path, "r") as f:
            _log_config_section("CONFIG", f"Loading configuration from '{os.path.abspath(config_path)}'", "SUCCESS")
            custom_config_cfg = json.load(f)

        copied_default_cfg.update(custom_config_cfg)
        return copied_default_cfg

    @classmethod
    def list_available_configs(cls) -> list[str]:
        """List all available configuration names."""
        configs: list[str] = ["default"]
        for file in os.listdir(cls.CONFIG_DIR):
            if file.casefold().endswith(".json"):
                configs.append(file[:-5])  # Remove .json extension
        return configs

    def parse_retrievers(self, retriever_str: str) -> list[str]:
        """Parse the retriever string into a list of retrievers and validate them."""
        retrievers: list[str] = [retriever.strip() for retriever in retriever_str.strip().split(",")]
        valid_retrievers: list[Any] = get_all_retriever_names() or []
        invalid_retrievers: list[str] = [r for r in retrievers if r not in valid_retrievers]
        if invalid_retrievers:
            raise ValueError(f"Invalid retriever(s) found: {', '.join(invalid_retrievers)}. Valid options are: {', '.join(valid_retrievers)}.")
        return retrievers

    @staticmethod
    def parse_llm(llm_str: str | None) -> tuple[str | None, str | None]:
        """Parse llm string into (llm_provider, llm_model)."""
        from gpt_researcher.llm_provider.generic.base import (
            _SUPPORTED_PROVIDERS as _SUPPORTED_LLM_PROVIDERS_BASE,
        )

        if (
            llm_str is None
            or not llm_str.strip()
            or llm_str.strip().casefold() == "auto"
        ):
            return None, None
        try:
            llm_provider, llm_model = llm_str.split(":", 1)
            assert llm_provider in _SUPPORTED_LLM_PROVIDERS_BASE, f"Unsupported `{llm_provider}`.\nSupported llm providers are: " + ", ".join(_SUPPORTED_LLM_PROVIDERS_BASE)
            return llm_provider, llm_model
        except ValueError:
            raise ValueError("Set SMART_LLM or FAST_LLM = '<llm_provider>:<llm_model>' e.g. 'openai:gpt-4o-mini'")

    @staticmethod
    def parse_reasoning_effort(reasoning_effort_str: str | None) -> str | None:
        """Parse reasoning effort string into (reasoning_effort)."""
        if reasoning_effort_str is None:
            return ReasoningEfforts.Medium.value
        if reasoning_effort_str not in [effort.value for effort in ReasoningEfforts]:
            raise ValueError(f"Invalid reasoning effort: {reasoning_effort_str}. Valid options are: {', '.join([effort.value for effort in ReasoningEfforts])}")
        return reasoning_effort_str

    @staticmethod
    def parse_embedding(embedding_str: str | None) -> tuple[str | None, str | None]:
        """Parse embedding string into (embedding_provider, embedding_model)."""
        from gpt_researcher.memory.embeddings import (
            _SUPPORTED_PROVIDERS as _SUPPORTED_EMBEDDING_PROVIDERS_MEM,
        )

        if embedding_str is None:
            return None, None
        try:
            embedding_provider, embedding_model = embedding_str.split(":", 1)
            assert embedding_provider in _SUPPORTED_EMBEDDING_PROVIDERS_MEM, f"Unsupported {embedding_provider}.\nSupported embedding providers are: " + ", ".join(
                _SUPPORTED_EMBEDDING_PROVIDERS_MEM
            )
            return embedding_provider, embedding_model
        except ValueError:
            raise ValueError("Set EMBEDDING = '<embedding_provider>:<embedding_model>' Eg 'openai:text-embedding-3-large'")

    def validate_doc_path(self):
        """Ensure that the folder exists at the doc path"""
        os.makedirs(self.doc_path, exist_ok=True)

    @staticmethod
    def parse_duration(duration_str: str) -> timedelta:
        """Parse a duration string into a timedelta object.

        Args:
            duration_str (str): The duration string to parse.

        Returns:
            timedelta: The parsed timedelta object.
        """
        # Define a regex pattern to match the format "XyYmZwZdHmMs"
        import re

        pattern = r"(?:(\d+)y)?(?:(\d+)m)?(?:(\d+)w)?(?:(\d+)d)?(?:(\d+)h)?(?:(\d+)m)?(?:(\d+)s)?"
        match: re.Match[str] | None = re.match(pattern, duration_str)
        if not match:
            raise ValueError(f"Invalid duration format: '{duration_str}'")

        years, months, weeks, days, hours, minutes, seconds = match.groups()
        return timedelta(
            days=(int(years or 0) * 365 + int(months or 0) * 30 + int(weeks or 0) * 7 + int(days or 0)),
            hours=int(hours or 0),
            minutes=int(minutes or 0),
            seconds=int(seconds or 0),
        )

    @staticmethod
    def convert_env_value(
        key: str,
        env_value: str,
        type_hint: type,
    ) -> Any:
        """Convert environment variable to the appropriate type based on the type hint."""

        casefold_env_value: str = env_value.casefold().strip()
        if key == "CACHE_EXPIRY_TIME":
            try:
                return Config.parse_duration(env_value)
            except ValueError:
                print(f"Warning: Invalid duration format: '{env_value}'. Using default value (2 days).")
                return timedelta(days=2)

        origin: Any | None = get_origin(type_hint)
        args: tuple[Any, ...] = get_args(type_hint)

        if origin is Union:
            # Handle Union types (e.g., Union[str, None])
            for arg in args:
                if arg is type(None):
                    if casefold_env_value in ("none", "null", ""):
                        return None
                else:
                    try:
                        return Config.convert_env_value(key, env_value, arg)
                    except ValueError:
                        continue
            raise ValueError(f"Cannot convert `{env_value}` to any of {args}")

        if type_hint is bool:
            return casefold_env_value in ("true", "1", "yes", "on")
        elif type_hint is int:
            return int(env_value)
        elif type_hint is float:
            return float(env_value)
        elif type_hint in (str, Any):
            return str(env_value)
        elif origin is list or origin is List:
            return json.loads(env_value)
        elif type_hint is dict or type_hint is Dict:
            return json.loads(env_value)
        else:
            raise ValueError(f"Unsupported type `{type_hint}` for key '{key}'")

    def set_verbose(self, verbose: bool) -> None:
        """Set the verbosity level."""
        self.llm_kwargs["verbose"] = verbose

    def get_mcp_server_config(self, name: str) -> dict:
        """
        Get the configuration for an MCP server.

        Args:
            name (str): The name of the MCP server to get the config for.

        Returns:
            dict: The server configuration, or an empty dict if the server is not found.
        """
        if not name or not self.mcp_servers:
            return {}

        for server in self.mcp_servers:
            if isinstance(server, dict) and server.get("name") == name:
                return server

        return {}
