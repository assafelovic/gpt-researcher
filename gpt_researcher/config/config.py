from __future__ import annotations

import json
import locale
import os

from multiprocessing import cpu_count
from pathlib import Path
from typing import TYPE_CHECKING, Any, ClassVar, Union, get_args, get_origin

from gpt_researcher.prompts import (
    PROMPT_AUTO_AGENT_INSTRUCTIONS,
    PROMPT_CONDENSE_INFORMATION,
    PROMPT_CURATE_SOURCES,
    PROMPT_GENERATE_CUSTOM_REPORT,
    PROMPT_GENERATE_DRAFT_TITLES,
    PROMPT_GENERATE_OUTLINE_REPORT,
    PROMPT_GENERATE_REPORT,
    PROMPT_GENERATE_REPORT_CONCLUSION,
    PROMPT_GENERATE_REPORT_INTRODUCTION,
    PROMPT_GENERATE_RESOURCE_REPORT,
    PROMPT_GENERATE_SEARCH_QUERIES,
    PROMPT_GENERATE_SUBTOPICS,
    PROMPT_GENERATE_SUBTOPIC_REPORT,
    PROMPT_POST_RETRIEVAL_PROCESSING,
)
from gpt_researcher.retrievers.utils import get_all_retriever_names
from gpt_researcher.utils.enum import OutputFileType, ReportFormat, ReportSource, ReportType, Tone
from gpt_researcher.utils.logger import get_formatted_logger


if TYPE_CHECKING:
    import logging

    from typing_extensions import Self

logger: logging.Logger = get_formatted_logger(__name__)


class BaseConfig:
    """Base config class for GPT Researcher.

    This class defines the base configuration for GPT Researcher. It provides a structure for managing configuration settings and environment variables.
    """

    DEFAULT_PATH: ClassVar[Path] = Path.home().joinpath(".gpt_researcher", "base.json").expanduser().absolute()

    def __new__(
        cls,
        config: Self | dict[str, Any] | os.PathLike | str | None = None,
        **kwargs: Any,
    ) -> Self:
        obj = super().__new__(cls)
        if config is not None:
            if isinstance(config, cls):
                cfg_path = Path(os.path.normpath(config.config_path)).expanduser().absolute()
            elif isinstance(config, dict):
                cfg_path = cls.from_dict(config).config_path
            elif isinstance(config, (os.PathLike, str)):
                cfg_path = Path(os.path.normpath(config)).expanduser().absolute()
            else:
                raise ValueError(f"Invalid config type: {config.__class__.__name__}, expected path-like or dict.")
        else:
            cfg_path = cls.DEFAULT_PATH
        for k, v in kwargs.items():
            setattr(obj, k, v)
        obj.config_path = cfg_path
        return obj

    def __init__(
        self,
        config: Self | dict[str, Any] | os.PathLike | str | None = None,
        **kwargs: Any,
    ):
        """Initialize the config class."""
        self.llm_kwargs: dict[str, Any] = kwargs.pop("llm_kwargs", {})
        self.embedding_kwargs: dict[str, Any] = kwargs.pop("embedding_kwargs", {})
        if isinstance(config, self.__class__):
            self.config_path = Path(os.path.normpath(config.config_path)).expanduser().absolute()
        elif isinstance(config, (os.PathLike, str)):
            self.config_path = Path(os.path.normpath(config)).expanduser().absolute()
        elif isinstance(config, dict):
            config_path = config.get("config_path")
            if config_path is None:
                self.config_path = Path.home().joinpath(".gpt_researcher", "default.json").expanduser().absolute()
            else:
                self.config_path = Path(os.path.normpath(config_path)).expanduser().absolute()

        else:
            self.config_path = Path.home().joinpath(".gpt_researcher", "default.json").expanduser().absolute()

        config_to_use: dict[str, Any] = {}
        if not os.path.exists(self.config_path) and not os.path.isfile(self.config_path):
            config_to_use = (
                self.default_config_dict()
                if config == "default" or config is None
                else self._create_config_dict(config)
            )
        else:
            config_to_use = self._create_config_dict(self.config_path)
        config_to_use.update(kwargs)  # type: ignore
        for key, value in config_to_use.items():
            setattr(self, key, value)

    @classmethod
    def from_path(
        cls,
        config_path: os.PathLike | str | None,
    ) -> Self:
        """Load a configuration from a path."""
        config_dict: dict[str, Any] = cls._create_config_dict(config_path)
        return cls(config_path, **config_dict)

    @classmethod
    def from_config(
        cls,
        params: dict[str, Any] | Self,
        config: Self | None = None,
    ) -> Self:
        """Load a configuration from a dictionary."""
        cur_config_dict: dict[str, Any] = cls().to_dict() if config is None else config.to_dict()
        params_dict = params.to_dict() if isinstance(params, cls) else params
        assert isinstance(params_dict, dict), f"params_dict must be a dictionary, got {params_dict.__class__.__name__}"
        cur_config_dict.update(params_dict)
        return cls(None, **cur_config_dict)

    @classmethod
    def from_dict(
        cls,
        params: dict[str, Any] | Self,
        config: Self | None = None,
    ) -> Self:
        """Load a configuration from a dictionary."""
        return cls.from_config(params, config)

    def to_dict(self) -> dict[str, Any]:
        """Return the config as a dictionary."""
        return {k: v for k, v in self.__dict__.items() if not k.startswith("_") and k.upper() == k}

    def to_json(self) -> str:
        """Return the config as a JSON string."""
        config_dict: dict[str, Any] = {k: str(v) for k, v in self.to_dict().items()}
        return json.dumps(config_dict, indent=2)

    @classmethod
    def default_config_dict(cls) -> dict[str, Any]:
        """Return the default config as a dictionary."""
        return {k: v for k, v in cls.__dict__.items() if k == k.upper() and not k.startswith("_")}

    @classmethod
    def _create_config_dict(
        cls,
        config: os.PathLike | str | dict[str, Any] | Self | None = None,
    ) -> dict[str, Any]:
        """Parse a config from a path or dict."""
        if config is None or config == "default":
            return cls.default_config_dict()
        if isinstance(config, str) and not config.strip():
            return cls.default_config_dict()

        if isinstance(config, dict):
            config_dict = config
        elif isinstance(config, (os.PathLike, str)):
            config_path_obj: Path = Path(os.path.expandvars(os.path.normpath(config))).absolute()
            if not config_path_obj.exists():
                config_path_obj = Path.home().joinpath(".gpt_researcher", f"{config_path_obj.stem}.json")
                if not config_path_obj.exists():
                    logger.warning(f"Warning: Configuration not found at '{config_path_obj}'. Using default configuration.")
                    if not config_path_obj.suffix.casefold().endswith(".json"):
                        logger.warning(f"Did you mean: '{config_path_obj.with_suffix('.json')}'?")
                    return cls.default_config_dict()
            try:
                config_dict: dict[str, Any] = json.loads(config_path_obj.read_text())
            except Exception as e:
                logger.exception(f"Error loading config from path '{config_path_obj}': {e.__class__.__name__}: {e}")
                logger.warning("Using default configuration.")
                return cls.default_config_dict()
        else:
            raise ValueError(f"Invalid config type: {config.__class__.__name__}, expected path-like or dict.")

        config_dict.update(cls.default_config_dict())  # type: ignore[arg-type]
        return config_dict

    def __setattr__(self, key: str, value: Any):
        upper_key = key.upper()
        if upper_key not in self.__class__.__annotations__:
            super().__setattr__(key, value)
            return
        env_value: str = os.environ.get(upper_key, "") or ""
        if not env_value:
            return
        value = self.convert_env_value(
            upper_key,
            env_value,
            self.__class__.__annotations__[upper_key],
        )
        os.environ[upper_key] = str(value)
        super().__setattr__(key, str(value))

    @classmethod
    def load_config(
        cls,
        config_path: os.PathLike | str | None,
    ) -> dict[str, Any]:
        """Load a configuration by name."""
        config_dict: dict[str, Any] = (
            cls.default_config_dict()
            if config_path is None
            else cls._create_config_dict(config_path)
        )

        # Merge with default config to ensure all keys are present
        merged_config: dict[str, Any] = cls.default_config_dict().copy()
        merged_config.update(config_dict)
        return merged_config

    def parse_retrievers(
        self,
        retriever_str: str,
    ) -> list[str]:
        """Parse the retriever string into a list of retrievers and validate them."""
        retrievers: list[str] = [retriever.strip() for retriever in retriever_str.split(",")]
        valid_retrievers: list[str] = get_all_retriever_names()
        invalid_retrievers: list[str] = [r for r in retrievers if r not in valid_retrievers]
        if invalid_retrievers:
            raise ValueError(f"Invalid retriever(s) found: {', '.join(invalid_retrievers)}. Valid options are: {', '.join(valid_retrievers)}.")
        return retrievers

    @classmethod
    def convert_env_value(
        cls,
        key: str,
        env_value: str,
        type_hint: type | str,
    ) -> Any:
        """Convert environment variable to the appropriate type based on the type hint."""
        origin: Any = get_origin(type_hint)
        args: tuple[Any, ...] = get_args(type_hint)

        if origin in (Union, "Union"):
            # Handle Union types (e.g., Union[str, None])
            for arg in args:
                if arg in (None.__class__.__name__, None.__class__):
                    if env_value.casefold() in ("none", "null", "", None):
                        return None
                else:
                    try:
                        return cls.convert_env_value(key, env_value, arg)
                    except ValueError:
                        continue
            raise ValueError(f"Cannot convert env value '{env_value}' to any of arg types `{args}` for key '{key}'")

        if type_hint in (bool, "bool"):
            return env_value.casefold() in ("true", "1", "yes", "on", "y")
        elif type_hint in (int, "int"):
            return int(env_value)
        elif type_hint in (float, "float"):
            return float(env_value)
        elif type_hint in (str, Any, "str"):
            return env_value
        elif origin in {list, list, dict, dict, "list", "dict", "List", "Dict"}:
            return json.loads(env_value)
        else:
            raise ValueError(f"Unsupported type `{type_hint}` for key '{key}'")


class Config(BaseConfig):
    """Config class for GPT Researcher.

    Config(): creates a default config,
    Config.from_path: constructs one from path, partially using class defaults if the file doesn't have the stuff already,
    Config.from_dict: Constructs a config from case-insensitive keys mapping to the attribute names.
    Config.from_params: same as from_dict except keys can be snake_case format.

    Examples:
        print(Config.DOC_PATH) # prints "./my-docs", the default.
        cfg = Config(doc_path="custom/path")
        print(cfg.DOC_PATH) # prints "custom/path"
        cfg = Config.from_dict({"doc_path": "custom/path"})
        print(cfg.DOC_PATH) # prints "custom/path"
        cfg = Config.from_path("~/.gpt_researcher/config.json")
        print(cfg.DOC_PATH) # prints whatever is defined in config.json, otherwise if it's not defined there, './my-docs'


    Attributes:
        AGENT_ROLE: The role of the agent.
        CONFIG_DIR: The directory for configuration files.
        CURATE_SOURCES: Whether to curate sources.
        DOC_PATH: The path to the document directory.
        DEEP_RESEARCH_CONCURRENCY: The number of concurrent deep research threads.
        DEEP_RESEARCH_DEPTH: The depth of the deep research.
        DEEP_RESEARCH_BREADTH: The breadth of the deep research.
        EMBEDDING: The embedding model to use.
        EMBEDDING_MODEL: The specific embedding model to use.
        EMBEDDING_PROVIDER: The provider of the embedding model.
        EMBEDDING_FALLBACK_MODELS: The fallback models for the embedding provider.
        EMBEDDING_KWARGS: The keyword arguments for the embedding model.
        FALLBACK_MODELS: The fallback models for the LLM.
        FAST_LLM: The fast LLM to use.
        FAST_LLM_MODEL: The specific fast LLM to use.
        FAST_LLM_PROVIDER: The provider of the fast LLM.
        FAST_LLM_TEMPERATURE: The temperature for the fast LLM.
        FAST_TOKEN_LIMIT: The token limit for the fast LLM.
        LANGUAGE: The language to use.
        LANGCHAIN_TRACING_V2: Boolean flag to enable LangChain tracing V2.
        MAX_ITERATIONS: The maximum number of iterations.
        MAX_SCRAPER_WORKERS: The maximum number of scraper workers.
        MAX_SEARCH_RESULTS_PER_QUERY: The maximum number of search results per query.
        MAX_SOURCES: The maximum number of sources.
        MAX_URLS: The maximum number of URLs.
        MAX_SUBTOPICS: The maximum number of subtopics.
        MAX_LINK_EXPLORATION_DEPTH: The maximum number of link exploration depth.
        MEMORY_BACKEND: The backend for memory storage.
        OUTPUT_FORMAT: The format of the output.
        QUERY_DOMAINS: The domains to query.
        REPORT_FORMAT: The format of the report.
        REPORT_SOURCE: The source of the report.
        REPORT_TYPE: The type of report.
        RESEARCH_PLANNER: The planner for research.
        RETRIEVER: The retriever to use.
        SCRAPER: The scraper to use.
        SIMILARITY_THRESHOLD: The similarity threshold for the retriever.
        SMART_LLM: The smart LLM to use.
        SMART_LLM_MODEL: The specific smart LLM to use.
        SMART_LLM_PROVIDER: The provider of the smart LLM.
        SMART_LLM_TEMPERATURE: The temperature for the smart LLM.
        SMART_TOKEN_LIMIT: The token limit for the smart LLM.
        STRATEGIC_LLM: The strategic LLM to use.
        STRATEGIC_LLM_MODEL: The specific strategic LLM to use.
        STRATEGIC_LLM_PROVIDER: The provider of the strategic LLM.
        STRATEGIC_LLM_TEMPERATURE: The temperature for the strategic LLM.
        STRATEGIC_TOKEN_LIMIT: The token limit for the strategic LLM.
        TEMPERATURE: The temperature for the LLM.
        TONE: The tone for the LLM.
        TOTAL_WORDS: The total number of words for the LLM.
        USER_AGENT: The user agent for the LLM.
        USE_FALLBACKS: Whether to use fallback models.
        VERBOSE: Whether to enable verbose logging.

        # Scraper configuration
        SCRAPER_TIMEOUT: The default timeout for scrapers in seconds.
        SCRAPER_MAX_WORKERS: The maximum number of scraper worker threads.
        SCRAPER_MIN_CONTENT_LENGTH: The minimum content length to consider valid.

        # Deep research configuration
        MAX_CONTEXT_WORDS: The maximum number of words to keep in context.
        DEEP_RESEARCH_NUM_QUERIES: The number of queries to generate for deep research.
        DEEP_RESEARCH_NUM_LEARNINGS: The number of learnings to extract from research results.

        # Retriever configuration
        RETRIEVER_TIMEOUT: The default timeout for retrievers in seconds.
        RETRIEVER_SERPER_TIMEOUT: The timeout for Serper retriever in seconds.
        RETRIEVER_TAVILY_TIMEOUT: The timeout for Tavily retriever in seconds.
        RETRIEVER_SEARCHAPI_TIMEOUT: The timeout for SearchAPI retriever in seconds.

        # Web request configuration
        WEB_REQUEST_TIMEOUT: The timeout for general web requests in seconds.
        XHR_TIMEOUT: The timeout for XHR requests in milliseconds.

        POST_RETRIEVAL_PROCESSING_INSTRUCTIONS: The instructions for post-retrieval processing.
        PROMPT_GENERATE_SEARCH_QUERIES: The prompt for generating search queries.
        PROMPT_GENERATE_REPORT: The prompt for generating a report.
        PROMPT_CURATE_SOURCES: The prompt for curating sources.
        PROMPT_GENERATE_RESOURCE_REPORT: The prompt for generating a resource report.
        PROMPT_GENERATE_CUSTOM_REPORT: The prompt for generating a custom report.
        PROMPT_GENERATE_OUTLINE_REPORT: The prompt for generating an outline report.
        PROMPT_AUTO_AGENT_INSTRUCTIONS: The prompt for auto-agent instructions.
        PROMPT_CONDENSE_INFORMATION: The prompt for condensing information.
        PROMPT_GENERATE_SUBTOPICS: The prompt for generating subtopics.
        PROMPT_GENERATE_SUBTOPIC_REPORT: The prompt for generating a subtopic report.
        PROMPT_GENERATE_DRAFT_TITLES: The prompt for generating draft titles.
        PROMPT_GENERATE_REPORT_INTRODUCTION: The prompt for generating a report introduction.
        PROMPT_GENERATE_REPORT_CONCLUSION: The prompt for generating a report conclusion.
        PROMPT_POST_RETRIEVAL_PROCESSING: The prompt for post-retrieval processing.
    """

    DEFAULT_PATH: ClassVar[Path] = Path.home().joinpath(".gpt_researcher", "config.json").expanduser().absolute()


    AGENT_ROLE: str = os.environ.get("AGENT_ROLE", "")
    CONFIG_DIR: str = os.path.join(os.path.dirname(__file__), "variables")
    CURATE_SOURCES: bool = bool(str(os.environ.get("CURATE_SOURCES", False)).casefold() == "true")
    DOC_PATH: str = os.environ.get("DOC_PATH", str(Path.home().absolute()))
    DEEP_RESEARCH_CONCURRENCY: int = int(os.environ.get("DEEP_RESEARCH_CONCURRENCY", 1))
    DEEP_RESEARCH_DEPTH: int = int(os.environ.get("DEEP_RESEARCH_DEPTH", 1))
    DEEP_RESEARCH_BREADTH: int = int(os.environ.get("DEEP_RESEARCH_BREADTH", 1))
    EMBEDDING: str = os.environ.get("EMBEDDING", "openai:text-embedding-3-small")
    EMBEDDING_MODEL: str = os.environ.get("EMBEDDING_MODEL", "text-embedding-3-small")
    EMBEDDING_PROVIDER: str = os.environ.get("EMBEDDING_PROVIDER", "openai")
    EMBEDDING_FALLBACK_MODELS: list[str] = (
        lambda value: json.loads(value)
        if value.lstrip().startswith("[") and value.rstrip().endswith("]")
        else value.split(",")
        if "," in value
        else [item.strip() for item in value.split(",") if item.strip()]
    )(str(os.environ.get("EMBEDDING_FALLBACK_MODELS", "") or "").strip())
    EMBEDDING_KWARGS: dict[str, Any] = json.loads(os.environ.get("EMBEDDING_KWARGS", "{}"))
    # FALLBACK_MODELS is a list of free LLM fallback model identifiers.
    # Users can specify this as a JSON-encoded list (e.g., '["model1", "model2"]') or as a comma-separated string (e.g., "model1, model2").
    EXCLUDED_DOMAINS: list[str] = (
        lambda value: json.loads(value)
        if value.lstrip().startswith("[") and value.rstrip().endswith("]")
        else value.split(",")
        if "," in value
        else [item.strip() for item in value.split(",") if item.strip()]
    )(str(os.environ.get("EXCLUDED_DOMAINS", "") or "").strip())
    FALLBACK_MODELS: list[str] = (
        lambda value: json.loads(value)
        if value.lstrip().startswith("[") and value.rstrip().endswith("]")
        else value.split(",")
        if "," in value
        else [item.strip() for item in value.split(",") if item.strip()]
    )(str(os.environ.get("FALLBACK_MODELS", "") or "").strip())
    FAST_LLM: str = os.environ.get("FAST_LLM", "groq:mixtral-8x7b-32768")  # TODO: use this somewhere
    FAST_LLM_MODEL: str = os.environ.get("FAST_LLM_MODEL", "mixtral-8x7b-32768")  # TODO: use this somewhere
    FAST_LLM_PROVIDER: str = os.environ.get("FAST_LLM_PROVIDER", "groq")
    FAST_LLM_TEMPERATURE: float = float(os.environ.get("FAST_LLM_TEMPERATURE", 0.15))
    FAST_TOKEN_LIMIT: int = int(os.environ.get("FAST_TOKEN_LIMIT", 32768))
    LANGCHAIN_TRACING_V2: bool = bool(str(os.environ.get("LANGCHAIN_TRACING_V2", False)).casefold() == "true")
    LANGUAGE: str = os.environ.get("LANGUAGE", (locale.getdefaultlocale()[0] or "en").split("_")[0])
    MAX_ITERATIONS: int = int(os.environ.get("MAX_ITERATIONS", 4))
    MAX_SCRAPER_WORKERS: int = int(os.environ.get("MAX_SCRAPER_WORKERS", 10))
    MAX_SEARCH_RESULTS_PER_QUERY: int = int(os.environ.get("MAX_SEARCH_RESULTS_PER_QUERY", 5))
    MAX_SOURCES: int = int(os.environ.get("MAX_SOURCES", 10))
    MAX_URLS: int = int(os.environ.get("MAX_URLS", 10))
    MAX_SUBTOPICS: int = int(os.environ.get("MAX_SUBTOPICS", 3))
    MAX_LINK_EXPLORATION_DEPTH: int = int(os.environ.get("MAX_LINK_EXPLORATION_DEPTH", 2))
    MEMORY_BACKEND: ReportSource = ReportSource.__members__[os.environ.get("MEMORY_BACKEND", ReportSource.Local.name) or ReportSource.Local.name]
    OUTPUT_FORMAT: OutputFileType = OutputFileType.__members__[os.environ.get("OUTPUT_FORMAT", OutputFileType.MARKDOWN.name) or OutputFileType.MARKDOWN.name]
    QUERY_DOMAINS: list[str] = str(os.environ.get("QUERY_DOMAINS", "")).split(",")
    REPORT_FORMAT: ReportFormat = ReportFormat.__members__[os.environ.get("REPORT_FORMAT", ReportFormat.APA.name) or ReportFormat.APA.name]
    REPORT_SOURCE: ReportSource = ReportSource.__members__[os.environ.get("REPORT_SOURCE", ReportSource.Web.name) or ReportSource.Web.name]
    REPORT_TYPE: ReportType = ReportType.__members__[os.environ.get("REPORT_TYPE", ReportType.ResearchReport.name) or ReportType.ResearchReport.name]
    RESEARCH_PLANNER: str = os.environ.get("RESEARCH_PLANNER", "outline")
    SIMILARITY_THRESHOLD: float = float(os.environ.get("SIMILARITY_THRESHOLD", 0.42))
    SMART_LLM: str = os.environ.get("SMART_LLM", "litellm:openrouter/google/gemini-2.0-pro-exp-02-05:free")
    SMART_LLM_MODEL: str = os.environ.get("SMART_LLM_MODEL", "openrouter/google/gemini-2.0-pro-exp-02-05:free")
    SMART_LLM_PROVIDER: str = os.environ.get("SMART_LLM_PROVIDER", "litellm")
    SMART_LLM_TEMPERATURE: float = float(os.environ.get("SMART_LLM_TEMPERATURE", 0.15))
    SMART_TOKEN_LIMIT: int = int(os.environ.get("SMART_TOKEN_LIMIT", 4096))
    STRATEGIC_LLM: str = os.environ.get("STRATEGIC_LLM", "litellm:openrouter/google/gemini-2.0-pro-exp-02-05:free")
    STRATEGIC_LLM_MODEL: str = os.environ.get("STRATEGIC_LLM_MODEL", "openrouter/google/gemini-2.0-pro-exp-02-05:free")
    STRATEGIC_LLM_PROVIDER: str = os.environ.get("STRATEGIC_LLM_PROVIDER", "litellm")
    STRATEGIC_LLM_TEMPERATURE: float = float(os.environ.get("STRATEGIC_LLM_TEMPERATURE", 0.4))
    STRATEGIC_TOKEN_LIMIT: int = int(os.environ.get("STRATEGIC_TOKEN_LIMIT", 4096))
    TEMPERATURE: float = STRATEGIC_LLM_TEMPERATURE
    TONE: Tone = Tone.__members__.get(os.environ.get("TONE", "Objective").upper(), Tone.Objective)
    TOTAL_WORDS: int = int(os.environ.get("TOTAL_WORDS", 1000))
    USER_AGENT: str = os.environ.get("USER_AGENT", "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.0.0 Safari/537.36 Edg/119.0.0.0")
      # alternatively: "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/128.0.0.0 Safari/537.36"
    USE_FALLBACKS: bool = bool(str(os.environ.get("USE_FALLBACKS", True)).casefold() == "true")
    VERBOSE: bool = bool(str(os.environ.get("VERBOSE", True)).casefold() == "true")

    # Scraper configuration
    SCRAPER: str = os.environ.get("SCRAPER", "bs")
    SCRAPER_TIMEOUT: int = int(os.environ.get("SCRAPER_TIMEOUT", 10))  # TODO: add to all the scrapers
    SCRAPER_MAX_WORKERS: int = int(os.environ.get("SCRAPER_MAX_WORKERS", cpu_count() * 2))  # TODO: add to all the scrapers
    SCRAPER_MIN_CONTENT_LENGTH: int = int(os.environ.get("SCRAPER_MIN_CONTENT_LENGTH", 100))  # TODO: add to all the scrapers

    # Deep research configuration
    MAX_CONTEXT_WORDS: int = int(os.environ.get("MAX_CONTEXT_WORDS", 25000))
    DEEP_RESEARCH_NUM_QUERIES: int = int(os.environ.get("DEEP_RESEARCH_NUM_QUERIES", 3))
    DEEP_RESEARCH_NUM_LEARNINGS: int = int(os.environ.get("DEEP_RESEARCH_NUM_LEARNINGS", 3))

    # Retriever configuration
    RETRIEVER: str = os.environ.get("RETRIEVER", "tavily")  # TODO: add to all the retrievers
    RETRIEVER_TIMEOUT: int = int(os.environ.get("RETRIEVER_TIMEOUT", 10))  # TODO: add to all the retrievers

    POST_RETRIEVAL_PROCESSING_INSTRUCTIONS: str = os.environ.get("POST_RETRIEVAL_PROCESSING_INSTRUCTIONS", "")
    PROMPT_GENERATE_SEARCH_QUERIES: str = os.environ.get("PROMPT_GENERATE_SEARCH_QUERIES", PROMPT_GENERATE_SEARCH_QUERIES)
    PROMPT_GENERATE_REPORT: str = os.environ.get("PROMPT_GENERATE_REPORT", PROMPT_GENERATE_REPORT)
    PROMPT_CURATE_SOURCES: str = os.environ.get("PROMPT_CURATE_SOURCES", PROMPT_CURATE_SOURCES)
    PROMPT_GENERATE_RESOURCE_REPORT: str = os.environ.get("PROMPT_GENERATE_RESOURCE_REPORT", PROMPT_GENERATE_RESOURCE_REPORT)
    PROMPT_GENERATE_CUSTOM_REPORT: str = os.environ.get("PROMPT_GENERATE_CUSTOM_REPORT", PROMPT_GENERATE_CUSTOM_REPORT)
    PROMPT_GENERATE_OUTLINE_REPORT: str = os.environ.get("PROMPT_GENERATE_OUTLINE_REPORT", PROMPT_GENERATE_OUTLINE_REPORT)
    PROMPT_AUTO_AGENT_INSTRUCTIONS: str = os.environ.get("PROMPT_AUTO_AGENT_INSTRUCTIONS", PROMPT_AUTO_AGENT_INSTRUCTIONS)
    PROMPT_CONDENSE_INFORMATION: str = os.environ.get("PROMPT_CONDENSE_INFORMATION", PROMPT_CONDENSE_INFORMATION)
    PROMPT_GENERATE_SUBTOPICS: str = os.environ.get("PROMPT_GENERATE_SUBTOPICS", PROMPT_GENERATE_SUBTOPICS)
    PROMPT_GENERATE_SUBTOPIC_REPORT: str = os.environ.get("PROMPT_GENERATE_SUBTOPIC_REPORT", PROMPT_GENERATE_SUBTOPIC_REPORT)
    PROMPT_GENERATE_DRAFT_TITLES: str = os.environ.get("PROMPT_GENERATE_DRAFT_TITLES", PROMPT_GENERATE_DRAFT_TITLES)
    PROMPT_GENERATE_REPORT_INTRODUCTION: str = os.environ.get("PROMPT_GENERATE_REPORT_INTRODUCTION", PROMPT_GENERATE_REPORT_INTRODUCTION)
    PROMPT_GENERATE_REPORT_CONCLUSION: str = os.environ.get("PROMPT_GENERATE_REPORT_CONCLUSION", PROMPT_GENERATE_REPORT_CONCLUSION)
    PROMPT_POST_RETRIEVAL_PROCESSING: str = os.environ.get("PROMPT_POST_RETRIEVAL_PROCESSING", PROMPT_POST_RETRIEVAL_PROCESSING)

    def __init__(
        self,
        config: Self | dict[str, Any] | os.PathLike | str | None = None,
        **kwargs: Any,
    ):
        super().__init__(config, **kwargs)
        try:
            self.retrievers: list[str] = self.parse_retrievers(self.RETRIEVER)
        except ValueError as e:
            logger.warning(
                f"{e.__class__.__name__}: {e}. Defaulting to 'tavily' retriever.",
                exc_info=True,
            )
            self.retrievers = ["tavily"]
        self._setup_llms()
        self._setup_fallback_models()
        os.makedirs(self.DOC_PATH, exist_ok=True)
        os.environ["LITELLM_LOG"] = "DEBUG" if self.VERBOSE else "INFO"

    def _setup_llms(self) -> None:
        embedding_provider: str | None = os.environ.get("EMBEDDING_PROVIDER")
        if embedding_provider is None:
            # Inline parse_embedding logic
            if self.EMBEDDING is None:
                msg = "Set EMBEDDING = '<embedding_provider>:<embedding_model>' Eg 'openai:text-embedding-3-large'"
                raise ValueError(msg)
            try:
                self.EMBEDDING_PROVIDER, self.EMBEDDING_MODEL = self.EMBEDDING.split(":", 1)
            except ValueError:
                msg = "Set EMBEDDING = '<embedding_provider>:<embedding_model>' Eg 'openai:text-embedding-3-large'"
                raise ValueError(msg)

        # FAST_LLM
        try:
            self.FAST_LLM_PROVIDER, self.FAST_LLM_MODEL = self.FAST_LLM.split(":", 1)
        except ValueError:
            logger.error("FAST_LLM not setup correctly. Format: '<llm_provider>:<llm_model>' e.g. 'openai:gpt-4o-mini'")
            self.FAST_LLM_PROVIDER = self.__class__.FAST_LLM_PROVIDER
            self.FAST_LLM_MODEL = self.__class__.FAST_LLM_MODEL

        # SMART_LLM
        try:
            self.SMART_LLM_PROVIDER, self.SMART_LLM_MODEL = self.STRATEGIC_LLM.split(":", 1)
        except ValueError:
            logger.error("STRATEGIC_LLM not setup correctly. Format: '<llm_provider>:<llm_model>' e.g. 'openai:gpt-4o-mini'")
            self.SMART_LLM_PROVIDER = self.__class__.SMART_LLM_PROVIDER
            self.SMART_LLM_MODEL = self.__class__.SMART_LLM_MODEL

        # STRATEGIC_LLM
        try:
            self.STRATEGIC_LLM_PROVIDER, self.STRATEGIC_LLM_MODEL = self.STRATEGIC_LLM.split(":", 1)
        except ValueError:
            logger.error("STRATEGIC_LLM not setup correctly. Format: '<llm_provider>:<llm_model>' e.g. 'openai:gpt-4o-mini'")
            self.STRATEGIC_LLM_PROVIDER = self.__class__.STRATEGIC_LLM_PROVIDER
            self.STRATEGIC_LLM_MODEL = self.__class__.STRATEGIC_LLM_MODEL

    def _setup_fallback_models(self) -> None:
        if not self.FALLBACK_MODELS:
            from llm_fallbacks.config import FREE_MODELS
            for model_name, model_spec in FREE_MODELS:
                if str(model_spec.get("mode", "chat") or "chat").strip().casefold() != "chat":
                    continue
                provider = model_spec["litellm_provider"]  # pyright: ignore[reportTypedDictNotRequiredAccess]
                self.FALLBACK_MODELS.append(f"litellm:{provider}/{model_name}")
        else:
            self.FALLBACK_MODELS = list(self.FALLBACK_MODELS)

        if not self.EMBEDDING_FALLBACK_MODELS:
            from llm_fallbacks.config import ALL_EMBEDDING_MODELS
            for model_name, model_spec in ALL_EMBEDDING_MODELS:
                provider = model_spec["litellm_provider"]  # pyright: ignore[reportTypedDictNotRequiredAccess]
                self.EMBEDDING_FALLBACK_MODELS.append(f"litellm:{provider}/{model_name}")
        else:
            self.EMBEDDING_FALLBACK_MODELS = list(self.EMBEDDING_FALLBACK_MODELS)

    @classmethod
    def list_available_configs(cls) -> list[str]:
        """List all available configuration names."""
        configs: list[str] = ["default"]
        for file in Path(os.path.expandvars(os.path.normpath(cls.CONFIG_DIR))).absolute().iterdir():
            if file.suffix.casefold() == ".json":
                configs.append(file.stem)  # Remove .json extension
        return configs


class Settings(BaseConfig):
    """Settings Configuration class for GPT Researcher.

    This subclass of BaseConfig is specifically designed to handle settings configurations
    for the GPT Researcher application. It provides a structure for managing settings needed for the application.

    Attributes:

        AI21_API_KEY: API key for AI21 services.
        ANTHROPIC_API_KEY: API key for Anthropic services.
        ARLIAI_API_KEY: API key for ArliAI services.
        AWANLLM_API_KEY: API key for AwanLLM services.
        AZURE_OPENAI_API_KEY: API key for Azure OpenAI services.
        AZURE_OPENAI_API_VERSION: API version for Azure OpenAI services.
        AZURE_OPENAI_ENDPOINT: Endpoint URL for Azure OpenAI services.
        BASETEN_API_KEY: API key for Baseten services.
        BING_API_KEY: API key for Bing search services.
        BRAVE_API_KEY: API key for Brave search services.
        CEREBRIUMAI_API_KEY: API key for CerebriumAI services.
        DEEPINFRA_API_KEY: API key for DeepInfra services.
        DEEPSEEK_API_KEY: API key for DeepSeek services.
        EXA_API_KEY: API key for Exa services.
        FOREFRONTAI_API_KEY: API key for ForefrontAI services.
        GEMINI_API_KEY: API key for Google Gemini services.
        GITHUB_TOKEN: Authentication token for GitHub API.
        GITLAB_TOKEN: Authentication token for GitLab API.
        GLAMA_API_KEY: API key for Glama services.
        GOOGLE_API_KEY: API key for Google services.
        GOOGLE_APPLICATION_CREDENTIALS: Path to Google application credentials file.
        GROQ_API_KEY: API key for Groq services.
        HUGGINGFACE_ACCESS_TOKEN: Access token for Hugging Face services.
        JINA_API_KEY: API key for Jina services.
        LANGCHAIN_API_KEY: API key for LangChain services.
        LM_STUDIO_API_BASE: Base URL for LM Studio API.
        MEILI_HTTP_ADDR: HTTP address for MeiliSearch.
        MEILI_MASTER_KEY: Master key for MeiliSearch.
        MISTRAL_API_KEY: API key for Mistral services.
        MISTRALAI_API_KEY: API key for MistralAI services.
        OLLAMA_BASE_URL: Base URL for Ollama services.
        OPENAI_API_KEY: API key for OpenAI services.
        OPENAI_ORGANIZATION: Organization ID for OpenAI services.
        OPENROUTER_API_KEY: API key for OpenRouter services.
        PERPLEXITY_API_KEY: API key for Perplexity services.
        PERPLEXITYAI_API_KEY: API key for PerplexityAI services.
        RETRIEVER: Default retriever to use (e.g., "tavily").
        RETRIEVER_ENDPOINT: Endpoint URL for custom retriever services.
        SEARCHAPI_API_KEY: API key for SearchAPI services.
        SEARX_URL: URL for SearX search engine.
        SERPAPI_API_KEY: API key for SerpAPI services.
        SERPER_API_KEY: API key for Serper services.
        SMART_LLM: Configuration string for smart LLM in format "provider:model".
        STRATEGIC_LLM: Configuration string for strategic LLM in format "provider:model".
        TAVILY_API_KEY: API key for Tavily search services.
        TOGETHERAI_API_KEY: API key for TogetherAI services.
        VERTEX_LOCATION: Location for Google Vertex AI services.
        VERTEX_PROJECT: Project ID for Google Vertex AI services.
        VOYAGE_API_KEY: API key for Voyage services.
        YANDEX_API_KEY: API key for Yandex services.
        YOU_API_KEY: API key for You.com services.
        ZENML_API_KEY: API key for ZenML services.

    """
    BASE_PATH: ClassVar[Path] = Path.home().joinpath(".gpt_researcher", "settings.json").expanduser().absolute()

    AI21_API_KEY: str = os.environ.get("AI21_API_KEY", "")
    ANTHROPIC_API_KEY: str = os.environ.get("ANTHROPIC_API_KEY", "")
    ARLIAI_API_KEY: str = os.environ.get("ARLIAI_API_KEY", "")
    AWANLLM_API_KEY: str = os.environ.get("AWANLLM_API_KEY", "")
    AZURE_OPENAI_API_KEY: str = os.environ.get("AZURE_OPENAI_API_KEY", "")
    AZURE_OPENAI_API_VERSION: str = os.environ.get("AZURE_OPENAI_API_VERSION", "")
    AZURE_OPENAI_ENDPOINT: str = os.environ.get("AZURE_OPENAI_ENDPOINT", "")
    BASETEN_API_KEY: str = os.environ.get("BASETEN_API_KEY", "")
    BING_API_KEY: str = os.environ.get("BING_API_KEY", "")
    BRAVE_API_KEY: str = os.environ.get("BRAVE_API_KEY", "")
    CEREBRIUMAI_API_KEY: str = os.environ.get("CEREBRIUMAI_API_KEY", "")
    DEEPINFRA_API_KEY: str = os.environ.get("DEEPINFRA_API_KEY", "")
    DEEPSEEK_API_KEY: str = os.environ.get("DEEPSEEK_API_KEY", "")
    EXA_API_KEY: str = os.environ.get("EXA_API_KEY", "")
    FOREFRONTAI_API_KEY: str = os.environ.get("FOREFRONTAI_API_KEY", "")
    GEMINI_API_KEY: str = os.environ.get("GEMINI_API_KEY", "")
    GITHUB_TOKEN: str = os.environ.get("GITHUB_TOKEN", "")
    GITLAB_TOKEN: str = os.environ.get("GITLAB_TOKEN", "")
    GLAMA_API_KEY: str = os.environ.get("GLAMA_API_KEY", "")
    GOOGLE_API_KEY: str = os.environ.get("GOOGLE_API_KEY", "")
    GOOGLE_APPLICATION_CREDENTIALS: str = os.environ.get("GOOGLE_APPLICATION_CREDENTIALS", "")
    GROQ_API_KEY: str = os.environ.get("GROQ_API_KEY", "")
    HUGGINGFACE_ACCESS_TOKEN: str = os.environ.get("HUGGINGFACE_ACCESS_TOKEN", "")
    JINA_API_KEY: str = os.environ.get("JINA_API_KEY", "")
    LANGCHAIN_API_KEY: str = os.environ.get("LANGCHAIN_API_KEY", "")
    LM_STUDIO_API_BASE: str = os.environ.get("LM_STUDIO_API_BASE", "")
    MEILI_HTTP_ADDR: str = os.environ.get("MEILI_HTTP_ADDR", "")
    MEILI_MASTER_KEY: str = os.environ.get("MEILI_MASTER_KEY", "")
    MISTRAL_API_KEY: str = os.environ.get("MISTRAL_API_KEY", "")
    MISTRALAI_API_KEY: str = os.environ.get("MISTRALAI_API_KEY", "")
    OLLAMA_BASE_URL: str = os.environ.get("OLLAMA_BASE_URL", "")
    OPENAI_API_KEY: str = os.environ.get("OPENAI_API_KEY", "")
    OPENAI_ORGANIZATION: str = os.environ.get("OPENAI_ORGANIZATION", "")
    OPENROUTER_API_KEY: str = os.environ.get("OPENROUTER_API_KEY", "")
    PERPLEXITY_API_KEY: str = os.environ.get("PERPLEXITY_API_KEY", "")
    PERPLEXITYAI_API_KEY: str = os.environ.get("PERPLEXITYAI_API_KEY", "")
    RETRIEVER: str = os.environ.get("RETRIEVER", "tavily")
    RETRIEVER_ENDPOINT: str = os.environ.get("RETRIEVER_ENDPOINT", "")
    SEARCHAPI_API_KEY: str = os.environ.get("SEARCHAPI_API_KEY", "")
    SEARX_URL: str = os.environ.get("SEARX_URL", "")
    SERPAPI_API_KEY: str = os.environ.get("SERPAPI_API_KEY", "")
    SERPER_API_KEY: str = os.environ.get("SERPER_API_KEY", "")
    SMART_LLM: str = os.environ.get("SMART_LLM", "")
    STRATEGIC_LLM: str = os.environ.get("STRATEGIC_LLM", "")
    TAVILY_API_KEY: str = os.environ.get("TAVILY_API_KEY", "")
    TOGETHERAI_API_KEY: str = os.environ.get("TOGETHERAI_API_KEY", "")
    VERTEX_LOCATION: str = os.environ.get("VERTEX_LOCATION", "")
    VERTEX_PROJECT: str = os.environ.get("VERTEX_PROJECT", "")
    VOYAGE_API_KEY: str = os.environ.get("VOYAGE_API_KEY", "")
    YANDEX_API_KEY: str = os.environ.get("YANDEX_API_KEY", "")
    YOU_API_KEY: str = os.environ.get("YOU_API_KEY", "")
    ZENML_API_KEY: str = os.environ.get("ZENML_API_KEY", "")

    def __init__(
        self,
        *args: Any,
        **kwargs: Any,
    ):
        """Initialize the settings class."""
        super().__init__(*args, **kwargs)
