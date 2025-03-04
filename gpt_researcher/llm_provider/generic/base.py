from __future__ import annotations

import importlib
import importlib.util
import logging
import os
import subprocess
import sys
import time
import uuid

from collections import defaultdict
from dataclasses import dataclass
from typing import TYPE_CHECKING, Any, Callable, Sequence, cast

from colorama import Fore, Style, init
from fastapi import WebSocket
from langchain_core.language_models import BaseChatModel
from langchain_core.messages import AIMessage, BaseMessage, HumanMessage, SystemMessage
from llm_fallbacks.config import FREE_MODELS, LiteLLMBaseModelSpec
from pydantic import SecretStr

if TYPE_CHECKING:
    from backend.server.server_utils import HTTPStreamAdapter

logger: logging.Logger = logging.getLogger(__name__)

# Supported LLM providers
_SUPPORTED_PROVIDERS: set[str] = {
    "anthropic",
    "azure_openai",
    "bedrock",
    "cohere",
    "dashscope",
    "deepseek",
    "fireworks",
    "gigachat",
    "google_genai",
    "google_vertexai",
    "groq",
    "huggingface",
    "litellm",
    "mistralai",
    "ollama",
    "openai",
    "together",
    "xai",
}


# New dataclass for model info
@dataclass
class ModelInfo:
    model: BaseChatModel
    model_id: str
    provider: str


# Class for error/failure tracking
class ErrorTracker:
    MAX_MODEL_FAILURES: int = 3
    MAX_PROVIDER_FAILURES: int = 5
    MAX_CONSECUTIVE_PROVIDER_FAILURES: int = 3
    FAILURE_RESET_TIME: int = 3600  # 1 hour in seconds
    MAX_ERROR_MESSAGES: int = 3

    def __init__(self) -> None:
        self.model_failures: dict[str, int] = defaultdict(int)
        self.provider_failures: dict[str, int] = defaultdict(int)
        self.consecutive_provider_failures: dict[str, int] = defaultdict(int)
        self.last_failure_time: dict[str, float] = {}
        self.error_messages: dict[str, list[str]] = defaultdict(list)

    def record_failure(
        self,
        model_id: str,
        provider: str,
        error: Exception,
    ) -> None:
        error_type: str = error.__class__.__name__
        error_msg: str = str(error)
        self.model_failures[model_id] += 1
        self.provider_failures[provider] += 1
        self.consecutive_provider_failures[provider] += 1
        self.last_failure_time[model_id] = time.time()
        if model_id in self.error_messages:
            if len(self.error_messages[model_id]) >= self.MAX_ERROR_MESSAGES:
                self.error_messages[model_id].pop(0)
            self.error_messages[model_id].append(f"{error_type}: {error_msg}")
        else:
            self.error_messages[model_id] = [f"{error_type}: {error_msg}"]
        logger.error(f"Error with model '{model_id}' (provider: {provider}): {error_type}: {error_msg}")

    def should_skip(
        self,
        model_id: str,
        provider: str,
    ) -> bool:
        if self.model_failures.get(model_id, 0) >= self.MAX_MODEL_FAILURES:
            logger.warning(f"Skipping model {model_id} due to excessive failures ({self.model_failures[model_id]})")
            return True
        if self.provider_failures.get(provider, 0) >= self.MAX_PROVIDER_FAILURES:
            logger.warning(f"Skipping provider {provider} due to excessive total failures")
            return True
        if self.consecutive_provider_failures.get(provider, 0) >= self.MAX_CONSECUTIVE_PROVIDER_FAILURES:
            logger.warning(f"Skipping provider {provider} due to excessive consecutive failures")
            return True
        return False

    def reset_expired_failures(self) -> None:
        current_time: float = time.time()
        for model_id, last_failure in list(self.last_failure_time.items()):
            if current_time - last_failure > self.FAILURE_RESET_TIME:
                if model_id in self.model_failures:
                    logger.info(f"Resetting failure count for model {model_id}")
                    del self.model_failures[model_id]
                    if model_id in self.error_messages:
                        del self.error_messages[model_id]
                provider = model_id.split(":", 1)[0] if ":" in model_id else model_id
                if provider in self.provider_failures:
                    logger.info(f"Resetting failure count for provider {provider}")
                    del self.provider_failures[provider]
                    if provider in self.consecutive_provider_failures:
                        del self.consecutive_provider_failures[provider]
                del self.last_failure_time[model_id]

    def reset_all_failures(self) -> None:
        self.model_failures.clear()
        self.provider_failures.clear()
        self.consecutive_provider_failures.clear()
        self.last_failure_time.clear()
        self.error_messages.clear()
        logger.info("Reset all model and provider failure tracking")

    def get_error_info(
        self,
        model_id: str,
    ) -> list[str]:
        return self.error_messages.get(model_id, ["No specific errors recorded"])


# Class for model instance creation
class ModelFactory:
    @staticmethod
    def extract_model_info(
        model_source: BaseChatModel | str,
    ) -> tuple[str, str]:
        if isinstance(model_source, str):
            if ":" in model_source:
                provider = model_source.split(":", 1)[0]
            elif "/" in model_source:
                provider = model_source.split("/", 1)[0]
            else:
                provider = model_source
            return model_source, provider
        else:
            return f"model_{uuid.uuid4().hex[:8]}", "unknown"

    @classmethod
    def create_model(
        cls,
        provider: str | BaseChatModel,
        **kwargs: Any,
    ) -> BaseChatModel:
        if isinstance(provider, BaseChatModel):
            return provider
        provider_name, model = provider.split(":", 1) if ":" in provider else (provider, "")
        model_name = str(kwargs.get("model", "") or model).strip().casefold()
        model_name = model_name.split(":", 1)[1] if ":" in model_name else model_name
        kwargs["model"] = model_name
        try:
            return GenericLLMProvider._create_model_for_provider(provider_name, **kwargs)
        except ImportError as e:
            init(autoreset=True)
            raise ImportError(f"{Fore.RED}Unable to import required package: {e.__class__.__name__}: {e}")  # from e
        except ValueError as e:
            raise ValueError(
                f"{Fore.RED}Unsupported provider: '{provider_name}'.\nSupported providers: [{', '.join(_SUPPORTED_PROVIDERS)}]"
            ) from e


# Class for message conversion
class MessageConverter:
    @staticmethod
    def convert_dicts_to_base(
        messages: list[dict[str, str]],
    ) -> list[BaseMessage]:
        converted: list[BaseMessage] = []
        for msg in messages:
            role: str = msg["role"]
            content: str = msg["content"]
            if role == "system":
                converted.append(SystemMessage(content=content))
            elif role == "assistant":
                converted.append(AIMessage(content=content))
            else:
                converted.append(HumanMessage(content=content))
        return converted

    @classmethod
    def convert_to_str(
        cls,
        msg: BaseMessage | str | dict | list,
    ) -> str:
        if isinstance(msg, str):
            return msg
        elif isinstance(msg, dict):
            return str(msg.get("contents", msg.get("content", msg)))
        elif isinstance(msg, BaseMessage):
            content: str | list[str | dict[str, str]] = msg.content
            if isinstance(content, list):
                return "\n".join(str(item) for item in content if str(item).strip())
            elif isinstance(content, dict):
                return str(content.get("contents", content.get("content", content)))
            else:
                return str(content)
        elif isinstance(msg, list):
            return "\n".join(cls.convert_to_str(item) for item in msg if cls.convert_to_str(item).strip())
        else:
            return str(msg)


class GenericLLMProvider:
    """A generic provider for LLM models with fallback capabilities."""

    _error_tracker: ErrorTracker = ErrorTracker()

    def __init__(
        self,
        llm: BaseChatModel | str,
        fallback_models: Sequence[BaseChatModel | str | tuple[str, LiteLLMBaseModelSpec]] | None = None,
        **llm_kwargs: Any,
    ):
        self.current_model: BaseChatModel = ModelFactory.create_model(llm, **llm_kwargs) if isinstance(llm, str) else llm
        self.fallback_models: list[BaseChatModel] = []
        self.model_info: list[ModelInfo] = []

        model_id, provider = ModelFactory.extract_model_info(llm)
        if isinstance(self.current_model, BaseChatModel):
            self.model_info.append(ModelInfo(model=self.current_model, model_id=model_id, provider=provider))

        self._setup_fallbacks(fallback_models, **llm_kwargs)

        if self.current_model not in self.fallback_models:
            self.fallback_models.insert(0, self.current_model)

        self._filter_failed_models()
        self._log_configuration()

    def _setup_fallbacks(
        self,
        fallback_models: Sequence[BaseChatModel | str | tuple[str, LiteLLMBaseModelSpec]] | None,
        **llm_kwargs: Any,
    ) -> None:
        if not fallback_models:
            self._setup_default_fallbacks(**llm_kwargs)
            return
        for model in fallback_models:
            if isinstance(model, BaseChatModel):
                self._add_preconstructed_fallback(model)
            elif isinstance(model, str):
                self._add_string_fallback(model, **llm_kwargs)
            elif isinstance(model, tuple):
                self._add_tuple_fallback(model, **llm_kwargs)

    def _setup_default_fallbacks(
        self,
        **llm_kwargs: Any,
    ) -> None:
        logger.info("No fallback models provided, using default FREE_MODELS")
        for model_name, model_spec in FREE_MODELS:
            provider = cast(str, model_spec.get("litellm_provider", "")).replace("vertex_ai-language-models", "vertex_ai")
            model_str = f"litellm:{provider}/{model_name}"
            fallback_model: BaseChatModel = ModelFactory.create_model(model_str, **llm_kwargs)
            model_id, _ = ModelFactory.extract_model_info(model_str)
            self.fallback_models.append(fallback_model)
            self.model_info.append(ModelInfo(model=fallback_model, model_id=model_id, provider=provider))

    def _add_preconstructed_fallback(
        self,
        model: BaseChatModel,
    ) -> None:
        model_id = f"model_{uuid.uuid4().hex[:8]}"
        provider = "unknown"
        self.fallback_models.append(model)
        self.model_info.append(ModelInfo(model=model, model_id=model_id, provider=provider))

    def _add_string_fallback(
        self,
        model_str: str,
        **llm_kwargs: Any,
    ) -> None:
        model_str = model_str.replace("vertex_ai-language-models", "vertex_ai")
        fallback_model: BaseChatModel = ModelFactory.create_model(model_str, **llm_kwargs)
        model_id, provider = ModelFactory.extract_model_info(model_str)
        self.fallback_models.append(fallback_model)
        self.model_info.append(ModelInfo(model=fallback_model, model_id=model_id, provider=provider))

    def _add_tuple_fallback(
        self,
        model_tuple: tuple[str, LiteLLMBaseModelSpec],
        **llm_kwargs: Any,
    ) -> None:
        model_name: str
        model_spec: LiteLLMBaseModelSpec
        model_name, model_spec = model_tuple
        provider = cast(str, model_spec.get("litellm_provider", "")).replace("vertex_ai-language-models", "vertex_ai")
        model_str = f"litellm:{provider}/{model_name}"
        fallback_model: BaseChatModel = ModelFactory.create_model(model_str, **llm_kwargs)
        model_id, _ = ModelFactory.extract_model_info(model_str)
        self.fallback_models.append(fallback_model)
        self.model_info.append(ModelInfo(model=fallback_model, model_id=model_id, provider=provider))

    def _log_configuration(self) -> None:
        current_model_info = self._get_model_info(self.current_model)
        logger.info(f"Using primary model: {current_model_info.model_id} (provider: {current_model_info.provider})")
        fallbacks: list[str] = [
            f"{self._get_model_info(model).model_id} ({self._get_model_info(model).provider})"
            for model in self.fallback_models[1:]
        ]
        if fallbacks:
            logger.info(f"Available fallbacks: {', '.join(fallbacks)}")
        else:
            logger.info("No fallback models available")
        print(f"{Fore.GREEN}{Style.BRIGHT}Using LLM provider: {Style.RESET_ALL}{self.current_model}", file=sys.__stdout__)
        if self.fallback_models[1:]:
            print(
                f"{Fore.GREEN}{Style.BRIGHT}Using fallbacks: {Style.RESET_ALL}{self.fallback_models[1:]}",
                file=sys.__stdout__,
            )

    def _get_model_info(
        self,
        model: BaseChatModel,
    ) -> ModelInfo:
        for info in self.model_info:
            if info.model is model:
                return info
        model_id = f"model_{uuid.uuid4().hex[:8]}"
        provider = "unknown"
        new_info = ModelInfo(model=model, model_id=model_id, provider=provider)
        self.model_info.append(new_info)
        return new_info

    def _filter_failed_models(self) -> None:
        self._error_tracker.reset_expired_failures()
        filtered_models: list[BaseChatModel] = []
        filtered_model_info: list[ModelInfo] = []
        for info in self.model_info:
            if self._error_tracker.should_skip(info.model_id, info.provider):
                continue
            filtered_models.append(info.model)
            filtered_model_info.append(info)
        self.fallback_models = filtered_models
        self.model_info = filtered_model_info
        if not self.fallback_models:
            logger.warning("All models have been filtered out due to failures. Resetting failure tracking.")
            self._error_tracker.reset_all_failures()

    @classmethod
    async def create_chat_completion(
        cls,
        messages: list,  # type: ignore
        model: str | None = None,
        temperature: float | None = 0.4,
        max_tokens: int | None = 16000,
        llm_provider: str | None = None,
        stream: bool | None = False,
        websocket: WebSocket | None = None,
        llm_kwargs: dict[str, Any] | None = None,
        cost_callback: Callable[[float], None] | None = None,
    ) -> str:
        if model is None:
            raise ValueError("Model cannot be None")
        if max_tokens is not None and max_tokens >= 16000:
            raise ValueError(f"Max tokens cannot be more than 16000, but got {max_tokens}")
        if llm_provider is None:
            raise ValueError("LLM provider cannot be None")
        provider: GenericLLMProvider = cls(
            llm_provider,
            model=model,
            temperature=temperature,
            max_tokens=max_tokens,
            **({} if llm_kwargs is None else llm_kwargs),
        )
        response: str = await provider.get_chat_response(
            messages,
            bool(stream),
            websocket,
        )
        if cost_callback is not None:
            from gpt_researcher.utils.costs import estimate_llm_cost

            cost_callback(estimate_llm_cost(str(messages), response))
        if not response.strip():
            logger.error(f"Failed to get response from {llm_provider} API")
            raise RuntimeError(f"Failed to get response from {llm_provider} API")
        return response

    @classmethod
    def _get_base_model(
        cls,
        provider: str | BaseChatModel,
        **kwargs: Any,
    ) -> BaseChatModel:
        if isinstance(provider, BaseChatModel):
            return provider
        provider_name: str
        model: str
        provider_name, model = provider.split(":", 1) if ":" in provider else (provider, "")
        model_name = str(kwargs.get("model", "") or model).strip().casefold()
        model_name = model_name.split(":", 1)[1] if ":" in model_name else model_name
        kwargs["model"] = model_name
        try:
            return cls._create_model_for_provider(provider_name, **kwargs)
        except ImportError as e:
            init(autoreset=True)
            raise ImportError(f"{Fore.RED}Unable to import required package: {str(e)}") from e
        except ValueError as e:
            raise ValueError(
                f"{Fore.RED}Unsupported provider: '{provider_name}'.\nSupported providers: [{', '.join(_SUPPORTED_PROVIDERS)}]"
            ) from e

    @classmethod
    def _create_model_for_provider(
        cls,
        provider: str,
        **kwargs: Any,
    ) -> BaseChatModel:
        """Create a model instance for the specified provider."""
        # Handle provider:model or provider/model format
        if ":" in provider:
            return cls._create_model_for_provider(provider.split(":")[0], **kwargs)
        elif "/" in provider:
            return cls._create_model_for_provider(provider.split("/")[0], **kwargs)

        # Create model based on provider
        if provider == "openai":
            return cls._create_openai_model(**kwargs)

        elif provider == "anthropic":
            return cls._create_anthropic_model(**kwargs)

        elif provider == "azure_openai":
            return cls._create_azure_openai_model(**kwargs)

        elif provider == "cohere":
            return cls._create_cohere_model(**kwargs)

        elif provider == "google_vertexai":
            return cls._create_google_vertexai_model(**kwargs)

        elif provider == "google_genai":
            return cls._create_google_genai_model(**kwargs)

        elif provider == "fireworks":
            return cls._create_fireworks_model(**kwargs)

        elif provider == "ollama":
            return cls._create_ollama_model(**kwargs)

        elif provider == "together":
            return cls._create_together_model(**kwargs)

        elif provider == "mistralai":
            return cls._create_mistralai_model(**kwargs)

        elif provider == "huggingface":
            return cls._create_huggingface_model(**kwargs)

        elif provider == "groq":
            return cls._create_groq_model(**kwargs)

        elif provider == "bedrock":
            return cls._create_bedrock_model(**kwargs)

        elif provider == "dashscope":
            return cls._create_dashscope_model(**kwargs)

        elif provider == "xai":
            return cls._create_xai_model(**kwargs)

        elif provider == "deepseek":
            return cls._create_deepseek_model(**kwargs)

        elif provider == "litellm":
            return cls._create_litellm_model(**kwargs)
        else:
            raise ValueError(f"Unsupported provider: {provider}")

    # Provider-specific model creation methods
    @classmethod
    def _create_openai_model(
        cls,
        **kwargs: Any,
    ) -> BaseChatModel:
        _check_pkg("langchain_openai")
        from langchain_openai import ChatOpenAI

        return ChatOpenAI(**kwargs)

    @classmethod
    def _create_anthropic_model(
        cls,
        **kwargs: Any,
    ) -> BaseChatModel:
        _check_pkg("langchain_anthropic")
        from langchain_anthropic import ChatAnthropic

        return ChatAnthropic(**kwargs)

    @classmethod
    def _create_azure_openai_model(
        cls,
        **kwargs: Any,
    ) -> BaseChatModel:
        _check_pkg("langchain_openai")
        from langchain_openai import AzureChatOpenAI

        model_name = str(kwargs.get("model", "")).strip().casefold()
        kwargs = {"azure_deployment": model_name, **kwargs}
        return AzureChatOpenAI(**kwargs)

    @classmethod
    def _create_cohere_model(
        cls,
        **kwargs: Any,
    ) -> BaseChatModel:
        _check_pkg("langchain_cohere")
        from langchain_cohere import ChatCohere

        return ChatCohere(**kwargs)

    @classmethod
    def _create_google_vertexai_model(
        cls,
        **kwargs: Any,
    ) -> BaseChatModel:
        _check_pkg("langchain_google_vertexai")
        from langchain_google_vertexai import ChatVertexAI

        return ChatVertexAI(**kwargs)

    @classmethod
    def _create_google_genai_model(
        cls,
        **kwargs: Any,
    ) -> BaseChatModel:
        _check_pkg("langchain_google_genai")
        from langchain_google_genai import ChatGoogleGenerativeAI

        return ChatGoogleGenerativeAI(**kwargs)

    @classmethod
    def _create_fireworks_model(
        cls,
        **kwargs: Any,
    ) -> BaseChatModel:
        _check_pkg("langchain_fireworks")
        from langchain_fireworks import ChatFireworks

        return ChatFireworks(**kwargs)

    @classmethod
    def _create_ollama_model(cls, **kwargs: Any) -> BaseChatModel:
        _check_pkg("langchain_community")
        from langchain_ollama import ChatOllama

        return ChatOllama(base_url=os.environ["OLLAMA_BASE_URL"], **kwargs)

    @classmethod
    def _create_together_model(
        cls,
        **kwargs: Any,
    ) -> BaseChatModel:
        _check_pkg("langchain_together")
        from langchain_together import ChatTogether

        return ChatTogether(**kwargs)

    @classmethod
    def _create_mistralai_model(
        cls,
        **kwargs: Any,
    ) -> BaseChatModel:
        _check_pkg("langchain_mistralai")
        from langchain_mistralai import ChatMistralAI

        return ChatMistralAI(**kwargs)

    @classmethod
    def _create_huggingface_model(
        cls,
        **kwargs: Any,
    ) -> BaseChatModel:
        _check_pkg("langchain_huggingface")
        from langchain_huggingface import ChatHuggingFace

        model_id = kwargs.pop("model", kwargs.pop("model_name", None))
        return ChatHuggingFace(model_id=model_id, **kwargs)

    @classmethod
    def _create_groq_model(
        cls,
        **kwargs: Any,
    ) -> BaseChatModel:
        _check_pkg("langchain_groq")
        from langchain_groq import ChatGroq

        return ChatGroq(**kwargs)

    @classmethod
    def _create_bedrock_model(
        cls,
        **kwargs: Any,
    ) -> BaseChatModel:
        _check_pkg("langchain_aws")
        from langchain_aws import ChatBedrock

        model_id = kwargs.pop("model", None) or kwargs.pop("model_name", None)
        return ChatBedrock(model=model_id, model_kwargs=kwargs)

    @classmethod
    def _create_dashscope_model(
        cls,
        **kwargs: Any,
    ) -> BaseChatModel:
        _check_pkg("langchain_dashscope")
        from langchain_dashscope import ChatDashScope

        return ChatDashScope(**kwargs)

    @classmethod
    def _create_xai_model(
        cls,
        **kwargs: Any,
    ) -> BaseChatModel:
        _check_pkg("langchain_xai")
        from langchain_xai import ChatXAI

        return ChatXAI(**kwargs)

    @classmethod
    def _create_deepseek_model(
        cls,
        **kwargs: Any,
    ) -> BaseChatModel:
        _check_pkg("langchain_openai")
        from langchain_openai import ChatOpenAI

        return ChatOpenAI(
            base_url="https://api.deepseek.com",
            api_key=SecretStr(os.environ["DEEPSEEK_API_KEY"]),
            **kwargs,
        )

    @classmethod
    def _create_litellm_model(
        cls,
        **kwargs: Any,
    ) -> BaseChatModel:
        _check_pkg("langchain_community")
        from langchain_community.chat_models.litellm import ChatLiteLLM

        return ChatLiteLLM(**kwargs)

    def _convert_to_base_messages(
        self,
        messages: list[dict[str, str]],
    ) -> list[BaseMessage]:
        """Convert dict messages to BaseMessage objects."""
        return [
            SystemMessage(content=msg["content"])
            if msg["role"] == "system"
            else AIMessage(content=msg["content"])
            if msg["role"] == "assistant"
            else HumanMessage(content=msg["content"])
            for msg in messages
        ]

    @classmethod
    def msgs_to_str(
        cls,
        msg: BaseMessage | str | dict | list,
    ) -> str:
        """Convert various message types to string.

        Handles BaseMessage, dict, list, and string formats.
        """
        if isinstance(msg, str):
            return msg
        elif isinstance(msg, dict):
            return str(msg.get("contents", msg.get("content", msg)))
        elif isinstance(msg, BaseMessage):
            content: str | list[str | dict[str, str]] = msg.content
            if isinstance(content, list):
                return "\n".join(str(item) for item in content if str(item).strip())
            elif isinstance(content, dict):
                return str(content.get("contents", content.get("content", content)))
            else:
                return str(content)
        elif isinstance(msg, list):
            # Convert each item once and filter, then join
            converted_items: list[str] = [cls.msgs_to_str(item) for item in msg]
            return "\n".join(item for item in converted_items if item.strip())
        else:
            return str(msg)

    async def get_chat_response(
        self,
        messages: list[BaseMessage | dict[str, str]],
        stream: bool,
        websocket: WebSocket | HTTPStreamAdapter | None = None,
        max_retries: int = 1,
        cost_callback: Callable[[float], None] | None = None,
        headers: dict[str, str] | None = None,
    ) -> str:
        headers = headers or {}
        self._filter_failed_models()
        if not self.fallback_models:
            logger.warning("No viable models available. Resetting failure tracking.")
            self._error_tracker.reset_all_failures()
            self.fallback_models = [self.current_model]
            info = self._get_model_info(self.current_model)
            self.model_info = [info]
        for model in self.fallback_models:
            info = self._get_model_info(model)
            if self._error_tracker.should_skip(info.model_id, info.provider):
                continue
            for retry in range(max_retries):
                try:
                    logger.info(
                        f"Attempting request with model {info.model_id} (provider: {info.provider}), attempt {retry + 1}/{max_retries}"
                    )
                    if stream:
                        return await self._stream_response(model, messages, websocket)
                    response: BaseMessage = await model.ainvoke(messages, headers=headers)
                    result: str = self.msgs_to_str(response)
                    if info.provider in self._error_tracker.consecutive_provider_failures:
                        self._error_tracker.consecutive_provider_failures[info.provider] = 0
                    if cost_callback is not None:
                        from gpt_researcher.utils.costs import estimate_llm_cost

                        cost_callback(estimate_llm_cost(self.msgs_to_str(list(messages)), result))
                    logger.info(f"Successfully got response from {info.model_id}")
                    return result
                except Exception as e:
                    logger.exception(
                        f"Error getting response from {info.provider}/{getattr(info.model, 'model', model.name)}! {e.__class__.__name__}: {e}"
                    )
                    self._error_tracker.record_failure(info.model_id, info.provider, e)
                    if retry == max_retries - 1:
                        logger.warning(f"Model {info.model_id} failed after {max_retries} attempts")
                        break
        self._raise_all_models_failed_error()
        raise ValueError("All models failed")

    async def _stream_response(
        self,
        model: BaseChatModel,
        messages: list[BaseMessage | dict[str, str]],
        websocket: WebSocket | HTTPStreamAdapter | None = None,
    ) -> str:
        info = self._get_model_info(model)
        logger.info(f"Streaming response from {info.model_id}")
        paragraph: str = ""
        response: str = ""
        try:
            async for chunk in model.astream(messages):
                content: str = self.msgs_to_str(chunk)
                response += content
                paragraph += content
                if "\n" in content:
                    await self._send_output(paragraph.strip(), websocket)
                    paragraph = ""
            if paragraph.strip():
                await self._send_output(paragraph.strip(), websocket)
            if info.provider in self._error_tracker.consecutive_provider_failures:
                self._error_tracker.consecutive_provider_failures[info.provider] = 0
            return response
        except Exception as e:
            self._error_tracker.record_failure(info.model_id, info.provider, e)
            raise

    async def _send_output(
        self,
        content: str,
        websocket: WebSocket | HTTPStreamAdapter | None = None,
    ) -> None:
        if websocket is not None:
            await websocket.send_json(
                {
                    "type": "report",
                    "output": content.strip(),
                }
            )
        logger.debug(f"{Fore.GREEN}{content.strip()}{Style.RESET_ALL}")

    def _raise_all_models_failed_error(self) -> None:
        failed_models_info: list[str] = []
        for model in self.fallback_models:
            info: ModelInfo = self._get_model_info(model)
            failures: int = self._error_tracker.model_failures.get(info.model_id, 0)
            errors: list[str] = self._error_tracker.get_error_info(info.model_id)
            failed_models_info.append(f"{info.model_id} (provider: {info.provider}, failures: {failures}, errors: {errors})")
        error_msg: str = "All models failed to generate a response. Tried:\n" + "\n".join(failed_models_info)
        logger.error(error_msg)
        raise ValueError(error_msg)


def _check_pkg(pkg: str) -> None:
    if not importlib.util.find_spec(pkg):
        pkg_kebab = pkg.replace("_", "-")
        init(autoreset=True)

        try:
            print(f"{Fore.YELLOW}Installing {pkg_kebab}...{Style.RESET_ALL}")
            subprocess.check_call([sys.executable, "-m", "pip", "install", "-U", pkg_kebab])
            print(f"{Fore.GREEN}Successfully installed {pkg_kebab}{Style.RESET_ALL}")

            # Try importing again after install
            importlib.import_module(pkg)

        except subprocess.CalledProcessError:
            raise ImportError(
                Fore.RED + f"Failed to install {pkg_kebab}. Please install manually with `pip install -U {pkg_kebab}`"
            )
