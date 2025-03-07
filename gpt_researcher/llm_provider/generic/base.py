from __future__ import annotations

import importlib
import importlib.util
import os
import subprocess
import sys
import time
import re

from collections import defaultdict
from typing import TYPE_CHECKING, Any, Callable, ClassVar, Sequence, cast, Type, TypeVar

from colorama import Fore, Style, init
from langchain_core.language_models import BaseChatModel
from langchain_core.messages import AIMessage, BaseMessage, HumanMessage, SystemMessage
from llm_fallbacks.config import FREE_MODELS
from pydantic import SecretStr, BaseModel

from gpt_researcher.utils.logger import get_formatted_logger
import json_repair

if TYPE_CHECKING:
    import logging

    from fastapi import WebSocket
    from llm_fallbacks.config import LiteLLMBaseModelSpec

logger: logging.Logger = get_formatted_logger("GenericLLMProvider")



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



class ErrorTracker:
    MAX_MODEL_FAILURES: ClassVar[int] = 3
    MAX_PROVIDER_FAILURES: ClassVar[int] = 25
    MAX_CONSECUTIVE_PROVIDER_FAILURES: ClassVar[int] = 50
    FAILURE_RESET_TIME: ClassVar[int] = 300
    MAX_ERROR_MESSAGES: ClassVar[int] = 3

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

                provider: str = model_id.split(":", 1)[0] if ":" in model_id else model_id
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

    def mark_provider_permanently_failed(self, provider: str) -> None:
        self.provider_failures[provider] = self.MAX_PROVIDER_FAILURES
        logger.warning(f"Provider '{provider}' marked as permanently failed due to billing issues.")



class ModelFactory:
    @staticmethod
    def extract_model_info(
        model_source: str,
    ) -> tuple[str, str]:
        """Extract the provider and model ID from a model source string.
        
        Args:
            model_source: The model source string to extract the provider and model ID from.
            
        Returns:
            A tuple containing the provider and model ID.

        Raises:
            ValueError: If the model source is not in the format 'provider:model' or 'provider/model'.
            TypeError: If the model source is not a string.
        """
        if not isinstance(model_source, str):
            raise TypeError(f"Model source must be a string, got {model_source.__class__.__name__}")

        provider, model_id = (
            model_source.split(":", 1)
            if ":" in model_source
            else model_source.split("/", 1)
            if "/" in model_source
            else (None, None)
        )
        if not provider or not model_id:
            raise ValueError(f"Invalid model source: '{model_source}': must be in the format 'provider:model' or 'provider/model'")
        assert model_id.casefold() != "free", f"bug in model source parsing: {model_source}"
        return provider, model_id

    @classmethod
    def create_model(
        cls,
        provider: str | BaseChatModel,
        **kwargs: Any,
    ) -> BaseChatModel:
        """Create a model instance for the specified provider.

        Args:
            provider: The provider string or an existing BaseChatModel instance.
            **kwargs: Additional keyword arguments to pass to the model constructor.

        Returns:
            A BaseChatModel instance.
        """
        if isinstance(provider, BaseChatModel):
            return provider
        provider_name, model = provider.split(":", 1) if ":" in provider else (provider, "")
        model_name: str = str(kwargs.pop("model", "") or model).strip().casefold()
        try:
            return GenericLLMProvider._create_model_for_provider(provider_name, model=model_name, **kwargs)
        except ImportError as e:
            init(autoreset=True)
            raise ImportError(f"{Fore.RED}Unable to import required package: {e.__class__.__name__}: {e}")
        except ValueError as e:
            raise ValueError(f"{Fore.RED}Unsupported provider: '{provider_name}'.\nSupported providers: [{', '.join(_SUPPORTED_PROVIDERS)}]. {e.__class__.__name__}: {e}")



class MessageConverter:
    @staticmethod
    def convert_dicts_to_base(
        messages: list[dict[str, str]],
    ) -> list[BaseMessage]:
        """Convert dictionary messages to BaseMessage objects.

        Args:
            messages: List of message dictionaries with 'role' and 'content' keys

        Returns:
            List of BaseMessage objects
        """
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
        """Convert various message types to string.

        Args:
            msg: Message to convert (BaseMessage, string, dict, or list)

        Returns:
            String representation of the message
        """
        if isinstance(msg, str):
            return msg
        elif isinstance(msg, dict):
            return str(msg.get("contents", msg.get("content", msg)))
        elif isinstance(msg, BaseMessage):
            content: str | list[str | dict[str, str]] = msg.content
            if isinstance(content, list):
                return " ".join(str(item) for item in content if str(item).strip())
            elif isinstance(content, dict):
                return str(content.get("contents", content.get("content", content)))
            else:
                return str(content)
        elif isinstance(msg, list):
            return " ".join(cls.convert_to_str(item) for item in msg if cls.convert_to_str(item).strip())
        else:
            return str(msg)



T = TypeVar('T', bound=BaseModel)


class GenericLLMProvider:
    """A generic provider for LLM models with fallback capabilities."""

    _error_tracker: ClassVar[ErrorTracker] = ErrorTracker()

    def __init__(
        self,
        llm: str,
        fallback_models: Sequence[str | tuple[str, LiteLLMBaseModelSpec]] | None = None,
        **llm_kwargs: Any,
    ):
        self.fallback_models: list[BaseChatModel] = []
        self.model_to_info: dict[int, dict[str, str]] = {}
        self.model_id_to_model: dict[str, BaseChatModel] = {}
        self.model_to_litellm_spec: dict[int, LiteLLMBaseModelSpec] = {}
        if isinstance(llm, str):
            self.current_model: BaseChatModel = ModelFactory.create_model(llm, **llm_kwargs)
            provider: str
            model_id: str
            provider, model_id = ModelFactory.extract_model_info(llm)
            self._add_model_info(self.current_model, provider, model_id)
        else:
            self.current_model = llm
            self._add_model_info(self.current_model, "", getattr(llm, "model_name", ""))
        self._setup_fallbacks(fallback_models, **llm_kwargs)
        if self.current_model not in self.fallback_models:
            self.fallback_models.insert(0, self.current_model)
        self._filter_failed_models()

    def _add_model_info(
        self, 
        model: BaseChatModel, 
        provider: str, 
        model_id: str,
        litellm_spec: LiteLLMBaseModelSpec | None = None
    ) -> None:
        """Add model information to the tracking dictionaries.

        Args:
            model: The BaseChatModel instance
            provider: The provider name
            model_id: The model ID
            litellm_spec: Optional LiteLLMBaseModelSpec for LiteLLM models
        """
        self.model_to_info[id(model)] = {"provider": provider, "model_id": model_id}
        self.model_id_to_model[f"{provider}:{model_id}"] = model
        if litellm_spec is not None:
            self.model_to_litellm_spec[id(model)] = litellm_spec

    def _setup_fallbacks(
        self,
        fallback_models: Sequence[BaseChatModel | str | tuple[str, LiteLLMBaseModelSpec]] | None,
        **llm_kwargs: Any,
    ) -> None:
        """Set up fallback models.

        Args:
            fallback_models: Sequence of fallback models
            **llm_kwargs: Additional keyword arguments to pass to model constructors
        """
        if not fallback_models:
            self._setup_default_fallbacks(**llm_kwargs)
            return

        for model in fallback_models:
            if isinstance(model, BaseChatModel):
                self._add_model_instance(model)
            elif isinstance(model, str):
                self._add_string_fallback(model, **llm_kwargs)
            elif isinstance(model, tuple):
                self._add_tuple_fallback(model, **llm_kwargs)

    def _add_model_instance(self, model: BaseChatModel) -> None:
        """Add a BaseChatModel instance to fallbacks.

        Args:
            model: The BaseChatModel instance to add
        """
        if model not in self.fallback_models:
            self.fallback_models.append(model)


        if model not in self.model_to_info:
            model_name: str = getattr(model, "model_name", "")
            provider: str = getattr(model, "provider", "")
            self._add_model_info(model, provider, model_name)

    def _setup_default_fallbacks(
        self,
        **llm_kwargs: Any,
    ) -> None:
        """Set up default fallback models from FREE_MODELS.

        Args:
            **llm_kwargs: Additional keyword arguments to pass to model constructors
        """
        logger.info("No fallback models provided, using default FREE_MODELS")
        for model_name, model_spec in FREE_MODELS:
            provider: str = str(model_spec.get("litellm_provider", "")).replace("vertex_ai-language-models", "vertex_ai")
            model_str: str = f"litellm:{provider}/{model_name}"
            fallback_model: BaseChatModel = ModelFactory.create_model(model_str, **llm_kwargs)
            provider, model_id = ModelFactory.extract_model_info(model_str)

            self.fallback_models.append(fallback_model)
            self._add_model_info(fallback_model, provider, model_id, model_spec)

    def _add_string_fallback(
        self,
        model_str: str,
        **llm_kwargs: Any,
    ) -> None:
        """Add a fallback model from a string.
        
        Args:
            model_str: The model string
            **llm_kwargs: Additional keyword arguments to pass to the model constructor
        """
        model_str = model_str.replace("vertex_ai-language-models", "vertex_ai")
        fallback_model: BaseChatModel = ModelFactory.create_model(model_str, **llm_kwargs)

        self.fallback_models.append(fallback_model)
        provider, model_id = ModelFactory.extract_model_info(model_str)
        self._add_model_info(fallback_model, provider, model_id)

    def _add_tuple_fallback(
        self,
        model_tuple: tuple[str, LiteLLMBaseModelSpec],
        **llm_kwargs: Any,
    ) -> None:
        """Add a fallback model from a tuple of (model_name, model_spec).
        
        Args:
            model_tuple: Tuple of (model_name, LiteLLMBaseModelSpec)
            **llm_kwargs: Additional keyword arguments to pass to the model constructor
        """
        model_name: str
        model_spec: LiteLLMBaseModelSpec
        model_name, model_spec = model_tuple
        provider: str = cast(str, model_spec.get("litellm_provider", "")).replace("vertex_ai-language-models", "vertex_ai")
        model_str: str = f"litellm:{provider}/{model_name}"
        fallback_model: BaseChatModel = ModelFactory.create_model(model_str, **llm_kwargs)
        provider, model_id = ModelFactory.extract_model_info(model_str)
        self.fallback_models.append(fallback_model)
        self._add_model_info(fallback_model, provider, model_id, model_spec)

    def _filter_failed_models(self) -> None:
        """Filter out models that have failed too many times."""
        self._error_tracker.reset_expired_failures()
        filtered_models: list[BaseChatModel] = []
        for model in self.fallback_models:
            info: dict[str, str] = self.model_to_info.get(id(model), {})
            provider: str = info.get("provider", "")
            model_id: str = info.get("model_id", "")
            if self._error_tracker.should_skip(model_id, provider):
                continue
            filtered_models.append(model)
        self.fallback_models = filtered_models
        if not self.fallback_models:
            logger.warning("All models have been filtered out due to failures. Resetting failure tracking.")
            self._error_tracker.reset_all_failures()


    def _add_ollama_fallbacks(self) -> None:
        try:
            logger.info("Adding Ollama models as ultimate fallback...")
            ollama_models: list[str] = [
                "deepseek-r1-distill-llama-8b-abliterated",
                "deepseek-r1-distill-qwen-1.5b-abliterated-dpo"
                "deepseek-r1-distill-qwen-1.5b-abliterated-dpo",
                "deepseek-r1-distill-qwen-7b-abliterated-v2",
                "dolphin3.0-qwen2.5-3b",
                "dolphin3.0-r1-mistral-24b-abliterated",
                "gemma-2-9b-it-abliterated",
                "hermes-3-llama-3.2-3b-abliterated",
                "phi-4-abliteratedrp-i1",
                "qwen2.5-7b-instruct-abliterated-v3",
            ]
            for model_name in ollama_models:
                try:
                    ollama_model: BaseChatModel = self._create_model_for_provider("ollama", model=model_name)
                    if ollama_model not in self.fallback_models:
                        self.fallback_models.append(ollama_model)
                        self._add_model_info(ollama_model, "ollama", model_name)
                        logger.info(f"Added Ollama model: {model_name}")
                except Exception as e:
                    logger.warning(f"Failed to add Ollama model {model_name}: {e.__class__.__name__}: {e}")
        except Exception as e:
            logger.warning(f"Failed to add Ollama models: {e.__class__.__name__}: {e}")

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
        if kwargs.get("model"):
            model_name: str = str(kwargs.get("model", "")).strip().casefold()
            if ":" in model_name:
                model_name = model_name.split(":", 1)[1]
        else:

            model_name = model.strip().casefold()
        kwargs["model"] = model_name
        try:
            return cls._create_model_for_provider(provider_name, **kwargs)
        except ImportError as e:
            init(autoreset=True)
            raise ImportError(f"{Fore.RED}Unable to import required package: {str(e)}") from e
        except ValueError as e:
            raise ValueError(f"{Fore.RED}Unsupported provider: '{provider_name}'.\nSupported providers: [{', '.join(_SUPPORTED_PROVIDERS)}]") from e

    @classmethod
    def _create_model_for_provider(
        cls,
        provider: str,
        **kwargs: Any,
    ) -> BaseChatModel:
        """Create a model instance for the specified provider.

        Args:
            provider: The provider name
            **kwargs: Additional keyword arguments to pass to the model constructor

        Returns:
            A BaseChatModel instance

        Raises:
            ValueError: If the provider is not supported
        """

        if ":" in provider:
            return cls._create_model_for_provider(provider.split(":", 1)[0], **kwargs)
        elif "/" in provider:
            return cls._create_model_for_provider(provider.split("/", 1)[0], **kwargs)

        if provider == "openai":
            _check_pkg("langchain_openai")
            from langchain_openai import ChatOpenAI
            return ChatOpenAI(**kwargs)

        elif provider == "anthropic":
            _check_pkg("langchain_anthropic")
            from langchain_anthropic import ChatAnthropic
            return ChatAnthropic(**kwargs)

        elif provider == "azure_openai":
            _check_pkg("langchain_openai")
            from langchain_openai import AzureChatOpenAI
            model_name: str = str(kwargs.get("model", "") or kwargs.get("model_name", "")).strip().casefold()
            kwargs = {"azure_deployment": model_name, **kwargs}
            return AzureChatOpenAI(**kwargs)

        elif provider == "cohere":
            _check_pkg("langchain_cohere")
            from langchain_cohere import ChatCohere
            return ChatCohere(**kwargs)

        elif provider == "google_vertexai":
            _check_pkg("langchain_google_vertexai")
            from langchain_google_vertexai import ChatVertexAI
            return ChatVertexAI(**kwargs)

        elif provider == "google_genai":
            _check_pkg("langchain_google_genai")
            from langchain_google_genai import ChatGoogleGenerativeAI
            return ChatGoogleGenerativeAI(**kwargs)

        elif provider == "fireworks":
            _check_pkg("langchain_fireworks")
            from langchain_fireworks import ChatFireworks
            return ChatFireworks(**kwargs)

        elif provider == "ollama":
            _check_pkg("langchain_ollama")
            from langchain_ollama import ChatOllama
            return ChatOllama(base_url=os.environ["OLLAMA_BASE_URL"], **kwargs)

        elif provider == "together":
            _check_pkg("langchain_together")
            from langchain_together import ChatTogether
            return ChatTogether(**kwargs)

        elif provider == "mistralai":
            _check_pkg("langchain_mistralai")
            from langchain_mistralai import ChatMistralAI
            return ChatMistralAI(**kwargs)

        elif provider == "huggingface":
            _check_pkg("langchain_huggingface")
            from langchain_huggingface import ChatHuggingFace
            model_id: str = kwargs.pop("model", kwargs.pop("model_name", None))
            return ChatHuggingFace(model_id=model_id, **kwargs)

        elif provider == "groq":
            _check_pkg("langchain_groq")
            from langchain_groq import ChatGroq
            return ChatGroq(**kwargs)

        elif provider == "bedrock":
            _check_pkg("langchain_aws")
            from langchain_aws import ChatBedrock
            model_id = kwargs.pop("model", None) or kwargs.pop("model_name", None)
            return ChatBedrock(model=model_id, model_kwargs=kwargs)

        elif provider == "dashscope":
            _check_pkg("langchain_dashscope")
            from langchain_dashscope import ChatDashScope
            return ChatDashScope(**kwargs)

        elif provider == "xai":
            _check_pkg("langchain_xai")
            from langchain_xai import ChatXAI
            return ChatXAI(**kwargs)

        elif provider == "deepseek":
            _check_pkg("langchain_openai")
            from langchain_openai import ChatOpenAI
            return ChatOpenAI(
                base_url="https://api.deepseek.com",
                api_key=SecretStr(os.environ["DEEPSEEK_API_KEY"]),
                **kwargs,
            )

        elif provider == "litellm":
            _check_pkg("langchain_community")
            from langchain_community.chat_models.litellm import ChatLiteLLM
            return ChatLiteLLM(**kwargs)

        else:
            raise ValueError(f"Unsupported provider: '{provider}'")

    async def get_chat_response(
        self,
        messages: list[BaseMessage] | list[dict[str, str]],
        stream: bool,
        websocket: WebSocket | None = None,
        max_retries: int = 1,
        cost_callback: Callable[[float], None] | None = None,
        headers: dict[str, str] | None = None,
    ) -> str:
        headers = headers or {}
        self._filter_failed_models()

        for model in (self.current_model, *self.fallback_models):
            info: dict[str, str] = self.model_to_info.get(id(model), {"provider": "", "model_id": ""})
            provider: str = info.get("provider", "")
            model_id: str = info.get("model_id", "")

            if provider and model_id and self._error_tracker.should_skip(model_id, provider):
                continue
            for retry in range(max_retries):
                try:
                    logger.info(f"Attempting request with model {model_id} (provider: {provider}), attempt {retry + 1}/{max_retries}")
                    if stream:
                        return await self._stream_response(model, messages, websocket)
                    response: BaseMessage = await model.ainvoke(messages, headers=headers)
                    result: str = MessageConverter.convert_to_str(response)
                    if provider in self._error_tracker.consecutive_provider_failures:
                        self._error_tracker.consecutive_provider_failures[provider] = 0
                    if cost_callback is not None:
                        from gpt_researcher.utils.costs import estimate_llm_cost

                        cost_callback(estimate_llm_cost(MessageConverter.convert_to_str(list(messages)), result))
                except Exception as e:
                    error_message = str(e)
                    if (
                        "Please enable billing on project" in error_message
                        or "If you enabled billing for this project" in error_message
                    ) and (e.__class__.__name__ == "VertexAIError" or provider == "vertex_ai"):
                        self._error_tracker.mark_provider_permanently_failed(provider)
                        break
                    logger.exception(f"Error getting response from {provider}/{getattr(model, 'model', model.name)}! {e.__class__.__name__}: {e}")
                    self._error_tracker.record_failure(model_id, provider, e)
                    if retry == max_retries - 1:
                        logger.warning(f"Model {model_id} failed after {max_retries} attempts")
                        break
                else:
                    logger.debug(f"Successfully got response from {model_id}")
                    return result

        self._raise_all_models_failed_error()
        raise ValueError("All models failed")

    async def _stream_response(
        self,
        model: BaseChatModel,
        messages: list[BaseMessage] | list[dict[str, str]],
        websocket: WebSocket | None = None,
    ) -> str:
        info: dict[str, str] = self.model_to_info.get(id(model), {"provider": "", "model_id": ""})
        provider: str = info.get("provider", "")
        model_id: str = info.get("model_id", "")

        logger.info(f"Streaming response from {model_id}")
        paragraph: str = ""
        response: str = ""
        try:
            async for chunk in model.astream(messages):
                content: str = MessageConverter.convert_to_str(chunk)
                response += content
                paragraph += content
                if "\n" in content:
                    await self._send_output(paragraph.strip(), websocket)
                    paragraph = ""
            if paragraph.strip():
                await self._send_output(paragraph.strip(), websocket)
            if provider in self._error_tracker.consecutive_provider_failures:
                self._error_tracker.consecutive_provider_failures[provider] = 0
            return response
        except Exception as e:
            self._error_tracker.record_failure(model_id, provider, e)
            raise

    async def _send_output(
        self,
        content: str,
        websocket: WebSocket | None = None,
    ) -> None:
        if websocket is not None:
            await websocket.send_json({"type": "report", "output": content.strip()})
        logger.debug(f"{Fore.GREEN}{content.strip()}{Style.RESET_ALL}")

    def _raise_all_models_failed_error(self) -> None:
        failed_models_info: list[str] = []
        for model in self.fallback_models:
            info: dict[str, str] = self.model_to_info.get(id(model), {"provider": "", "model_id": ""})
            provider: str = info.get("provider", "")
            model_id: str = info.get("model_id", "")
            failures: int = self._error_tracker.model_failures.get(model_id, 0)
            errors: list[str] = self._error_tracker.get_error_info(model_id)
            failed_models_info.append(f"{model_id} (provider: {provider}, failures: {failures}, errors: {errors})")
        error_msg: str = "All models failed to generate a response. Tried:\n" + "\n".join(failed_models_info)
        raise ValueError(error_msg)

    async def get_structured_response(
        self,
        messages: list[BaseMessage] | list[dict[str, str]],
        response_model: Type[T],
        stream: bool = False,
        websocket: WebSocket | None = None,
        max_retries: int = 1,
        cost_callback: Callable[[float], None] | None = None,
        headers: dict[str, str] | None = None,
    ) -> T:
        """Get a structured JSON response using Pydantic models.
        
        This method uses structured output capabilities to ensure
        the response is properly formatted according to the provided Pydantic model.
        
        Args:
            messages: List of message dictionaries to send to the model
            response_model: Pydantic model class that defines the expected response structure
            stream: Whether to stream the response
            websocket: Optional websocket for streaming
            max_retries: Maximum number of retries
            cost_callback: Optional callback for cost tracking
            headers: Optional headers for the request
            
        Returns:
            An instance of the provided Pydantic model
        """
        headers = headers or {}
        self._filter_failed_models()
        if not self.fallback_models:
            logger.warning("No viable models available. Resetting failure tracking.")
            self._error_tracker.reset_all_failures()
            self.fallback_models = [self.current_model]
        for model in self.fallback_models:
            info: dict[str, str] = self.model_to_info.get(id(model), {"provider": "", "model_id": ""})
            provider: str = info.get("provider", "")
            model_id: str = info.get("model_id", "")
            if self._error_tracker.should_skip(model_id, provider):
                continue
            for retry in range(max_retries):
                try:
                    logger.info(f"Attempting structured JSON request with model {model_id} (provider: {provider}), attempt {retry + 1}/{max_retries}")
                    if stream:
                        logger.warning("Streaming is not supported for structured responses. Disabling streaming.")
                        stream = False
                    schema: dict[str, Any] = response_model.model_json_schema()
                    formatted_messages: list[BaseMessage | dict[str, str]] = list(messages)
                    has_system_message: bool = False
                    for msg in formatted_messages:
                        if isinstance(msg, dict) and msg.get("role") == "system":
                            has_system_message = True
                            break
                        elif not isinstance(msg, dict) and msg.type == "system":
                            has_system_message = True
                            break
                    if not has_system_message:
                        system_message_content = f"You are a helpful assistant that always responds in JSON format according to this schema: {schema}"
                        if all(isinstance(msg, dict) for msg in formatted_messages):
                            formatted_messages.insert(0, {"role": "system", "content": system_message_content})
                        else:
                            from langchain_core.messages import SystemMessage
                            formatted_messages.insert(0, SystemMessage(content=system_message_content))
                    response: BaseMessage = await model.ainvoke(
                        formatted_messages, 
                        headers=headers,
                        response_format={"type": "json_object", "schema": schema}
                    )
                    result_text: str = MessageConverter.convert_to_str(response)
                    if cost_callback is not None:
                        from gpt_researcher.utils.costs import estimate_llm_cost
                        cost_callback(estimate_llm_cost(MessageConverter.convert_to_str(list(messages)), result_text))
                    if provider in self._error_tracker.consecutive_provider_failures:
                        self._error_tracker.consecutive_provider_failures[provider] = 0
                    
                    logger.debug(f"Successfully got response from {model_id}")
                    return self._parse_to_pydantic_model(result_text, response_model)
                except Exception as e:
                    error_message = str(e)
                    if (
                        "Please enable billing on project" in error_message
                        or "If you enabled billing for this project" in error_message
                    ) and (e.__class__.__name__ == "VertexAIError" or provider == "vertex_ai"):
                        self._error_tracker.mark_provider_permanently_failed(provider)
                        break
                    logger.exception(
                        f"Error getting structured response from {provider}/{getattr(model, 'model', model.name)}! {e.__class__.__name__}: {e}"
                    )
                    self._error_tracker.record_failure(model_id, provider, e)
                    if retry == max_retries - 1:
                        logger.warning(f"Model {model_id} failed after {max_retries} attempts")
                        break
        self._raise_all_models_failed_error()
        raise ValueError("All models failed to provide a structured response")
    
    def _parse_to_pydantic_model(self, text: str, model_class: Type[T]) -> T:
        """Parse a text response into a Pydantic model.
        
        This method tries multiple approaches to extract valid JSON from the response
        and parse it into the specified Pydantic model.
        
        Args:
            text: The text response from the model
            model_class: The Pydantic model class to parse into
            
        Returns:
            An instance of the provided Pydantic model
            
        Raises:
            ValueError: If the response cannot be parsed into the model
        """
        try:
            return model_class.model_validate_json(text)
        except Exception:
            pass
        try:
            json_match: re.Match[str] | None = re.search(r'```(?:json)?\s*([\s\S]*?)\s*```', text)
            if json_match:
                json_str: str = json_match.group(1)
                return model_class.model_validate_json(json_str)
        except Exception:
            pass
        try:
            function_match: re.Match[str] | None = re.search(r'"function_call":\s*{[^}]*"arguments":\s*"([^"]*)"', text.replace("\n", ""))
            if function_match:
                args_str: str = function_match.group(1).replace("\\", "")
                return model_class.model_validate_json(args_str)
        except Exception:
            pass
        try:
            return model_class.model_validate(json_repair.loads(text))
        except Exception as e:
            raise ValueError(f"Failed to parse response as {model_class.__name__}! {e.__class__.__name__}: {e}\nResponse: {text[:500]}...")


def _check_pkg(pkg: str) -> None:
    if not importlib.util.find_spec(pkg):
        pkg_kebab: str = pkg.replace("_", "-")
        init(autoreset=True)
        try:
            logger.info(f"{Fore.YELLOW}Installing {pkg_kebab}...{Style.RESET_ALL}")
            subprocess.check_call([sys.executable, "-m", "pip", "install", "-U", pkg_kebab])
            logger.info(f"{Fore.GREEN}Successfully installed {pkg_kebab}{Style.RESET_ALL}")
            importlib.import_module(pkg)
        except subprocess.CalledProcessError:
            raise ImportError(Fore.RED + f"Failed to install {pkg_kebab}. Please install manually with `pip install -U {pkg_kebab}`")
