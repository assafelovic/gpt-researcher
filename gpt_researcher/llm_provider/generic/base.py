from __future__ import annotations

import asyncio
import importlib
import importlib.util
import json
import os
import re
import subprocess
import sys
import time
import traceback
from contextlib import suppress
from enum import Enum
from typing import TYPE_CHECKING, Any, ClassVar, cast

import aiofiles
import tiktoken
from colorama import Fore, Style, init
from langchain_core.language_models.chat_models import BaseChatModel
from langchain_core.messages import BaseMessage, HumanMessage, SystemMessage

# Import the LLM debug logger
try:
    from gpt_researcher.utils.llm_debug_logger import get_llm_debug_logger, initialize_llm_debug_logger
except ImportError:
    # Fallback if the debug logger is not available
    get_llm_debug_logger = None
    initialize_llm_debug_logger = None

# Attempt to import specific error types, fallback to general Exception
try:
    from openai import BadRequestError as OpenAIBadRequestError
except ImportError:
    OpenAIBadRequestError = None  # type: ignore

try:
    from anthropic import APIError as AnthropicAPIError
except ImportError:
    AnthropicAPIError = None # type: ignore


if TYPE_CHECKING:
    from fastapi import WebSocket
    from typing_extensions import Self


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
    "openrouter",
    "together",
    "xai",
}

NO_SUPPORT_TEMPERATURE_MODELS: list[str] = [
    "deepseek/deepseek-reasoner",
    "o1-mini",
    "o1-mini-2024-09-12",
    "o1",
    "o1-2024-12-17",
    "o3-mini",
    "o3-mini-2025-01-31",
    "o4-mini",
    "o1-preview"
]

SUPPORT_REASONING_EFFORT_MODELS: list[str] = [
    "o3-mini",
    "o3-mini-2025-01-31",
    "o4-mini"
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
    SUMMARIZATION_PROMPT_TEMPLATE = (
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
                if self.verbose:
                    print(f"{Fore.GREEN}🔍 LLM Debug Logger enabled for detailed interaction logging{Style.RESET_ALL}")
            except Exception as e:
                if self.verbose:
                    print(f"{Fore.YELLOW}⚠️ Could not initialize LLM debug logger: {e}{Style.RESET_ALL}")
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

            llm = ChatDashScope(**kwargs)
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

            # Set up model_kwargs
            model_kwargs: dict[str, Any] = kwargs.pop("model_kwargs", {})

            llm = ChatOpenAI(
                base_url="https://openrouter.ai/api/v1",  # pyright: ignore[reportCallIssue]
                api_key=os.environ["OPENROUTER_API_KEY"],  # pyright: ignore[reportCallIssue]
                rate_limiter=rate_limiter,
                model_kwargs=model_kwargs,  # pyright: ignore[reportCallIssue]
                **kwargs,
            )

        else:
            supported: str = ", ".join(_SUPPORTED_PROVIDERS)
            raise ValueError(f"Unsupported {provider}.\\n\\nSupported model providers are: {supported}")
        return cls(llm, chat_log, verbose=verbose)

    def _get_token_count(
        self,
        text: str,
        model_for_counting: BaseChatModel | None = None,
    ) -> int:
        """Estimates token count. Prefers model-specific tokenizer if available, else uses tiktoken."""
        if model_for_counting is not None and hasattr(model_for_counting, "get_num_tokens"):
            with suppress(Exception):
                return model_for_counting.get_num_tokens(text)

        if self.tokenizer is not None:
            return len(self.tokenizer.encode(text))
        return len(text.split()) # Crude fallback

    def _parse_token_limit_error(
        self,
        error: Exception,
    ) -> tuple[int | None, int | None, str | None]:
        """Parses error messages for token limit information."""
        error_str = str(error)
        limit_tokens: int | None = None
        actual_tokens: int | None = None

        # OpenAI specific parsing (and some compatible APIs like OpenRouter)
        # Example: "This model's maximum context length is 16385 tokens. However, your messages resulted in 20000 tokens..."
        if (
            OpenAIBadRequestError is not None
            and isinstance(error, OpenAIBadRequestError)
        ) or "maximum context length" in error_str.lower():
            match: re.Match[str] | None = re.search(r"maximum context length is (\d+) tokens.*resulted in (\d+) tokens", error_str, re.IGNORECASE)
            if match:
                limit_tokens = int(match.group(1))
                actual_tokens = int(match.group(2))
            else: # Simpler pattern if the above fails
                match_limit: re.Match[str] | None = re.search(r"maximum context length is (\d+) tokens", error_str, re.IGNORECASE)
                if match_limit:
                    limit_tokens = int(match_limit.group(1))
                # Initialize match_actual here before its potential use for this specific error block
                match_actual_openai: re.Match[str] | None = re.search(r"resulted in (\d+) tokens", error_str, re.IGNORECASE)
                if match_actual_openai:
                    actual_tokens = int(match_actual_openai.group(1))
            return limit_tokens, actual_tokens, error_str

        # Anthropic specific parsing (example, might need adjustment based on actual errors)
        # Example: "Prompt too long: expected prompt to be at most 4096 tokens, but got 5000"
        if (
            AnthropicAPIError is not None
            and isinstance(error, AnthropicAPIError)
        ) or "prompt too long" in error_str.lower():
            match_anthropic: re.Match[str] | None = re.search(r"at most (\d+) tokens, but got (\d+)", error_str, re.IGNORECASE)
            if match_anthropic:
                limit_tokens = int(match_anthropic.group(1))
                actual_tokens = int(match_anthropic.group(2))
            return limit_tokens, actual_tokens, error_str

        # Generic catch-all for other potential error messages (less reliable)
        # Initialize actual_tokens to None before generic searches might assign to it if not already set.
        # limit_tokens is also initialized at the top of the function.
        match_limit_generic: re.Match[str] | None = re.search(r"(?:limit|max|maximum).*\b(\d+)\s*tokens", error_str, re.IGNORECASE)
        if match_limit_generic:
            limit_tokens = int(match_limit_generic.group(1))

        match_actual_generic: re.Match[str] | None = re.search(r"(?:actual|got|your|request|prompt).*\b(\d+)\s*tokens", error_str, re.IGNORECASE)
        if match_actual_generic:
            # This might sometimes pick up the limit again, so be careful
            # Prefer specific matches if actual_tokens is still None from earlier specific blocks
            if actual_tokens is None:
                actual_tokens = int(match_actual_generic.group(1))

        return limit_tokens, actual_tokens, error_str

    def estimate_message_tokens(
        self,
        messages: list[dict[str, str] | BaseMessage],
        model: str = "gpt-4",
    ) -> int:
        """Advanced token estimation that handles both dict and BaseMessage formats.

        Args:
            messages: The messages to estimate tokens for
            model: The model to use for estimation

        Returns:
            int: Estimated number of tokens
        """
        try:
            encoding: tiktoken.Encoding = tiktoken.encoding_for_model(model)
        except KeyError:
            # Fall back to cl100k_base encoding for models not in the tiktoken registry
            encoding = tiktoken.get_encoding("cl100k_base")

        total_tokens = 0

        for message in messages:
            # Handle both dict and BaseMessage formats
            if isinstance(message, BaseMessage):
                content = str(message.content)
                role: str = message.__class__.__name__.lower().replace("message", "")
                if role == "human":
                    role = "user"
                elif role == "ai":
                    role = "assistant"
            else:
                content = str(message["content"])
                role = str(message["role"])

            # Add message overhead (4 tokens per message)
            total_tokens += 4

            # Add content token count
            if content:
                total_tokens += len(encoding.encode(content))

            # Add role token count
            if role:
                total_tokens += len(encoding.encode(role))

        # Add final overhead (3 tokens)
        total_tokens += 3

        return total_tokens

    def truncate_messages_to_fit_advanced(
        self,
        messages: list[dict[str, str] | BaseMessage],
        max_context_tokens: int,
        model: str = "gpt-4",
    ) -> list[dict[str, str] | BaseMessage]:
        """Advanced message truncation with intelligent prioritization.

        This function preserves system messages and truncates the user and assistant messages.
        It uses sophisticated strategies including binary search for precise truncation.

        Args:
            messages: List of messages to truncate
            max_context_tokens: Maximum context tokens to preserve
            model: The model for token estimation

        Returns:
            Truncated messages that fit within the token limit
        """
        if not messages:
            return []

        # Calculate minimum viable tokens for a coherent message
        min_message: dict[str, str] = {"role": "user", "content": "..."}
        min_viable_tokens: int = self.estimate_message_tokens([min_message], model)

        # Ensure we have a workable token limit
        if max_context_tokens < min_viable_tokens:
            if self.verbose:
                print(f"max_context_tokens ({max_context_tokens}) less than minimum needed ({min_viable_tokens}), using minimum")
            max_context_tokens = min_viable_tokens

        # Separate system messages from user/assistant messages
        system_messages: list[dict[str, str] | BaseMessage] = [msg for msg in messages if self._get_message_role(msg) == "system"]
        user_assistant_messages: list[dict[str, str] | BaseMessage] = [msg for msg in messages if self._get_message_role(msg) != "system"]

        # Estimate token count for system messages
        system_token_count: int = self.estimate_message_tokens(system_messages, model)

        # Allocate tokens dynamically based on message importance
        system_importance_factor = 0.8  # Higher factor = more importance to system messages

        # Calculate target token allocations
        if system_token_count > 0:
            max_system_tokens: int = min(
                max(int(max_context_tokens * system_importance_factor), min_viable_tokens * len(system_messages)),
                system_token_count
            )
        else:
            max_system_tokens = 0

        # If system needs truncation
        if system_token_count > max_system_tokens:
            if self.verbose:
                print(f"System messages need truncation ({system_token_count} > {max_system_tokens})")
            system_messages = self._truncate_system_messages_advanced(system_messages, max_system_tokens, model)
            system_token_count = self.estimate_message_tokens(system_messages, model)

        # Allocate the remaining tokens to user/assistant messages
        remaining_tokens: int = max_context_tokens - system_token_count

        if remaining_tokens <= 0:
            return system_messages

        # Keep an ordered list of messages for further processing
        result_messages: list[dict[str, str] | BaseMessage] = system_messages.copy()

        # For user/assistant messages, prioritize the most recent ones
        user_assistant_messages.reverse()  # Reverse to prioritize recent messages
        current_tokens: int = system_token_count
        current_messages: list[dict[str, str] | BaseMessage] = []

        # First pass: determine which messages can be included entirely
        for msg in user_assistant_messages:
            msg_tokens: int = self.estimate_message_tokens([msg], model)

            if current_tokens + msg_tokens <= max_context_tokens:
                current_messages.append(msg)
                current_tokens += msg_tokens
            else:
                # This message would exceed the limit
                if not current_messages:
                    # Truncate this message to fit
                    truncated_msg: dict[str, str] | BaseMessage = self._truncate_message_content_advanced(msg, remaining_tokens, model)
                    current_messages.append(truncated_msg)
                break

        # Restore the correct order and combine with system messages
        current_messages.reverse()
        result_messages.extend(current_messages)

        # Make sure we have at least one valid message
        if not result_messages:
            result_messages = [{"role": "user", "content": "..."}]

        # Make sure messages have content
        for msg in result_messages:
            if isinstance(msg, dict) and not msg["content"]:
                msg["content"] = "..."

        return result_messages

    def _truncate_message_content_advanced(
        self,
        message: dict[str, str] | BaseMessage,
        max_tokens: int,
        model: str = "gpt-4",
    ) -> dict[str, str] | BaseMessage:
        """Advanced truncation of a single message using binary search for precision.

        Args:
            message: The message to truncate
            max_tokens: Maximum tokens for the message
            model: The model to use for token estimation

        Returns:
            Truncated message
        """
        import math

        # Convert to dict format for processing
        if isinstance(message, BaseMessage):
            msg_dict: dict[str, str] = {
                "role": message.__class__.__name__.lower().replace("message", ""),
                "content": str(message.content)
            }
            if msg_dict["role"] == "human":
                msg_dict["role"] = "user"
            elif msg_dict["role"] == "ai":
                msg_dict["role"] = "assistant"
            original_type = message.__class__
        else:
            msg_dict = message.copy()
            original_type = None

        content: str = msg_dict["content"]

        # Calculate minimum viable token space needed for basic message structure
        role_tokens: int = len(msg_dict["role"])
        estimated_overhead: int = role_tokens + 5

        if max_tokens <= estimated_overhead + 1:
            msg_dict["content"] = "..."
            return self._convert_message_back(msg_dict, original_type)

        # Reserve tokens for message formatting and role
        truncated_tokens: int = max_tokens - estimated_overhead

        if truncated_tokens <= 0:
            msg_dict["content"] = "..."
            return self._convert_message_back(msg_dict, original_type)

        # Binary search approach for efficient truncation
        content_length: int = len(content)
        start_ratio: float = 0.0
        end_ratio: float = 1.0
        best_content: str = "..."
        best_token_count: int = 0

        max_iterations: int = max(3, min(12, int(math.log(content_length + 1, 2))))

        # Binary search phase
        for iteration in range(max_iterations):
            mid_ratio: float = (start_ratio + end_ratio) / 2
            current_length: int = int(len(content) * mid_ratio)

            if current_length <= 0:
                break

            truncated_content: str = content[:current_length]
            test_msg: dict[str, str] = msg_dict.copy()
            test_msg["content"] = truncated_content
            token_count: int = self.estimate_message_tokens([test_msg], model)

            if token_count <= max_tokens:
                best_content = truncated_content
                best_token_count = token_count
                start_ratio = mid_ratio
            else:
                end_ratio = mid_ratio

            # Early termination for precision
            precision_factor: float = min(0.01, 10.0 / content_length)
            if end_ratio - start_ratio < precision_factor:
                break

        msg_dict["content"] = best_content if best_token_count > 0 else "..."
        return self._convert_message_back(msg_dict, original_type)

    def _truncate_system_messages_advanced(
        self,
        system_messages: list[dict[str, str] | BaseMessage],
        max_tokens: int,
        model: str = "gpt-4",
    ) -> list[dict[str, str] | BaseMessage]:
        """Advanced truncation of system messages to fit within max_tokens.

        Args:
            system_messages: List of system messages
            max_tokens: Maximum tokens to fit within
            model: Model to use for token estimation

        Returns:
            Truncated system messages
        """
        if not system_messages:
            return []

        # Calculate minimum viable token count for a valid system message
        min_system_tokens: int = self.estimate_message_tokens([{"role": "system", "content": "..."}], model)

        if max_tokens <= min_system_tokens:
            if self.verbose:
                print(f"max_tokens ({max_tokens}) less than minimum needed for system message ({min_system_tokens})")
            return [{"role": "system", "content": "..."}]

        if len(system_messages) == 1:
            return [self._truncate_message_content_advanced(system_messages[0], max_tokens, model)]

        # Multiple system messages - keep as many as possible
        result_messages: list[dict[str, str] | BaseMessage] = []
        remaining_tokens: int = max_tokens

        for i, msg in enumerate(system_messages):
            msg_tokens: int = self.estimate_message_tokens([msg], model)
            if msg_tokens <= remaining_tokens:
                result_messages.append(msg)
                remaining_tokens -= msg_tokens
            elif i == 0:
                # First message doesn't fit, truncate it
                truncated: dict[str, str] | BaseMessage = self._truncate_message_content_advanced(msg, remaining_tokens, model)
                result_messages.append(truncated)
                break
            else:
                break

        return result_messages

    def _get_message_role(
        self,
        message: dict[str, str] | BaseMessage,
    ) -> str:
        """Extract role from message regardless of format."""
        if isinstance(message, BaseMessage):
            role: str = message.__class__.__name__.lower().replace("message", "")
            if role == "human":
                return "user"
            elif role == "ai":
                return "assistant"
            return role
        return message["role"]

    def _convert_message_back(
        self,
        msg_dict: dict[str, str],
        original_type: type[BaseMessage] | None,
    ) -> dict[str, str] | BaseMessage:
        """Convert processed message dict back to original type."""
        if original_type is not None:
            try:
                return original_type(content=msg_dict["content"])
            except Exception:
                return HumanMessage(content=msg_dict["content"])
        return msg_dict

    async def _summarize_messages_to_fit(
        self,
        messages: list[dict[str, str] | BaseMessage],
        target_total_tokens: int,
    ) -> list[dict[str, str] | BaseMessage]:
        """Summarizes message content to fit within target_total_tokens."""
        mutable_messages: list[dict[str, Any] | dict[str, str]] = [
            msg.model_dump()
            if isinstance(msg, BaseMessage)
            else msg.copy()
            for msg in messages
        ]

        # Calculate current total tokens and identify summarizable content
        total_current_tokens = 0
        summarizable_content: list[dict[str, Any]] = [] # List of (index, role, content, tokens)

        system_messages_content: list[str] = []
        system_messages_tokens = 0

        for i, msg in enumerate(mutable_messages):
            role: str = msg["role"]
            content: str = str(msg["content"])
            tokens: int = self._get_token_count(content, self.llm)
            total_current_tokens += tokens + self._get_token_count(role, self.llm) # Approx role tokens

            if role == "system":
                system_messages_content.append(content)
                system_messages_tokens += tokens
            elif role in ["user", "assistant", "human"] and tokens > 100: # Only summarize longer messages
                summarizable_content.append({"index": i, "role": role, "content": content, "tokens": tokens})

        if not summarizable_content or total_current_tokens <= target_total_tokens:
            return messages # Nothing to summarize or already fits

        # Sort by length to summarize longest first
        summarizable_content.sort(key=lambda x: x["tokens"], reverse=True)

        tokens_to_reduce: int = total_current_tokens - target_total_tokens
        if self.verbose:
            print(f"{Fore.CYAN}Attempting summarization. Current tokens: {total_current_tokens}, Target: {target_total_tokens}, Reduce by: {tokens_to_reduce}{Style.RESET_ALL}")

        for item in summarizable_content:
            if tokens_to_reduce <= 0:
                break

            original_tokens: int = item["tokens"]
            # Aim to reduce this message's token count significantly, but not to zero
            # Target for this specific summary should leave room for other messages.
            # This is a heuristic.
            reduction_share: int = min(original_tokens - 50, tokens_to_reduce + 50) # Reduce by at least 50 tokens, or up to the needed reduction + buffer
            summarized_target_tokens: int = max(50, original_tokens - reduction_share)


            if self.verbose:
                print(f"{Fore.CYAN}Summarizing message {item['index']} (role: {item['role']}): {original_tokens} tokens to ~{summarized_target_tokens} tokens.{Style.RESET_ALL}")

            try:
                summarization_prompt: str = self.SUMMARIZATION_PROMPT_TEMPLATE.format(
                    target_tokens=summarized_target_tokens,
                    text_to_summarize=item["content"]
                )
                summary_messages: list[BaseMessage] = [SystemMessage(content="You are an expert summarizer."), HumanMessage(content=summarization_prompt)]

                # The summarizer should not stream.
                summarized_text: str = await self.get_chat_response(summary_messages, stream=False)

                summarized_tokens: int = self._get_token_count(summarized_text, self.llm)

                mutable_messages[item["index"]]["content"] = summarized_text

                reduction_achieved: int = original_tokens - summarized_tokens
                tokens_to_reduce -= reduction_achieved
                total_current_tokens -= reduction_achieved

                if self.verbose:
                    print(f"{Fore.GREEN}Summarized message {item['index']}. Original tokens: {original_tokens}, New: {summarized_tokens}, Reduced by: {reduction_achieved}{Style.RESET_ALL}")

            except Exception as e:
                if self.verbose:
                    print(f"{Fore.RED}Error during summarization for message {item['index']}: {e}{Style.RESET_ALL}")
                # If summarization fails, we might try trimming this message later or just skip it for summarization.

        if total_current_tokens > target_total_tokens:
            if self.verbose:
                print(f"{Fore.YELLOW}Summarization did not meet target. Current tokens: {total_current_tokens}, Target: {target_total_tokens}. Further trimming might be needed.{Style.RESET_ALL}")

        # Convert back to BaseMessage if original was
        final_messages: list[dict[str, str] | BaseMessage] = []
        for i, new_msg_dict in enumerate(mutable_messages):
            original_msg: dict[str, Any] | dict[str, str] | BaseMessage = messages[i]
            if isinstance(original_msg, BaseMessage):
                # Reconstruct BaseMessage of the same type
                try:
                    final_messages.append(original_msg.__class__(content=new_msg_dict["content"]))
                except TypeError: # Some BaseMessage types might not just take 'content'
                    final_messages.append(HumanMessage(content=new_msg_dict["content"])) # Fallback
            else:
                final_messages.append(new_msg_dict)
        return final_messages


    def _trim_messages_to_fit(
        self,
        messages: list[dict[str, str] | BaseMessage],
        target_total_tokens: int,
        preserve_system_messages: bool = True
    ) -> list[dict[str, str] | BaseMessage]:
        """Trims message content to fit within target_total_tokens.

        Prioritizes removing/trimming from the middle or oldest user/assistant messages.

        Args:
            messages: List of messages to trim
            target_total_tokens: Target total tokens
            preserve_system_messages: Whether to preserve system messages

        Returns:
            Trimmed messages that fit within the target_total_tokens
        """
        mutable_messages: list[dict[str, Any] | dict[str, str]] = [
            msg.model_dump()
            if isinstance(msg, BaseMessage)
            else msg.copy()
            for msg in messages
        ]

        # Calculate current total tokens
        current_total_tokens: int = sum(
            self._get_token_count(str(msg["content"]), self.llm)
            + self._get_token_count(str(msg["role"]), self.llm)
            for msg in mutable_messages
        )

        if current_total_tokens <= target_total_tokens:
            return messages

        if self.verbose:
            print(f"{Fore.CYAN}Trimming messages. Current: {current_total_tokens}, Target: {target_total_tokens}{Style.RESET_ALL}")

        tokens_to_cut: int = current_total_tokens - target_total_tokens

        # Separate system messages if they should be preserved
        system_msgs: list[dict[str, Any] | dict[str, str]] = []
        other_msgs_indices: list[int] = []
        if preserve_system_messages is not None:
            for i, msg in enumerate(mutable_messages):
                if msg["role"] == "system":
                    system_msgs.append(msg)
                else:
                    other_msgs_indices.append(i)
        else:
            other_msgs_indices = list(range(len(mutable_messages)))

        # Trim from non-system messages. Start with the longest ones or oldest.
        # For simplicity here, we'll trim proportionally from the content of user/assistant messages.
        # A more sophisticated strategy could remove entire messages from the middle/start.

        # Calculate total tokens in trimmable messages
        trimmable_tokens: int = sum(
            self._get_token_count(
                str(mutable_messages[i]["content"]),
                self.llm,
            )
            for i in other_msgs_indices
        )

        if trimmable_tokens == 0: # Nothing to trim from content
            return messages # Or raise error, cannot meet target

        for idx in reversed(other_msgs_indices): # Trim from end of content first (or longest)
            if tokens_to_cut <= 0:
                break

            msg_content: str = str(mutable_messages[idx]["content"])
            msg_tokens: int = self._get_token_count(msg_content, self.llm)

            if msg_tokens == 0:
                continue

            # Proportion to cut from this message
            proportion_to_cut_from_msg: float = min(1.0, tokens_to_cut / trimmable_tokens if trimmable_tokens > 0 else 0.5)
            chars_to_cut: int = int(len(msg_content) * proportion_to_cut_from_msg)

            # Ensure we cut at least some if needed, but not more than the message length
            tokens_to_cut_this_msg: int = min(msg_tokens, int(msg_tokens * proportion_to_cut_from_msg) + 1)

            if chars_to_cut > 0 and len(msg_content) > chars_to_cut :

                # Estimate characters per token to find how many chars to cut
                # This is a rough heuristic. For tiktoken, it's often around 3-4 chars/token.
                # For simplicity, let's try to cut a fraction of characters based on token proportion.

                # A simple way: trim from the end of the content string.
                # For more robust trimming, especially with tiktoken, one would encode, trim token IDs, then decode.

                original_char_len: int = len(msg_content)

                # Try to trim characters based on tokens_to_cut_this_msg
                # Assume avg 3 chars per token as a very rough guide for tiktoken based models
                chars_to_remove_estimated: int = tokens_to_cut_this_msg * 3

                if chars_to_remove_estimated < original_char_len:
                    mutable_messages[idx]["content"] = msg_content[:-chars_to_remove_estimated]
                else: # If estimate is too high, cut a fixed smaller portion or half
                    mutable_messages[idx]["content"] = msg_content[:original_char_len // 2]

                new_msg_tokens: int = self._get_token_count(str(mutable_messages[idx]["content"]), self.llm)
                cut_for_this_message: int = msg_tokens - new_msg_tokens
                tokens_to_cut -= cut_for_this_message

                if self.verbose:
                    print(f"{Fore.CYAN}Trimmed message {idx}. Original tokens: {msg_tokens}, New: {new_msg_tokens}, Cut: {cut_for_this_message}{Style.RESET_ALL}")
            elif tokens_to_cut > 0 and msg_tokens > 0 : # If very small message or proportion is tiny, just remove it if not system
                if mutable_messages[idx]["role"] != "system" or not preserve_system_messages:
                    tokens_to_cut -= msg_tokens
                    mutable_messages[idx]["content"] = "" # Effectively remove content
                    if self.verbose:
                        print(f"{Fore.CYAN}Emptied content of message {idx} (role: {mutable_messages[idx]['role']}). Cut: {msg_tokens}{Style.RESET_ALL}")


        # Reconstruct final messages list
        final_trimmed_messages: list[dict[str, str] | BaseMessage] = []
        current_total_tokens_after_trim: int = 0
        for i, new_msg_dict in enumerate(mutable_messages):
            # Only add if content is not empty or it's a system message we want to keep
            if str(new_msg_dict["content"]).strip() or (preserve_system_messages and new_msg_dict["role"] == "system"):
                original_msg: dict[str, str] | BaseMessage = messages[i] # Get corresponding original message for type
                if isinstance(original_msg, BaseMessage):
                    try:
                        final_trimmed_messages.append(original_msg.__class__(content=new_msg_dict["content"]))
                    except TypeError:
                        final_trimmed_messages.append(HumanMessage(content=new_msg_dict["content"]))
                else:
                    final_trimmed_messages.append(new_msg_dict)
                current_total_tokens_after_trim += (
                    self._get_token_count(str(new_msg_dict["content"]), self.llm)
                    + self._get_token_count(str(new_msg_dict["role"]), self.llm)
                )


        if self.verbose:
            print(f"{Fore.GREEN}Trimming complete. Final tokens: {current_total_tokens_after_trim} (Target was {target_total_tokens}){Style.RESET_ALL}")

        if (
            current_total_tokens_after_trim > target_total_tokens
            and self.verbose
        ):
            print(f"{Fore.RED}Warning: Trimming did not fully meet target. This may cause issues.{Style.RESET_ALL}")

        return final_trimmed_messages

    async def get_chat_response(
        self,
        messages: list[dict[str, str] | BaseMessage],
        stream: bool = False,
        websocket: WebSocket | None = None,
    ) -> str:
        """Get chat response with intelligent token handling and fallback support.

        This method implements smart token limit handling with multiple strategies:
        1. Minimal trimming for small overflows (<10%)
        2. Smart summarization for medium overflows (10-50%)
        3. Aggressive summarization for large overflows (>50%)
        4. Progressive reduction with fine-tuning
        5. Automatic fallback to larger models when needed
        """
        processed_messages: list[dict[str, str] | BaseMessage] = messages
        original_messages: list[dict[str, str] | BaseMessage] = messages  # Keep original for reference

        # Start debug logging if available
        interaction_id: str | None = None
        start_time: float = time.time()

        if self.debug_logger is not None:
            try:
                # Extract model and provider info
                model_name: str = getattr(self.llm, "model_name", str(self.llm.__class__.__name__))
                provider_name: str = self.llm.__class__.__module__.split(".")[-1] if hasattr(self.llm, "__module__") else "unknown"

                # Start logging interaction
                interaction_id = self.debug_logger.start_interaction(
                    step_name="chat_response",
                    model=model_name,
                    provider=provider_name,
                    context_info={
                        "stream": stream,
                        "has_websocket": websocket is not None,
                        "message_count": len(messages),
                        "original_message_count": len(original_messages)
                    }
                )

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
                        msg if isinstance(msg, dict) else {"role": "user", "content": str(msg.content)}
                        for msg in messages
                    ],
                    temperature=temperature,
                    max_tokens=max_tokens,
                    **model_kwargs
                )
            except Exception as e:
                if self.verbose:
                    print(f"{Fore.YELLOW}⚠️ Debug logging start failed: {e}{Style.RESET_ALL}")

        # Track our attempts
        token_reduction_attempts: int = 0
        max_token_reduction_attempts = 10  # More attempts for fine-tuning
        strategies_tried: list[str] = []

        while True:
            try:
                if not stream:
                    output: BaseMessage = await self.llm.ainvoke(processed_messages)
                    res: str = str(output.content)
                else:
                    res: str = await self.stream_response(processed_messages, websocket)

                # Log successful response
                if (
                    self.debug_logger is not None
                    and interaction_id
                    and interaction_id.strip()
                ):
                    try:
                        duration: float = time.time() - start_time
                        self.debug_logger.log_response(
                            response=res,
                            success=True,
                            duration_seconds=duration
                        )
                        self.debug_logger.finish_interaction()
                    except Exception as e:
                        if self.verbose:
                            print(f"{Fore.YELLOW}⚠️ Debug logging response failed: {e.__class__.__name__}: {e}{Style.RESET_ALL}")

                if self.chat_logger is not None:
                    loggable_msgs: list[dict[str, str]] = [
                        msg.model_dump()
                        if isinstance(msg, BaseMessage)
                        else msg
                        for msg in processed_messages
                    ]
                    await self.chat_logger.log_request(loggable_msgs, res)

                # Validate response quality
                if len(res.strip()) < 50 or res.lower().strip().startswith(("ate ", "ing ", "ed ", "the ")):
                    if self.verbose:
                        print(f"{Fore.YELLOW}[TOKEN-STRATEGY] Response appears truncated or incomplete. Length: {len(res)}{Style.RESET_ALL}")
                    # If we have more attempts, try a different strategy
                    if token_reduction_attempts < max_token_reduction_attempts - 2:
                        token_reduction_attempts += 1
                        # Force more aggressive reduction
                        processed_messages = await self._apply_token_reduction_strategy(
                            original_messages,
                            strategy="aggressive_summarization",
                            target_reduction=0.5,
                            attempt=token_reduction_attempts
                        )
                        continue

                return res

            except Exception as e:
                # Log error if debug logger is available
                if (
                    self.debug_logger is not None
                    and interaction_id
                    and interaction_id.strip()
                ):
                    try:
                        duration = time.time() - start_time
                        self.debug_logger.log_response(
                            response="",
                            success=False,
                            error_message=str(e),
                            error_type=e.__class__.__name__,
                            duration_seconds=duration
                        )
                    except Exception as log_error:
                        if self.verbose:
                            print(f"{Fore.YELLOW}⚠️ Debug logging error failed: {log_error.__class__.__name__}: {log_error}{Style.RESET_ALL}")

                error_str: str = str(e).lower()

                # Check if this is a token limit error
                is_token_limit_error: bool = any(
                    phrase in error_str
                    for phrase in (
                        "maximum context length",
                        "token",
                        "limit",
                        "too long",
                        "too many tokens",
                        "context length",
                        "length is",
                    )
                )

                if is_token_limit_error:
                    if self.verbose:
                        print(f"{Fore.YELLOW}[TOKEN-STRATEGY] Token limit error detected. Attempt {token_reduction_attempts + 1}/{max_token_reduction_attempts}{Style.RESET_ALL}")

                    # Log token reduction attempt
                    if self.debug_logger:
                        try:
                            self.debug_logger.log_retry_attempt(
                                attempt_number=token_reduction_attempts + 1,
                                reason="token_limit_exceeded",
                                details={"error": str(e), "error_type": e.__class__.__name__}
                            )
                        except Exception:
                            pass

                    # Parse token limits from error
                    limit_tokens, _actual_tokens, _ = self._parse_token_limit_error(e)

                    # Calculate current token usage
                    current_input_tokens: int = sum(
                        self._get_token_count(str(msg["content"] if isinstance(msg, dict) else msg.content), self.llm)
                        for msg in processed_messages
                    )

                    # Extract max_tokens if configured
                    max_tokens_requested: int | None = getattr(self.llm, "max_tokens", None)
                    model_kwargs: dict[str, Any] = getattr(self.llm, "model_kwargs", {})
                    if isinstance(model_kwargs, dict):
                        max_tokens_requested: int | None = model_kwargs.get("max_tokens", max_tokens_requested)

                    if self.verbose:
                        print(f"{Fore.CYAN}[TOKEN-STRATEGY] Current input: {current_input_tokens}, Limit: {limit_tokens}, Output requested: {max_tokens_requested}{Style.RESET_ALL}")

                    # Check if we've exhausted our attempts
                    if token_reduction_attempts >= max_token_reduction_attempts:
                        if self.verbose:
                            print(f"{Fore.RED}[TOKEN-STRATEGY] Exhausted all {max_token_reduction_attempts} reduction attempts. Strategies tried: {strategies_tried}{Style.RESET_ALL}")
                            print(f"{Fore.RED}[TOKEN-STRATEGY] This model cannot handle this request. Allowing fallback to a larger model.{Style.RESET_ALL}")

                        # Log final failure
                        if self.debug_logger is not None and interaction_id and interaction_id.strip():
                            try:
                                self.debug_logger.finish_interaction()
                            except Exception:
                                pass

                        raise  # Let fallback providers handle this

                    # Determine the appropriate strategy based on overflow percentage
                    if limit_tokens:
                        total_needed: int = current_input_tokens + (max_tokens_requested or 2000)
                        overflow_ratio: float = total_needed / limit_tokens

                        if self.verbose:
                            print(f"{Fore.CYAN}[TOKEN-STRATEGY] Overflow ratio: {overflow_ratio:.2f} ({total_needed}/{limit_tokens} tokens){Style.RESET_ALL}")

                        # Choose strategy based on overflow
                        if overflow_ratio < 1.1:  # Less than 10% overflow
                            strategy = "minimal_trimming"
                            target_reduction = 0.15  # Trim 15% to leave buffer
                        elif overflow_ratio < 1.5:  # 10-50% overflow
                            strategy = "smart_summarization"
                            target_reduction = 0.4  # Reduce by 40%
                        elif overflow_ratio < 2.0:  # 50-100% overflow
                            strategy = "aggressive_summarization"
                            target_reduction = 0.6  # Reduce by 60%
                        else:  # More than 100% overflow
                            strategy = "extreme_compression"
                            target_reduction = 0.8  # Reduce by 80%

                        # Apply progressive reduction on retries
                        if token_reduction_attempts > 2:
                            # Get more aggressive with each attempt
                            target_reduction: float = min(0.9, target_reduction + (token_reduction_attempts * 0.1))
                            if token_reduction_attempts > 5:
                                strategy = "extreme_compression"

                        if self.verbose:
                            print(f"{Fore.CYAN}[TOKEN-STRATEGY] Selected strategy: {strategy} with {target_reduction*100:.0f}% reduction{Style.RESET_ALL}")

                        # Log token reduction attempt
                        if self.debug_logger is not None:
                            try:
                                original_tokens: int = sum(
                                    self._get_token_count(str(msg["content"] if isinstance(msg, dict) else msg.content), self.llm)
                                    for msg in original_messages
                                )
                                target_tokens = int(original_tokens * (1 - target_reduction))

                                self.debug_logger.log_token_reduction_attempt(
                                    strategy=strategy,
                                    original_tokens=original_tokens,
                                    target_tokens=target_tokens,
                                    final_tokens=0,  # Will be updated after reduction
                                    success=False,  # Will be updated
                                    details={
                                        "overflow_ratio": overflow_ratio,
                                        "limit_tokens": limit_tokens,
                                        "attempt": token_reduction_attempts
                                    }
                                )
                            except Exception:
                                pass

                        # Apply the selected strategy
                        try:
                            processed_messages = await self._apply_token_reduction_strategy(
                                processed_messages if token_reduction_attempts > 0 else original_messages,
                                strategy=strategy,
                                target_reduction=target_reduction,
                                attempt=token_reduction_attempts,
                                limit_tokens=limit_tokens,
                                max_output_tokens=max_tokens_requested
                            )

                            strategies_tried.append(f"{strategy}({target_reduction*100:.0f}%)")
                            token_reduction_attempts += 1

                            # Verify reduction was effective
                            new_tokens: int = sum(
                                self._get_token_count(str(msg["content"] if isinstance(msg, dict) else msg.content), self.llm)
                                for msg in processed_messages
                            )

                            if self.verbose:
                                print(f"{Fore.GREEN}[TOKEN-STRATEGY] Reduction complete. New input tokens: {new_tokens} (was {current_input_tokens}){Style.RESET_ALL}")

                            continue  # Retry with reduced messages

                        except Exception as strategy_error:
                            if self.verbose:
                                print(f"{Fore.RED}[TOKEN-STRATEGY] Strategy '{strategy}' failed: {strategy_error}{Style.RESET_ALL}")
                            token_reduction_attempts += 1
                            # Try next strategy
                            continue

                    else:
                        # No clear limit, use progressive reduction
                        if self.verbose:
                            print(f"{Fore.YELLOW}[TOKEN-STRATEGY] No clear token limit found. Using progressive reduction.{Style.RESET_ALL}")

                        reduction_factor: float = 0.8 - (token_reduction_attempts * 0.1)
                        reduction_factor = max(0.2, reduction_factor)

                        try:
                            processed_messages = await self._apply_token_reduction_strategy(
                                processed_messages,
                                strategy="progressive_reduction",
                                target_reduction=1 - reduction_factor,
                                attempt=token_reduction_attempts
                            )
                            token_reduction_attempts += 1
                            continue
                        except Exception:
                            token_reduction_attempts += 1
                            continue

                else:
                    # Non-token error - let fallback handle it
                    if self.verbose:
                        print(f"{Fore.RED}[TOKEN-STRATEGY] Non-token error: {e.__class__.__name__}. Allowing fallback.{Style.RESET_ALL}")

                    # Log final failure
                    if (
                        self.debug_logger is not None
                        and interaction_id
                        and interaction_id.strip()
                    ):
                        with suppress(Exception):
                            self.debug_logger.finish_interaction()

                    raise

    async def _apply_token_reduction_strategy(
        self,
        messages: list[dict[str, str] | BaseMessage],
        strategy: str,
        target_reduction: float,
        attempt: int,
        limit_tokens: int | None = None,
        max_output_tokens: int | None = None
    ) -> list[dict[str, str] | BaseMessage]:
        """Apply a specific token reduction strategy to messages.

        Strategies:
        - minimal_trimming: Remove redundancy, clean up formatting
        - smart_summarization: Use LLM to intelligently summarize
        - aggressive_summarization: Heavy summarization preserving key points
        - extreme_compression: Extract only essential information
        - progressive_reduction: Gradually reduce content
        """
        if self.verbose:
            print(f"{Fore.CYAN}[TOKEN-STRATEGY] Applying {strategy} (attempt {attempt + 1}){Style.RESET_ALL}")

        # Calculate target tokens
        current_tokens: int = sum(
            self._get_token_count(str(msg["content"] if isinstance(msg, dict) else msg.content), self.llm)
            for msg in messages
        )

        if limit_tokens and max_output_tokens:
            # Reserve space for output
            available_for_input: int = limit_tokens - max_output_tokens - 500  # Buffer
            target_tokens: int = min(available_for_input, int(current_tokens * (1 - target_reduction)))
        else:
            target_tokens = int(current_tokens * (1 - target_reduction))

        if self.verbose:
            print(f"{Fore.CYAN}[TOKEN-STRATEGY] Target: {target_tokens} tokens (from {current_tokens}){Style.RESET_ALL}")

        # Convert messages to mutable format
        mutable_messages: list[dict[str, str] | BaseMessage] = [
            msg.model_dump() if isinstance(msg, BaseMessage) else msg.copy()
            for msg in messages
        ]

        # Apply strategy
        if strategy == "minimal_trimming":
            # Remove whitespace, redundancy, clean formatting
            for msg in mutable_messages:
                if msg["role"] != "system":  # Preserve system messages  # pyright: ignore[reportIndexIssue]
                    content = str(msg["content"] if isinstance(msg, dict) else msg.content)
                    # Remove excessive whitespace
                    content = " ".join(content.split())
                    # Remove markdown formatting if present
                    content = re.sub(r'\*{1,2}([^\*]+)\*{1,2}', r'\1', content)
                    # Remove redundant punctuation
                    content = re.sub(r'\.{2,}', '.', content)
                    content = re.sub(r'\s+([,.!?])', r'\1', content)
                    if isinstance(msg, dict):
                        msg["content"] = content
                    else:
                        msg.content = content

            # If still too long, trim from the middle
            content = msg["content"] if isinstance(msg, dict) else msg.content
            if sum(self._get_token_count(content, self.llm) for msg in mutable_messages) > target_tokens:
                return self._trim_messages_to_fit(messages, target_tokens)

        elif strategy in {"smart_summarization", "aggressive_summarization", "extreme_compression"}:
            # Use different prompts based on aggressiveness
            if strategy == "smart_summarization":
                summary_instruction = "Summarize the following content, preserving all key information, facts, and context:"
                length_instruction: str = f"Target length: approximately {target_tokens} tokens"
            elif strategy == "aggressive_summarization":
                summary_instruction = "Provide a concise summary focusing on the most important points:"
                length_instruction = f"Maximum length: {target_tokens} tokens"
            else:  # extreme_compression
                summary_instruction = "Extract only the essential information in bullet points:"
                length_instruction = f"Strict limit: {target_tokens} tokens"

            # Group and summarize user/assistant messages
            for i, msg in enumerate(mutable_messages):
                content: str = msg["content"] if isinstance(msg, dict) else msg.content
                if msg["role"] not in {"user", "assistant", "human"} or len(content) <= 500:  # pyright: ignore[reportIndexIssue]
                    continue

                try:
                    summary_prompt: str = f"{summary_instruction}\n\n{content}\n\n{length_instruction}"

                    # Use a simple completion without streaming
                    summary_messages: list[BaseMessage] = [
                        SystemMessage(content="You are an expert summarizer. Be concise."),
                        HumanMessage(content=summary_prompt)
                    ]

                    # Temporarily reduce verbosity for summarization calls
                    original_verbose: bool = self.verbose
                    self.verbose = False

                    summary: str = await self.get_chat_response(summary_messages, stream=False)

                    self.verbose = original_verbose

                    if summary and len(summary.strip()) > 20:
                        mut_msg: dict[str, str] | BaseMessage = mutable_messages[i]
                        if isinstance(mut_msg, dict):
                            mut_msg["content"] = summary.strip()
                        if self.verbose:
                            original_len: int = len(content)
                            new_len: int = len(summary)
                            print(f"{Fore.GREEN}[TOKEN-STRATEGY] Summarized message {i}: {original_len} → {new_len} chars{Style.RESET_ALL}")

                except Exception as e:
                    if self.verbose:
                        print(f"{Fore.YELLOW}[TOKEN-STRATEGY] Summarization failed for message {i}: {e}{Style.RESET_ALL}")
                    if strategy == "extreme_compression":
                        # Keep only first and last parts
                        keep_chars: int = len(content) // 4
                        if isinstance(msg, dict):
                            msg["content"] = content[:keep_chars] + "\n...[content compressed]...\n" + content[-keep_chars:]
                        else:
                            msg.content = content[:keep_chars] + "\n...[content compressed]...\n" + content[-keep_chars:]
                    else:
                        # Progressive trimming
                        if isinstance(msg, dict):
                            msg["content"] = content[:int(len(content) * (1 - target_reduction))]
                        else:
                            msg.content = content[:int(len(content) * (1 - target_reduction))]

        elif strategy == "progressive_reduction":
            # Gradually reduce all messages proportionally
            for msg in mutable_messages:
                if msg["role"] == "system":  # pyright: ignore[reportIndexIssue]
                    continue
                content = msg["content"] if isinstance(msg, dict) else msg.content
                if len(content) <= 100:
                    continue
                # Keep more of the beginning and end
                total_len: int = len(content)
                keep_ratio: float = 1 - target_reduction

                if keep_ratio < 0.5:
                    # For aggressive reduction, use beginning/end strategy
                    keep_start = int(total_len * keep_ratio * 0.6)
                    keep_end = int(total_len * keep_ratio * 0.4)
                    if isinstance(msg, dict):
                        msg["content"] = content[:keep_start] + "\n...\n" + content[-keep_end:]
                    else:
                        msg.content = content[:keep_start] + "\n...\n" + content[-keep_end:]
                else:
                    # For mild reduction, trim from middle
                    keep_total = int(total_len * keep_ratio)
                    if isinstance(msg, dict):
                        msg["content"] = content[:keep_total]
                    else:
                        msg.content = content[:keep_total]

        # Convert back to appropriate message types
        final_messages: list[dict[str, str] | BaseMessage] = []
        for i, new_msg in enumerate(mutable_messages):
            msg: dict[str, str] | BaseMessage = messages[i]
            if i >= len(messages) or not isinstance(msg, BaseMessage):
                final_messages.append(new_msg)
                continue
            try:
                final_messages.append(msg.__class__(content=new_msg["content"] if isinstance(new_msg, dict) else new_msg.content))
            except:  # noqa: E722
                final_messages.append(HumanMessage(content=new_msg["content"] if isinstance(new_msg, dict) else new_msg.content))

        # Verify we achieved target
        final_tokens: int = sum(
            self._get_token_count(str(msg["content"] if isinstance(msg, dict) else msg.content), self.llm)
            for msg in final_messages
        )

        if self.verbose:
            reduction_achieved: float = (1 - final_tokens / current_tokens) * 100
            print(f"{Fore.GREEN}[TOKEN-STRATEGY] Achieved {reduction_achieved:.1f}% reduction: {current_tokens} → {final_tokens} tokens{Style.RESET_ALL}")

            if final_tokens > target_tokens * 1.1:  # More than 10% over target
                print(f"{Fore.YELLOW}[TOKEN-STRATEGY] Warning: Still over target ({final_tokens} > {target_tokens}). May need another iteration.{Style.RESET_ALL}")

        return final_messages

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
