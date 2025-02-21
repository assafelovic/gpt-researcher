from __future__ import annotations

import json
import locale
import logging
import os

from pathlib import Path
from typing import Any, Dict, List, Union, get_args, get_origin

from gpt_researcher.retrievers.utils import get_all_retriever_names
from gpt_researcher.utils.enum import OutputFileType, ReportFormat, ReportSource, ReportType, SupportedLanguages, Tone

logger: logging.Logger = logging.getLogger(__name__)


class Config:
    """Config class for GPT Researcher."""

    AGENT_ROLE: str = os.environ.get("AGENT_ROLE", "")
    CONFIG_DIR: str = os.path.join(os.path.dirname(__file__), "variables")
    CURATE_SOURCES: bool = bool(os.environ.get("CURATE_SOURCES", False))
    DOC_PATH: str = os.environ.get("DOC_PATH", str(Path.home().absolute()))
    EMBEDDING: str = os.environ.get("EMBEDDING", "openai:text-embedding-3-small")
    EMBEDDING_KWARGS: dict[str, Any] = json.loads(os.environ.get("EMBEDDING_KWARGS", "{}"))
    EMBEDDING_MODEL: str = os.environ.get("EMBEDDING_MODEL", "text-embedding-3-small")
    EMBEDDING_PROVIDER: str = os.environ.get("EMBEDDING_PROVIDER", "openai")
    FAST_LLM: str = os.environ.get("FAST_LLM", "groq:mixtral-8x7b-32768")
    FAST_LLM_MODEL: str = os.environ.get("FAST_LLM_MODEL", "mixtral-8x7b-32768")
    FAST_LLM_PROVIDER: str = os.environ.get("FAST_LLM_PROVIDER", "groq")
    FAST_TOKEN_LIMIT: int = int(os.environ.get("FAST_TOKEN_LIMIT", 32768))
    LANGUAGE: SupportedLanguages = SupportedLanguages(
        os.environ.get(
            "LANGUAGE",
            (locale.getdefaultlocale()[0] or "en").split("_")[0],
        )
    )
    MAX_ITERATIONS: int = int(os.environ.get("MAX_ITERATIONS", 4))
    MAX_SEARCH_RESULTS_PER_QUERY: int = int(os.environ.get("MAX_SEARCH_RESULTS_PER_QUERY", 5))
    MAX_SUBTOPICS: int = int(os.environ.get("MAX_SUBTOPICS", 3))
    MEMORY_BACKEND: ReportSource = ReportSource(os.environ.get("MEMORY_BACKEND", "local").lower())
    OUTPUT_FORMAT: OutputFileType = OutputFileType(
        os.environ.get(
            "OUTPUT_FORMAT",
            "markdown",
        )
    )
    REPORT_FORMAT: ReportFormat = ReportFormat(os.environ.get("REPORT_FORMAT", "APA"))
    REPORT_SOURCE: ReportSource = ReportSource(os.environ.get("REPORT_SOURCE", "web"))
    REPORT_TYPE: ReportType = ReportType(os.environ.get("REPORT_TYPE", "research_report"))
    RESEARCH_PLANNER: str = os.environ.get("RESEARCH_PLANNER", "outline")
    RETRIEVER: str = os.environ.get("RETRIEVER", "tavily")
    SCRAPER: str = os.environ.get("SCRAPER", "bs")
    SIMILARITY_THRESHOLD: float = float(os.environ.get("SIMILARITY_THRESHOLD", 0.42))
    SMART_LLM: str = os.environ.get("SMART_LLM", "litellm:gemini-2.0-flash-exp")
    SMART_LLM_MODEL: str = os.environ.get("SMART_LLM_MODEL", "gemini-2.0-flash-exp")
    SMART_LLM_PROVIDER: str = os.environ.get("SMART_LLM_PROVIDER", "litellm")
    SMART_TOKEN_LIMIT: int = int(os.environ.get("SMART_TOKEN_LIMIT", 4096))
    STRATEGIC_LLM: str = os.environ.get("STRATEGIC_LLM", "litellm:gemini-2.0-flash-thinking-exp")
    STRATEGIC_LLM_MODEL: str = os.environ.get(
        "STRATEGIC_LLM_MODEL",
        "gemini-2.0-flash-thinking-exp",
    )
    STRATEGIC_LLM_PROVIDER: str = os.environ.get("STRATEGIC_LLM_PROVIDER", "litellm")
    STRATEGIC_TOKEN_LIMIT: int = int(os.environ.get("STRATEGIC_TOKEN_LIMIT", 4096))
    TEMPERATURE: float = float(os.environ.get("TEMPERATURE", 0.4))
    TONE: Tone = Tone.__members__.get(os.environ.get("TONE", "Objective").upper(), Tone.Objective)
    TOTAL_WORDS: int = int(os.environ.get("TOTAL_WORDS", 1000))
    USER_AGENT: str = os.environ.get(
        "USER_AGENT",
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.0.0 Safari/537.36 Edg/119.0.0.0",
    )  # "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/128.0.0.0 Safari/537.36"
    VERBOSE: bool = bool(os.environ.get("VERBOSE", True))

    def __init__(
        self,
        config: os.PathLike | str | None = None,
        **kwargs: Any,
    ):
        """Initialize the config class."""
        self.config_path: Path | None = None
        if config is not None:
            self.config_path = Path(os.path.normpath(config)).expanduser().absolute()
        self.llm_kwargs: dict[str, Any] = {}
        self.embedding_kwargs: dict[str, Any] = {}

        config_to_use: dict[str, Any] = self.default_config_dict() if config == "default" or config is None else self._create_config_dict(config)
        config_to_use.update(kwargs)  # type: ignore
        for key, value in config_to_use.items():
            setattr(self, key, value)
        try:
            self.retrievers: list[str] = self.parse_retrievers(self.RETRIEVER)
        except ValueError as e:
            logger.warning(
                f"{e.__class__.__name__}: {e}. Defaulting to 'tavily' retriever.",
                exc_info=True,
            )
            self.retrievers = ["tavily"]
        self._setup_llms()
        self._set_doc_path(config_to_use)

    @classmethod
    def from_path(
        cls,
        config_path: os.PathLike | str | None,
    ) -> Config:
        """Load a configuration from a path."""
        config_dict: dict[str, Any] = cls._create_config_dict(config_path)
        return cls(config_path, **config_dict)

    @classmethod
    def from_config(
        cls,
        config: dict[str, Any],
    ) -> Config:
        """Load a configuration from a dictionary."""
        config_dict: dict[str, Any] = cls._create_config_dict(config)
        return cls(None, **config_dict)

    def to_dict(self) -> dict[str, Any]:
        """Return the config as a dictionary."""
        return {k: v for k, v in self.__dict__.items() if not k.startswith("_") and k.upper() == k}

    @classmethod
    def default_config_dict(cls) -> dict[str, Any]:
        """Return the default config as a dictionary."""
        return {k: v for k, v in cls.__dict__.items() if k == k.upper() and not k.startswith("_")}

    @classmethod
    def _create_config_dict(
        cls,
        config: os.PathLike | str | dict[str, Any] | None = None,
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
        if upper_key not in Config.__annotations__:
            super().__setattr__(key, value)
            return
        env_value: str | None = os.environ.get(key)
        if env_value is None:
            super().__setattr__(key, value)
            return
        value = self.convert_env_value(
            key,
            env_value,
            Config.__annotations__[upper_key],
        )
        os.environ[upper_key] = str(value)

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

    def _set_doc_path(
        self,
        config: dict[str, Any],
    ):
        self.DOC_PATH = config.get("DOC_PATH", self.DOC_PATH)
        if not self.DOC_PATH or not self.DOC_PATH.strip():
            return
        try:
            os.makedirs(self.DOC_PATH, exist_ok=True)
        except Exception as e:
            logger.warning(
                f"Warning: Error validating doc_path: {e.__class__.__name__}: {e}. Using default doc_path.",
                exc_info=True,
            )
            self.DOC_PATH = config.get("DOC_PATH", str(Path.home().absolute()))

    @classmethod
    def load_config(
        cls,
        config_path: os.PathLike | str | None,
    ) -> dict[str, Any]:
        """Load a configuration by name."""
        if config_path is None:
            config_dict: dict[str, Any] = cls.default_config_dict()
        else:
            config_dict = cls._create_config_dict(config_path)

        # Merge with default config to ensure all keys are present
        merged_config: dict[str, Any] = cls.default_config_dict().copy()
        merged_config.update(config_dict)
        return merged_config

    @classmethod
    def list_available_configs(cls) -> list[str]:
        """List all available configuration names."""
        configs: list[str] = ["default"]
        for file in Path(os.path.expandvars(os.path.normpath(cls.CONFIG_DIR))).absolute().iterdir():
            if file.suffix.casefold() == ".json":
                configs.append(file.stem)  # Remove .json extension
        return configs

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
            raise ValueError(f"Cannot convert env value `{env_value}` to any of arg types `{args}` for key '{key}'")

        if type_hint in (bool, "bool"):
            return env_value.casefold() in ("true", "1", "yes", "on", "y")
        elif type_hint in (int, "int"):
            return int(env_value)
        elif type_hint in (float, "float"):
            return float(env_value)
        elif type_hint in (str, Any, "str"):
            return env_value
        elif origin in {list, List, dict, Dict, "list", "dict", "List", "Dict"}:
            return json.loads(env_value)
        else:
            raise ValueError(f"Unsupported type '{type_hint}' for key '{key}'")
