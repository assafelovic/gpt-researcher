from __future__ import annotations

import asyncio
import importlib
import importlib.util
import json
import os
import subprocess
import sys
import time
import traceback
from enum import Enum
from typing import TYPE_CHECKING, Any, ClassVar

import aiofiles
import tiktoken
from colorama import Fore, Style, init
from langchain_core.language_models.chat_models import BaseChatModel
from langchain_core.messages import BaseMessage

# Import the LLM debug logger
try:
    from gpt_researcher.utils.llm_debug_logger import (
        get_llm_debug_logger,
        initialize_llm_debug_logger,
    )
except ImportError:
    # Fallback if the debug logger is not available
    get_llm_debug_logger = None
    initialize_llm_debug_logger = None

# Attempt to import specific error types, fallback to general Exception
try:
    from openai import BadRequestError as OpenAIBadRequestError
except ImportError:
    OpenAIBadRequestError = None  # pyright: ignore[reportAssignmentIssue]

try:
    from anthropic import APIError as AnthropicAPIError  # pyright: ignore[reportMissingImports]
except ImportError:
    AnthropicAPIError = None  # pyright: ignore[reportAssignmentIssue]


if TYPE_CHECKING:
    from fastapi import WebSocket
    from typing_extensions import Self


_SUPPORTED_PROVIDERS: set[str] = {
    "aimlapi",
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
    "openrouter",
    "together",
    "vllm_openai",
    "xai",
}

NO_SUPPORT_TEMPERATURE_MODELS: list[str] = [
    "deepseek/deepseek-reasoner",
    "o1-2024-12-17",
    "o1-mini-2024-09-12",
    "o1-mini",
    "o1-preview",
    "o1-preview",
    "o1",
    "o3-2025-04-16",
    "o3-mini-2025-01-31",
    "o3-mini",
    "o3",
    "o4-mini-2025-04-16",
    "o4-mini",
    # GPT-5 family: OpenAI enforces default temperature only
    "gpt-5",
    "gpt-5-mini",
]

SUPPORT_REASONING_EFFORT_MODELS: list[str] = [
    "o3-mini",
    "o3-mini-2025-01-31",
    "o3",
    "o3-2025-04-16",
    "o4-mini",
    "o4-mini-2025-04-16",
]


class ReasoningEfforts(Enum):
    High = "high"
    Medium = "medium"
    Low = "low"


class ChatLogger:
    """Helper utility to log all chat requests and their corresponding responses plus the stack trace leading to the call."""

    def __init__(self, fname: str):
        self.fname: str = fname
        self._lock: asyncio.Lock = asyncio.Lock()

    async def log_request(
        self,
        messages: list[dict[str, str]],
        response: str,
    ) -> None:
        async with self._lock:
            async with aiofiles.open(self.fname, mode="a", encoding="utf-8") as handle:
                await handle.write(
                    json.dumps(
                        {
                            "messages": messages,
                            "response": response,
                            "stacktrace": traceback.format_exc(),
                        }
                    )
                    + "\n"
                )


class GenericLLMProvider:
    """Generic LLM provider."""

    MODEL_BLACKLIST: ClassVar[list[str]] = [
        # Non-chat models are already filtered by mode="chat" in config.py
        # These patterns catch models that might slip through that filter
        # Embedding models (in case they're misclassified)
        r"text-embedding.*",
        r"embedding.*",
        r".*-embed$",
        # Image/audio generation/processing (should have different modes but just in case)
        r"dall-e.*",
        r"stable-diffusion.*",
        r"whisper.*",
        r"tts-.*",
    ]
    SUMMARIZATION_PROMPT_TEMPLATE: ClassVar[str] = (
        "You are an expert summarizer. Please summarize the following text to be approximately {target_tokens} tokens long. "
        "Focus on preserving all key information, entities, facts, and the overall meaning. "
        "Avoid conversational fluff or introductory/concluding remarks not present in the original. "
        "Original text:\\n\\n{text_to_summarize}"
    )

    def __init__(
        self,
        llm: Any,
        chat_log: str | None = None,
        verbose: bool = True,
    ):
        self.llm: BaseChatModel = llm
        self.chat_logger: ChatLogger | None = ChatLogger(chat_log) if chat_log else None
        self.verbose: bool = verbose

        # Initialize LLM debug logger for detailed debugging
        self.debug_logger: Any | None = None
        if get_llm_debug_logger and initialize_llm_debug_logger:
            try:
                # Try to get existing debug logger or create a new one
                self.debug_logger = get_llm_debug_logger()
                if self.debug_logger is None:
                    self.debug_logger = initialize_llm_debug_logger()
            except Exception as e:
                if self.verbose:
                    print(f"{Fore.YELLOW}⚠️ Could not initialize LLM debug logger: {e.__class__.__name__}: {e}{Style.RESET_ALL}")
                self.debug_logger = None

        try:
            self.tokenizer: tiktoken.Encoding | None = tiktoken.get_encoding("cl100k_base")
        except Exception:
            self.tokenizer = None

    @classmethod
    def from_provider(
        cls,
        provider: str,
        chat_log: str | None = None,
        verbose: bool = True,
        **kwargs: Any,
    ) -> Self:
        if provider == "openai":
            _check_pkg("langchain_openai")
            from langchain_openai import ChatOpenAI

            llm = ChatOpenAI(**kwargs)
        elif provider == "anthropic":
            _check_pkg("langchain_anthropic")
            from langchain_anthropic import ChatAnthropic  # pyright: ignore[reportMissingImports]

            llm = ChatAnthropic(**kwargs)
        elif provider == "azure_openai":
            _check_pkg("langchain_openai")
            from langchain_openai import AzureChatOpenAI

            if "model" in kwargs:
                model_name: str | None = kwargs.get("model", None)
                kwargs = {"azure_deployment": model_name, **kwargs}

            llm = AzureChatOpenAI(**kwargs)
        elif provider == "cohere":
            _check_pkg("langchain_cohere")
            from langchain_cohere import ChatCohere  # pyright: ignore[reportMissingImports]

            llm = ChatCohere(**kwargs)
        elif provider == "google_vertexai":
            _check_pkg("langchain_google_vertexai")
            from langchain_google_vertexai import ChatVertexAI  # pyright: ignore[reportMissingImports]

            llm = ChatVertexAI(**kwargs)
        elif provider == "google_genai":
            _check_pkg("langchain_google_genai")
            from langchain_google_genai import ChatGoogleGenerativeAI  # pyright: ignore[reportMissingImports]

            llm = ChatGoogleGenerativeAI(**kwargs)
        elif provider == "fireworks":
            _check_pkg("langchain_fireworks")
            from langchain_fireworks import ChatFireworks  # pyright: ignore[reportMissingImports]

            llm = ChatFireworks(**kwargs)
        elif provider == "ollama":
            _check_pkg("langchain_community")
            _check_pkg("langchain_ollama")
            from langchain_ollama import ChatOllama

            llm = ChatOllama(base_url=os.environ["OLLAMA_BASE_URL"], **kwargs)
        elif provider == "together":
            _check_pkg("langchain_together")
            from langchain_together import ChatTogether  # pyright: ignore[reportMissingImports]

            llm = ChatTogether(**kwargs)
        elif provider == "mistralai":
            _check_pkg("langchain_mistralai")
            from langchain_mistralai import ChatMistralAI  # pyright: ignore[reportMissingImports]

            llm = ChatMistralAI(**kwargs)
        elif provider == "huggingface":
            _check_pkg("langchain_huggingface")
            from langchain_huggingface import ChatHuggingFace  # pyright: ignore[reportMissingImports]

            if "model" in kwargs or "model_name" in kwargs:
                model_name = kwargs.pop("model", None) or kwargs.pop("model_name", None)
                kwargs = {"model_id": model_name, **kwargs}
            llm = ChatHuggingFace(**kwargs)
        elif provider == "groq":
            _check_pkg("langchain_groq")
            from langchain_groq import ChatGroq  # pyright: ignore[reportMissingImports]

            llm = ChatGroq(**kwargs)
        elif provider == "bedrock":
            _check_pkg("langchain_aws")
            from langchain_aws import ChatBedrock  # pyright: ignore[reportMissingImports]

            if "model" in kwargs or "model_name" in kwargs:
                model_name = kwargs.pop("model", None) or kwargs.pop("model_name", None)
                kwargs = {"model_id": model_name, "model_kwargs": kwargs}
            llm = ChatBedrock(**kwargs)
        elif provider == "dashscope":
            _check_pkg("langchain_dashscope")
            from langchain_dashscope import ChatDashScope  # pyright: ignore[reportMissingImports]
            llm = ChatOpenAI(openai_api_base='https://dashscope.aliyuncs.com/compatible-mode/v1',
                     openai_api_key=os.environ["DASHSCOPE_API_KEY"],
                     **kwargs
                )
        elif provider == "xai":
            _check_pkg("langchain_xai")
            from langchain_xai import ChatXAI  # pyright: ignore[reportMissingImports]

            llm = ChatXAI(**kwargs)
        elif provider == "deepseek":
            _check_pkg("langchain_openai")
            from langchain_openai import ChatOpenAI

            llm = ChatOpenAI(
                openai_api_base="https://api.deepseek.com",  # pyright: ignore[reportCallIssue]
                openai_api_key=os.environ["DEEPSEEK_API_KEY"],  # pyright: ignore[reportCallIssue]
                **kwargs,
            )
        elif provider == "litellm":
            try:
                _check_pkg("langchain_litellm")
                from langchain_litellm import ChatLiteLLM  # pyright: ignore[reportMissingImports]
            except ModuleNotFoundError:
                _check_pkg("langchain_community")
                from langchain_community.chat_models.litellm import ChatLiteLLM

            llm = ChatLiteLLM(**kwargs)
        elif provider == "gigachat":
            _check_pkg("langchain_gigachat")
            from langchain_gigachat.chat_models import GigaChat  # pyright: ignore[reportMissingImports]

            kwargs.pop("model", None)  # Use env GIGACHAT_MODEL=GigaChat-Max
            llm = GigaChat(**kwargs)
        elif provider == "openrouter":
            _check_pkg("langchain_openai")
            from langchain_core.rate_limiters import InMemoryRateLimiter
            from langchain_openai import ChatOpenAI

            rps: float = float(os.environ["OPENROUTER_LIMIT_RPS"]) if "OPENROUTER_LIMIT_RPS" in os.environ else 1.0

            rate_limiter = InMemoryRateLimiter(
                requests_per_second=rps,
                check_every_n_seconds=0.1,
                max_bucket_size=10,
            )
            # Set up extra_body with middle-out transform for OpenRouter
            extra_body: dict[str, Any] = kwargs.pop("extra_body", {})

            # Add middle-out transform for OpenRouter to handle context length issues
            if "transforms" not in extra_body:
                extra_body["transforms"] = ["middle-out"]
            elif "middle-out" not in extra_body["transforms"]:
                extra_body["transforms"].append("middle-out")

            llm = ChatOpenAI(
                base_url="https://openrouter.ai/api/v1",  # pyright: ignore[reportCallIssue]
                api_key=os.environ["OPENROUTER_API_KEY"],  # pyright: ignore[reportCallIssue]
                rate_limiter=rate_limiter,
                extra_body=extra_body,  # pyright: ignore[reportCallIssue]
                **kwargs,
            )
        elif provider == "vllm_openai":
            _check_pkg("langchain_openai")
            from langchain_openai import ChatOpenAI
            llm = ChatOpenAI(
                openai_api_key=os.environ["VLLM_OPENAI_API_KEY"],
                openai_api_base=os.environ["VLLM_OPENAI_API_BASE"],
                **kwargs
            )
        elif provider == "aimlapi":
            _check_pkg("langchain_openai")
            from langchain_openai import ChatOpenAI

            llm = ChatOpenAI(openai_api_base='https://api.aimlapi.com/v1',
                             openai_api_key=os.environ["AIMLAPI_API_KEY"],
                             **kwargs
                             )
        else:
            supported: str = ", ".join(_SUPPORTED_PROVIDERS)
            raise ValueError(f"Unsupported provider: '{provider}'.\\n\\nSupported model providers are: '{supported}'")
        return cls(llm, chat_log, verbose=verbose)


    async def get_chat_response(
        self,
        messages: list[dict[str, str] | BaseMessage],
        stream: bool = False,
        websocket: WebSocket | None = None,
    ) -> str:
        """Get chat response and stream output if websocket is provided.

        Args:
            messages (list[dict[str, str] | BaseMessage]): The messages to send to the LLM.
            stream (bool, optional): Whether to stream the response. Defaults to False.
            websocket (WebSocket | None, optional): The websocket to send the response to. Defaults to None.

        Returns:
            str: The response from the LLM.
        """
        processed_messages: list[dict[str, str] | BaseMessage] = messages

        # Start debug logging if available and no current interaction exists
        interaction_id: str | None = None
        start_time: float = time.time()
        should_finish_interaction: bool = False

        if self.debug_logger is not None:
            try:
                # Check if there's already an active interaction (fallback scenario)
                if self.debug_logger.current_interaction is None:
                    # Extract model and provider info
                    model_name: str = getattr(self.llm, "model_name", str(self.llm.__class__.__name__))
                    provider_name: str = (getattr(self.llm.__class__, "__module__") or "unknown").split(".")[-1]

                    # Start logging interaction
                    interaction_id = self.debug_logger.start_interaction(
                        step_name="chat_response",
                        model=model_name,
                        provider=provider_name,
                        context_info={
                            "stream": stream,
                            "has_websocket": websocket is not None,
                            "message_count": len(messages),
                        },
                    )
                    should_finish_interaction = True

                    # Log request details
                    system_msg: str = ""
                    user_msg: str = ""
                    if messages:
                        for msg in messages:
                            if isinstance(msg, dict):
                                if msg.get("role") == "system":
                                    system_msg += msg.get("content", "") + "\n"
                                elif msg.get("role") == "user":
                                    user_msg += msg.get("content", "") + "\n"
                            elif hasattr(msg, "content"):
                                if hasattr(msg, "type") and msg.type == "system":
                                    system_msg += str(msg.content) + "\n"
                                else:
                                    user_msg += str(msg.content) + "\n"

                    # Get model parameters
                    temperature: float | None = getattr(self.llm, "temperature", None)
                    max_tokens: int | None = getattr(self.llm, "max_tokens", None)
                    model_kwargs: dict[str, Any] = getattr(self.llm, "model_kwargs", {})

                    self.debug_logger.log_request(
                        system_message=system_msg.strip(),
                        user_message=user_msg.strip(),
                        full_messages=[
                            msg
                            if isinstance(msg, dict)
                            else {"role": "user", "content": str(msg.content)}
                            for msg in messages
                        ],
                        temperature=temperature,
                        max_tokens=max_tokens,
                        **model_kwargs,
                    )
                else:
                    # Reuse existing interaction for fallback scenarios
                    interaction_id = self.debug_logger.current_interaction.interaction_id
                    should_finish_interaction = False

                    # Update the current interaction with fallback provider info if needed
                    if self.debug_logger.current_interaction.is_fallback:
                        model_name: str = getattr(self.llm, "model_name", str(self.llm.__class__.__name__))
                        provider_name: str = (getattr(self.llm.__class__, "__module__") or "unknown").split(".")[-1]
                        self.debug_logger.current_interaction.model = model_name
                        self.debug_logger.current_interaction.provider = provider_name

            except Exception as e:
                if self.verbose:
                    print(f"{Fore.YELLOW}⚠️ Debug logging start failed: {e.__class__.__name__}: {e}{Style.RESET_ALL}")

        try:
            if not stream:
                output: BaseMessage = await self.llm.ainvoke(processed_messages)
                res: str = str(output.content)
            else:
                res: str = await self.stream_response(processed_messages, websocket)

            if (
                self.debug_logger is not None
                and interaction_id
                and interaction_id.strip()
                and should_finish_interaction
            ):
                try:
                    duration: float = time.time() - start_time
                    self.debug_logger.log_response(
                        response=res, success=True, duration_seconds=duration
                    )
                    self.debug_logger.finish_interaction()
                except Exception as e:
                    if self.verbose:
                        print(f"{Fore.YELLOW}⚠️ Debug logging response failed: {e.__class__.__name__}: {e}{Style.RESET_ALL}")

            if self.chat_logger is not None:
                loggable_msgs: list[dict[str, str]] = [
                    msg.model_dump() if isinstance(msg, BaseMessage) else msg
                    for msg in processed_messages
                ]
                await self.chat_logger.log_request(loggable_msgs, res)

            return res

        except Exception as e:
            if (
                self.debug_logger is not None
                and interaction_id
                and interaction_id.strip()
                and should_finish_interaction
            ):
                try:
                    duration = time.time() - start_time
                    self.debug_logger.log_response(
                        response="",
                        success=False,
                        error_message=str(e),
                        error_type=e.__class__.__name__,
                        duration_seconds=duration,
                    )
                    self.debug_logger.finish_interaction()
                except Exception as log_error:
                    if self.verbose:
                        print(f"{Fore.YELLOW}⚠️ Debug logging error failed: {log_error.__class__.__name__}: {log_error}{Style.RESET_ALL}")
            raise

    async def stream_response(
        self,
        messages: list[dict[str, str]],
        websocket: WebSocket | None = None,
    ) -> str:
        paragraph: str = ""
        response: str = ""

        # Streaming the response using the chain astream method from langchain
        async for chunk in self.llm.astream(messages):
            content: str = chunk.content
            response += content
            paragraph += content
            if "\n" in paragraph:
                await self._send_output(paragraph, websocket)
                paragraph = ""

        if paragraph:
            await self._send_output(paragraph, websocket)

        return response

    async def _send_output(
        self,
        content: str,
        websocket: WebSocket | None = None,
    ) -> None:
        if websocket is not None:
            await websocket.send_json({"type": "report", "output": content})
        elif self.verbose:
            print(f"{Fore.GREEN}{content}{Style.RESET_ALL}")


def _check_pkg(pkg: str) -> None:
    if importlib.util.find_spec(pkg) is not None:
        return
    pkg_kebab: str = pkg.replace("_", "-")
    # Import colorama and initialize it
    init(autoreset=True)

    try:
        print(f"{Fore.YELLOW}Installing {pkg_kebab}...{Style.RESET_ALL}")
        subprocess.check_call([sys.executable, "-m", "pip", "install", "-U", pkg_kebab])
        print(f"{Fore.GREEN}Successfully installed {pkg_kebab}{Style.RESET_ALL}")

        # Try importing again after install
        importlib.import_module(pkg)

    except subprocess.CalledProcessError:
        raise ImportError(Fore.RED + f"Failed to install `{pkg_kebab}`. Please install manually with `pip install -U {pkg_kebab}`")
