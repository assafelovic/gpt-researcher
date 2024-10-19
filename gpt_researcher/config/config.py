import json
import os
import warnings
from typing import Dict, Any, List, Union, Type, get_origin, get_args
from .variables.default import DEFAULT_CONFIG
from .variables.base import BaseConfig
from ..retrievers.utils import get_all_retriever_names


class Config:
    """Config class for GPT Researcher."""

    CONFIG_DIR = os.path.join(os.path.dirname(__file__), "variables")

    def __init__(self, config_name: str = "default"):
        """Initialize the config class."""
        self.config_name = config_name
        self.llm_kwargs: Dict[str, Any] = {}
        self.config_file = None

        config_to_use = self.load_config(config_name)
        self._set_attributes(config_to_use)
        self._handle_deprecated_attributes()
        self._set_llm_attributes()
        self._set_doc_path(config_to_use)
        self.load_config_file()

    def _set_attributes(self, config: Dict[str, Any]) -> None:
        for key, value in config.items():
            env_value = os.getenv(key)
            if env_value is not None:
                value = self.convert_env_value(key, env_value, BaseConfig.__annotations__[key])
            setattr(self, key.lower(), value)

        # Handle RETRIEVER with default value
        retriever_env = os.environ.get("RETRIEVER", "tavily")
        try:
            self.retrievers = self.parse_retrievers(retriever_env)
        except ValueError as e:
            print(f"Warning: {str(e)}. Defaulting to 'tavily' retriever.")
            self.retrievers = ["tavily"]

    def _handle_deprecated_attributes(self) -> None:
        _deprecation_warning = (
            "LLM_PROVIDER, FAST_LLM_MODEL and SMART_LLM_MODEL are deprecated and "
            "will be removed soon. Use FAST_LLM and SMART_LLM instead."
        )
        try:
            if self.llm_provider is not None:
                warnings.warn(_deprecation_warning, DeprecationWarning, stacklevel=2)
        except AttributeError:
            self.llm_provider = None
        try:
            if self.fast_llm_model is not None:
                warnings.warn(_deprecation_warning, DeprecationWarning, stacklevel=2)
        except AttributeError:
            self.fast_llm_model = None
        try:
            if self.smart_llm_model is not None:
                warnings.warn(_deprecation_warning, DeprecationWarning, stacklevel=2)
        except AttributeError:
            self.smart_llm_model = None

    def _set_llm_attributes(self) -> None:
        _fast_llm_provider, _fast_llm_model = self.parse_llm(self.fast_llm)
        _smart_llm_provider, _smart_llm_model = self.parse_llm(self.smart_llm)
        self.fast_llm_provider = self.llm_provider or _fast_llm_provider
        self.fast_llm_model = self.fast_llm_model or _fast_llm_model
        self.smart_llm_provider = self.llm_provider or _smart_llm_provider
        self.smart_llm_model = self.smart_llm_model or _smart_llm_model

    def _set_doc_path(self, config: Dict[str, Any]) -> None:
        self.doc_path = config['DOC_PATH']
        if self.doc_path:
            try:
                self.validate_doc_path()
            except Exception as e:
                print(f"Warning: Error validating doc_path: {str(e)}. Using default doc_path.")
                self.doc_path = DEFAULT_CONFIG['DOC_PATH']

    @classmethod
    def load_config(cls, config_name: str) -> Dict[str, Any]:
        """Load a configuration by name."""
        if config_name == "default":
            return DEFAULT_CONFIG

        config_path = os.path.join(cls.CONFIG_DIR, f"{config_name}.json")
        if not os.path.exists(config_path):
            if config_name:
                print(
                    f"Warning: Configuration '{config_name}' not found. Using default configuration.")
            return DEFAULT_CONFIG

        with open(config_path, "r") as f:
            custom_config = json.load(f)

        # Merge with default config to ensure all keys are present
        merged_config = DEFAULT_CONFIG.copy()
        merged_config.update(custom_config)
        return merged_config

    @classmethod
    def list_available_configs(cls) -> List[str]:
        """List all available configuration names."""
        configs = ["default"]
        for file in os.listdir(cls.CONFIG_DIR):
            if file.endswith(".json"):
                configs.append(file[:-5])  # Remove .json extension
        return configs

    def parse_retrievers(self, retriever_str: str) -> List[str]:
        """Parse the retriever string into a list of retrievers and validate them."""
        retrievers = [retriever.strip()
                      for retriever in retriever_str.split(",")]
        valid_retrievers = get_all_retriever_names() or []
        invalid_retrievers = [r for r in retrievers if r not in valid_retrievers]
        if invalid_retrievers:
            raise ValueError(
                f"Invalid retriever(s) found: {', '.join(invalid_retrievers)}. "
                f"Valid options are: {', '.join(valid_retrievers)}."
            )
        return retrievers

    @staticmethod
    def parse_llm(llm_str: str | None) -> tuple[str | None, str | None]:
        """Parse llm string into (llm_provider, llm_model)."""
        if llm_str is None:
            return None, None
        try:
            return llm_str.split(":", 1)
        except ValueError:
            raise ValueError(
                "Set SMART_LLM or FAST_LLM = '<llm_provider>:<llm_model_name>' "
                "Eg 'openai:gpt-4o-mini'"
            )

    def validate_doc_path(self):
        """Ensure that the folder exists at the doc path"""
        os.makedirs(self.doc_path, exist_ok=True)

    def load_config_file(self) -> None:
        """Load the config file."""
        if self.config_file is None:
            return None
        with open(self.config_file, "r") as f:
            config = json.load(f)
        for key, value in config.items():
            setattr(self, key.lower(), value)

    @staticmethod
    def convert_env_value(key: str, env_value: str, type_hint: Type) -> Any:
        """Convert environment variable to the appropriate type based on the type hint."""
        origin = get_origin(type_hint)
        args = get_args(type_hint)

        if origin is Union:
            # Handle Union types (e.g., Union[str, None])
            for arg in args:
                if arg is type(None):
                    if env_value.lower() in ('none', 'null', ''):
                        return None
                else:
                    try:
                        return Config.convert_env_value(key, env_value, arg)
                    except ValueError:
                        continue
            raise ValueError(f"Cannot convert {env_value} to any of {args}")

        if type_hint is bool:
            return env_value.lower() in ('true', '1', 'yes', 'on')
        elif type_hint is int:
            return int(env_value)
        elif type_hint is float:
            return float(env_value)
        elif type_hint in (str, Any):
            return env_value
        elif origin is list or origin is List:
            return json.loads(env_value)
        else:
            raise ValueError(f"Unsupported type {type_hint} for key {key}")
