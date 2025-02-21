from __future__ import annotations

import importlib
import importlib.util
import logging
import os
import sys

from typing import TYPE_CHECKING, Any, Callable, Dict, List, cast

import litellm

from colorama import Fore, Style, init
from langchain_core.messages import BaseMessage
from litellm.exceptions import BadRequestError, ContextWindowExceededError
from pydantic import SecretStr

if TYPE_CHECKING:
    from fastapi import WebSocket
    from langchain_core.language_models import BaseChatModel
    from typing_extensions import Self


logger: logging.Logger = logging.getLogger(__name__)
litellm.set_verbose = True  # pyright: ignore[reportPrivateImportUsage]


_SUPPORTED_PROVIDERS: set[str] = {
    "anthropic",
    "azure_openai",
    "bedrock",
    "cohere",
    "dashscope",
    "deepseek",
    "fireworks",
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


class GenericLLMProvider:
    def __init__(
        self,
        llm: BaseChatModel | str,
    ):
        self.llm: BaseChatModel = llm if isinstance(llm, BaseChatModel) else self._get_base_chat_model(llm)
        self.fallback_models: list[BaseChatModel] = []
        print(
            f"Using model '{self.llm}' with fallbacks '{self.fallback_models!r}'",
            file=sys.__stdout__,
        )

    @classmethod
    async def create_chat_completion(
        cls,
        messages: list,  # type: ignore
        model: str | None = None,
        temperature: float | None = 0.4,
        max_tokens: int | None = 16000,
        llm_provider: str | None = None,
        stream: bool | None = False,
        websocket: Any | None = None,
        llm_kwargs: dict[str, Any] | None = None,
        cost_callback: Callable[[Any], None] | None = None,
    ) -> str:
        """Create a chat completion using the specified LLM provider.

        Args:
            messages (list[dict[str, str]]): The messages to send to the chat completion
            model (str, optional): The model to use. Defaults to None.
            temperature (float, optional): The temperature to use. Defaults to 0.4.
            max_tokens (int, optional): The max tokens to use. Defaults to 16000.
            stream (bool, optional): Whether to stream the response. Defaults to False.
            llm_provider (str, optional): The LLM Provider to use.
            websocket (WebSocket): The websocket used in the current request,
            cost_callback: Callback function for updating cost

        Returns:
            str: The response from the chat completion.

        Raises:
            ValueError: If model is None or max_tokens > 16000
            RuntimeError: If provider fails to get response
        """
        # validate input
        if model is None:
            raise ValueError("Model cannot be None")
        if max_tokens is not None and max_tokens > 16001:
            raise ValueError(f"Max tokens cannot be more than 16,000, but got {max_tokens}")

        # Get the provider from supported providers
        assert llm_provider is not None
        provider: Self = cls.from_provider(
            llm_provider,
            model=model,
            temperature=temperature,
            max_tokens=max_tokens,
            **(llm_kwargs or {}),
        )

        response: str = ""
        # create response
        response = await provider.get_chat_response(
            messages,
            bool(stream),
            websocket,
        )

        if cost_callback:
            from gpt_researcher.utils.costs import estimate_llm_cost

            llm_costs = estimate_llm_cost(
                str(messages),
                response,
            )
            cost_callback(llm_costs)

        if not response:
            logger.error(f"Failed to get response from {llm_provider} API")
            raise RuntimeError(f"Failed to get response from {llm_provider} API")

        return response

    @classmethod
    def from_provider(
        cls,
        provider: str,
        **kwargs: Any,
    ) -> Self:
        return cls(cls._get_base_chat_model(provider, **kwargs))

    @classmethod
    def _get_base_chat_model(
        cls,
        provider: str,
        **kwargs: Any,
    ) -> BaseChatModel:
        if provider == "openai":
            _check_pkg("langchain_openai")
            from langchain_openai import ChatOpenAI

            llm = ChatOpenAI(**kwargs)
        elif provider == "anthropic":
            _check_pkg("langchain_anthropic")
            from langchain_anthropic import ChatAnthropic

            llm = ChatAnthropic(**kwargs)
        elif provider == "azure_openai":
            _check_pkg("langchain_openai")
            from langchain_openai import AzureChatOpenAI

            if "model" in kwargs:
                model_name = kwargs.get("model", None)
                kwargs = {"azure_deployment": model_name, **kwargs}

            llm = AzureChatOpenAI(**kwargs)
        elif provider == "cohere":
            _check_pkg("langchain_cohere")
            from langchain_cohere import ChatCohere

            llm = ChatCohere(**kwargs)
        elif provider == "google_vertexai":
            _check_pkg("langchain_google_vertexai")
            from langchain_google_vertexai import ChatVertexAI

            llm = ChatVertexAI(**kwargs)
        elif provider == "google_genai":
            _check_pkg("langchain_google_genai")
            from langchain_google_genai import ChatGoogleGenerativeAI

            llm = ChatGoogleGenerativeAI(**kwargs)
        elif provider == "fireworks":
            _check_pkg("langchain_fireworks")
            from langchain_fireworks import ChatFireworks

            llm = ChatFireworks(**kwargs)
        elif provider == "ollama":
            _check_pkg("langchain_community")
            from langchain_ollama import ChatOllama

            llm = ChatOllama(base_url=os.environ["OLLAMA_BASE_URL"], **kwargs)
        elif provider == "together":
            _check_pkg("langchain_together")
            from langchain_together import ChatTogether

            llm = ChatTogether(**kwargs)
        elif provider == "mistralai":
            _check_pkg("langchain_mistralai")
            from langchain_mistralai import ChatMistralAI

            llm = ChatMistralAI(**kwargs)
        elif provider == "huggingface":
            _check_pkg("langchain_huggingface")
            from langchain_huggingface import ChatHuggingFace

            if "model" in kwargs or "model_name" in kwargs:
                model_id = kwargs.pop("model", kwargs.pop("model_name", None))
                kwargs = {"model_id": model_id, **kwargs}
            llm = ChatHuggingFace(**kwargs)
        elif provider == "groq":
            _check_pkg("langchain_groq")
            from langchain_groq import ChatGroq

            llm = ChatGroq(**kwargs)
        elif provider == "bedrock":
            _check_pkg("langchain_aws")
            from langchain_aws import ChatBedrock

            if "model" in kwargs or "model_name" in kwargs:
                model_id = kwargs.pop("model", None) or kwargs.pop("model_name", None)
                kwargs = {
                    "model_id": model_id,
                    "model_kwargs": kwargs,
                }
            llm = ChatBedrock(**kwargs)
        elif provider == "dashscope":
            _check_pkg("langchain_dashscope")
            from langchain_dashscope import ChatDashScope

            llm = ChatDashScope(**kwargs)
        elif provider == "xai":
            _check_pkg("langchain_xai")
            from langchain_xai import ChatXAI

            llm = ChatXAI(**kwargs)
        elif provider == "deepseek":
            _check_pkg("langchain_openai")
            from langchain_openai import ChatOpenAI

            llm = ChatOpenAI(
                base_url="https://api.deepseek.com",
                api_key=SecretStr(os.environ["DEEPSEEK_API_KEY"]),
                **kwargs,
            )
        elif provider == "litellm":
            _check_pkg("langchain_community")
            from langchain_community.chat_models.litellm import ChatLiteLLM

            print(repr(kwargs))
            llm = ChatLiteLLM(**kwargs)
        else:
            supported = ", ".join(_SUPPORTED_PROVIDERS)
            raise ValueError(f"Unsupported provider: '{provider}'.\nSupported model providers are:\n[{supported}]\n")
        return llm

    def _convert_to_base_messages(self, messages: list[dict[str, str]]) -> list[BaseMessage]:
        """Convert dict messages to BaseMessage objects."""
        from langchain_core.messages import AIMessage, HumanMessage, SystemMessage

        converted: list[BaseMessage] = []
        for msg in messages:
            role: str = msg["role"]
            content: str = msg["content"]
            if role == "system":
                converted.append(SystemMessage(content=content))
            elif role == "assistant":
                converted.append(AIMessage(content=content))
            else:  # user or default
                converted.append(HumanMessage(content=content))
        return converted

    async def get_chat_response(
        self,
        messages: list[dict[str, str]] | list[BaseMessage],
        stream: bool,
        websocket: WebSocket | None = None,
        max_retries: int = 10,
        headers: dict[str, str] | None = None,
    ) -> str:
        """Get chat response with fallback support.

        Args:
            messages: List of message dicts or BaseMessage objects
            stream: Whether to stream the response
            websocket: Optional websocket for streaming
            max_retries: Maximum number of retries per model

        Returns:
            The response text
        """
        headers = {} if headers is None else headers
        current_model: BaseChatModel = self.llm
        for model in (current_model, *self.fallback_models):
            retries = 0
            while retries < max_retries:
                try:
                    if stream:
                        msgs: list[dict[str, Any]] = cast(List[Dict[str, Any]], messages)
                        return await self.stream_response(msgs, websocket, headers)
                    response: BaseMessage = await model.ainvoke(messages, headers=headers)
                    return "\n".join(" ".join(entry) for entry in response)
                except ContextWindowExceededError:
                    logger.warning("Context window exceeded, trying fallback models...", exc_info=True)
                    break  # Move to the next model
                except BadRequestError as e:
                    logger.exception(f"Bad request error with model '{model}': {e}, retrying {retries}/{max_retries}")
                except Exception as e:
                    logger.exception(f"Error with model '{model}': {e.__class__.__name__}: {e}, retrying {retries}/{max_retries}")
                    retries += 1
                    if retries == max_retries:
                        if self.fallback_models and model == self.fallback_models[-1]:  # Last model in tuple
                            raise ValueError(f"All models failed. Last error: {e.__class__.__name__}: {e}")
                        break  # Move to the next model
                    continue
        raise ValueError("All models failed to generate a response")

    async def _send_output(
        self,
        content: str,
        websocket: WebSocket | None = None,
    ):
        """Helper to send output to websocket or console."""
        if websocket is not None:
            await websocket.send_json(
                {
                    "type": "report",
                    "output": content.strip(),
                }
            )
        logger.debug(f"{Fore.GREEN}{content.strip()}{Style.RESET_ALL}")


def _check_pkg(pkg: str) -> None:
    if not importlib.util.find_spec(pkg):
        pkg_kebab = pkg.replace("_", "-")
        # Import colorama and initialize it
        init(autoreset=True)
        # Use Fore.RED to color the error message
        raise ImportError(Fore.RED + f"Unable to import {pkg_kebab}. Please install with `pip install -U {pkg_kebab}`")
