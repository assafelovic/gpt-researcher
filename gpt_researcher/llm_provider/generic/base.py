from __future__ import annotations

import asyncio
import importlib
import importlib.util
import json
import os
import re
import subprocess
import sys
import traceback

from enum import Enum
from typing import TYPE_CHECKING, Any, ClassVar

import aiofiles
import tiktoken
from colorama import Fore, Style, init
from langchain_core.exceptions import OutputParserException
from langchain_core.language_models.chat_models import BaseChatModel
from langchain_core.messages import BaseMessage, HumanMessage, SystemMessage
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

NO_SUPPORT_TEMPERATURE_MODELS = [
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

SUPPORT_REASONING_EFFORT_MODELS = [
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
        # Old/deprecated/low-quality models (that might still have mode="chat")
        r"davinci(?!.*-003)",  # Exclude davinci models except davinci-003
        r"curie.*",
        r"babbage.*",
        r"ada(?!.*-embedding)",
        r"text-davinci-00[12]",
        r"text-curie-.*",
        r"text-babbage-.*",
        r"text-ada-.*",
        r"code-davinci-.*",
        r"code-cushman-.*",
        r"gpt-3*",
        r".*unstable$",
        # Utility models not meant for general chat
        r"^moderation$",
        r"^content-filter.*",
        r"^toxicity-classifier.*",
    ]
    MAX_RETRIES_TOKEN_LIMIT = 2
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
            from langchain_google_genai import ChatGoogleGenerativeAI

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
                model_id: str | None = kwargs.pop("model", None) or kwargs.pop("model_name", None)
                kwargs = {"model_id": model_id, **kwargs}
            llm = ChatHuggingFace(**kwargs)
        elif provider == "groq":
            _check_pkg("langchain_groq")
            from langchain_groq import ChatGroq  # pyright: ignore[reportMissingImports]

            llm = ChatGroq(**kwargs)
        elif provider == "bedrock":
            _check_pkg("langchain_aws")
            from langchain_aws import ChatBedrock  # pyright: ignore[reportMissingImports]

            if "model" in kwargs or "model_name" in kwargs:
                model_id = kwargs.pop("model", None) or kwargs.pop("model_name", None)
                kwargs = {"model_id": model_id, "model_kwargs": kwargs}
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
            model_kwargs = kwargs.pop("model_kwargs", {})

            llm = ChatOpenAI(
                base_url="https://openrouter.ai/api/v1",  # pyright: ignore[reportCallIssue]
                api_key=os.environ["OPENROUTER_API_KEY"],  # pyright: ignore[reportCallIssue]
                rate_limiter=rate_limiter,
                model_kwargs=model_kwargs,
                **kwargs,
            )

        else:
            supported: str = ", ".join(_SUPPORTED_PROVIDERS)
            raise ValueError(f"Unsupported {provider}.\\n\\nSupported model providers are: {supported}")
        return cls(llm, chat_log, verbose=verbose)

    def _get_token_count(self, text: str, model_for_counting: BaseChatModel | None = None) -> int:
        """Estimates token count. Prefers model-specific tokenizer if available, else uses tiktoken."""
        if model_for_counting and hasattr(model_for_counting, 'get_num_tokens'):
            try:
                return model_for_counting.get_num_tokens(text)
            except Exception:
                # Fallback if model-specific counting fails
                pass

        if self.tokenizer:
            return len(self.tokenizer.encode(text))
        return len(text.split()) # Crude fallback

    def _parse_token_limit_error(self, error: Exception) -> tuple[int | None, int | None, str | None]:
        """Parses error messages for token limit information."""
        error_str = str(error)
        limit_tokens, actual_tokens = None, None

        # OpenAI specific parsing (and some compatible APIs like OpenRouter)
        # Example: "This model's maximum context length is 16385 tokens. However, your messages resulted in 20000 tokens..."
        if (OpenAIBadRequestError and isinstance(error, OpenAIBadRequestError)) or "maximum context length" in error_str.lower():
            match = re.search(r"maximum context length is (\d+) tokens.*resulted in (\d+) tokens", error_str, re.IGNORECASE)
            if match:
                limit_tokens = int(match.group(1))
                actual_tokens = int(match.group(2))
            else: # Simpler pattern if the above fails
                match_limit = re.search(r"maximum context length is (\d+) tokens", error_str, re.IGNORECASE)
                if match_limit:
                    limit_tokens = int(match_limit.group(1))
                # Initialize match_actual here before its potential use for this specific error block
                match_actual_openai: re.Match[str] | None = re.search(r"resulted in (\d+) tokens", error_str, re.IGNORECASE)
                if match_actual_openai:
                    actual_tokens = int(match_actual_openai.group(1))
            return limit_tokens, actual_tokens, error_str

        # Anthropic specific parsing (example, might need adjustment based on actual errors)
        # Example: "Prompt too long: expected prompt to be at most 4096 tokens, but got 5000"
        if (AnthropicAPIError and isinstance(error, AnthropicAPIError)) or "prompt too long" in error_str.lower():
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

    async def _summarize_messages_to_fit(
        self,
        messages: list[dict[str, str] | BaseMessage],
        target_total_tokens: int,
    ) -> list[dict[str, str] | BaseMessage]:
        """Summarizes message content to fit within target_total_tokens."""
        mutable_messages: list[dict[str, Any] | dict[str, str]] = [msg.model_dump() if isinstance(msg, BaseMessage) else msg.copy() for msg in messages]

        # Calculate current total tokens and identify summarizable content
        total_current_tokens = 0
        summarizable_content: list[dict[str, Any]] = [] # List of (index, role, content, tokens)

        system_messages_content: list[str] = []
        system_messages_tokens = 0

        for i, msg in enumerate(mutable_messages):
            role: str = msg.get("role")
            content: str = str(msg.get("content", ""))
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
                msg_type: type[BaseMessage] = type(original_msg)
                try:
                    final_messages.append(msg_type(content=new_msg_dict["content"]))
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
        """
        mutable_messages: list[dict[str, Any] | dict[str, str]] = [
            msg.model_dump()
            if isinstance(msg, BaseMessage)
            else msg.copy()
            for msg in messages
        ]

        # Calculate current total tokens
        current_total_tokens: int = sum(
            self._get_token_count(str(msg.get("content", "")), self.llm)
            + self._get_token_count(str(msg.get("role")), self.llm)
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
        if preserve_system_messages:
            for i, msg in enumerate(mutable_messages):
                if msg.get("role") == "system":
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
                str(mutable_messages[i].get("content", "")), self.llm
            )
            for i in other_msgs_indices
        )

        if trimmable_tokens == 0: # Nothing to trim from content
            return messages # Or raise error, cannot meet target

        for idx in reversed(other_msgs_indices): # Trim from end of content first (or longest)
            if tokens_to_cut <= 0:
                break

            msg_content = str(mutable_messages[idx].get("content", ""))
            msg_tokens = self._get_token_count(msg_content, self.llm)

            if msg_tokens == 0:
                continue

            # Proportion to cut from this message
            proportion_to_cut_from_msg = min(1.0, tokens_to_cut / trimmable_tokens if trimmable_tokens > 0 else 0.5)
            chars_to_cut = int(len(msg_content) * proportion_to_cut_from_msg)

            # Ensure we cut at least some if needed, but not more than the message length
            tokens_to_cut_this_msg = min(msg_tokens, int(msg_tokens * proportion_to_cut_from_msg) +1)

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
                if mutable_messages[idx].get("role") != "system" or not preserve_system_messages:
                    tokens_to_cut -= msg_tokens
                    mutable_messages[idx]["content"] = "" # Effectively remove content
                    if self.verbose:
                        print(f"{Fore.CYAN}Emptied content of message {idx} (role: {mutable_messages[idx].get('role')}). Cut: {msg_tokens}{Style.RESET_ALL}")


        # Reconstruct final messages list
        final_trimmed_messages: list[dict[str, str] | BaseMessage] = []
        current_total_tokens_after_trim: int = 0
        for i, new_msg_dict in enumerate(mutable_messages):
            # Only add if content is not empty or it's a system message we want to keep
            if str(new_msg_dict.get("content","")).strip() or (preserve_system_messages and new_msg_dict.get("role") == "system"):
                original_msg: dict[str, str] | BaseMessage = messages[i] # Get corresponding original message for type
                if isinstance(original_msg, BaseMessage):
                    msg_type: type[BaseMessage] = type(original_msg)
                    try:
                        final_trimmed_messages.append(msg_type(content=new_msg_dict["content"]))
                    except TypeError:
                        final_trimmed_messages.append(HumanMessage(content=new_msg_dict["content"]))
                else:
                    final_trimmed_messages.append(new_msg_dict)
                current_total_tokens_after_trim += self._get_token_count(
                    str(new_msg_dict.get("content", "")), self.llm
                ) + self._get_token_count(
                    str(new_msg_dict.get("role")), self.llm
                )


        if self.verbose:
            print(f"{Fore.GREEN}Trimming complete. Final tokens: {current_total_tokens_after_trim} (Target was {target_total_tokens}){Style.RESET_ALL}")

        if current_total_tokens_after_trim > target_total_tokens and self.verbose:
            print(f"{Fore.RED}Warning: Trimming did not fully meet target. This may cause issues.{Style.RESET_ALL}")

        return final_trimmed_messages

    async def get_chat_response(
        self,
        messages: list[dict[str, str] | BaseMessage],
        stream: bool = False,
        websocket: WebSocket | None = None,
    ) -> str:
        processed_messages: list[dict[str, str] | BaseMessage] = messages # Start with original messages

        for attempt in range(self.MAX_RETRIES_TOKEN_LIMIT + 1):
            try:
                if not stream:
                    output: BaseMessage = await self.llm.ainvoke(processed_messages)
                    res: str = str(output.content)
                else:
                    res: str = await self.stream_response(processed_messages, websocket)

                if self.chat_logger is not None:
                    # Log with the messages that were actually sent (processed_messages)
                    loggable_msgs: list[dict[str, str]] = [msg.model_dump() if isinstance(msg, BaseMessage) else msg for msg in processed_messages]
                    await self.chat_logger.log_request(loggable_msgs, res)
                return res

            except Exception as e:
                # Check for specific token limit errors first
                is_token_limit_error = False
                if OpenAIBadRequestError and isinstance(e, OpenAIBadRequestError):
                    if "maximum context length" in str(e).lower():
                        is_token_limit_error = True
                elif AnthropicAPIError and isinstance(e, AnthropicAPIError): # Example for Anthropic
                    if "prompt is too long" in str(e).lower() or "too many tokens" in str(e).lower():
                        is_token_limit_error = True
                # Add other provider specific error checks here if needed
                elif "token" in str(e).lower() and ("limit" in str(e).lower() or "maximum" in str(e).lower() or "length" in str(e).lower()): # Generic check
                    is_token_limit_error = True

                if is_token_limit_error and attempt < self.MAX_RETRIES_TOKEN_LIMIT:
                    if self.verbose:
                        print(f"{Fore.YELLOW}Token limit error detected (Attempt {attempt + 1}/{self.MAX_RETRIES_TOKEN_LIMIT}). Error: {str(e)[:500]}{Style.RESET_ALL}")

                    limit_tokens, actual_tokens, _ = self._parse_token_limit_error(e)

                    # Determine target tokens for reduction. If limit_tokens is known, use it, else estimate.
                    # Default target reduction: try to get 10-20% below the perceived limit or current size.
                    if limit_tokens:
                        target_tokens_for_retry = int(limit_tokens * 0.9) # Aim for 90% of limit
                    elif actual_tokens: # If we only know how many tokens we sent
                        target_tokens_for_retry = int(actual_tokens * 0.8) # Reduce by 20%
                    else: # Fallback if no numbers parsed
                        current_total_tokens = sum(self._get_token_count(str(msg.get("content", "") if isinstance(msg, dict) else msg.content), self.llm) for msg in processed_messages)
                        target_tokens_for_retry = int(current_total_tokens * 0.75) # Reduce by 25%

                    if self.verbose:
                        print(f"{Fore.CYAN}Parsed limits: Max={limit_tokens}, Actual={actual_tokens}. Retrying with target tokens: {target_tokens_for_retry}{Style.RESET_ALL}")

                    # Try summarization first if summarizer is available and it's not the first attempt (to give trimming a chance)
                    # Or if overflow is significant
                    should_summarize = False
                    if should_summarize:
                        if self.verbose:
                            print(f"{Fore.MAGENTA}Attempting summarization to reduce context...{Style.RESET_ALL}")
                        processed_messages = (
                            await self._summarize_messages_to_fit(
                                processed_messages,
                                target_tokens_for_retry,
                            )
                        )
                    else:
                        if self.verbose:
                            print(f"{Fore.MAGENTA}Attempting trimming to reduce context...{Style.RESET_ALL}")
                        processed_messages = self._trim_messages_to_fit(
                            processed_messages, target_tokens_for_retry
                        )

                    # After processing, convert dict messages back to Langchain BaseMessage types if needed
                    # This is important as self.llm.ainvoke expects List[BaseMessage] or compatible.
                    final_processed_messages: list[BaseMessage] = []
                    for i, p_msg_data in enumerate(processed_messages):
                        original_msg_type: type[BaseMessage] = type(messages[i]) if i < len(messages) and isinstance(messages[i], BaseMessage) else HumanMessage
                        if isinstance(p_msg_data, dict):
                            # Ensure 'content' key exists, use empty string if not
                            content_val: str = p_msg_data.get('content', '')
                            if original_msg_type == SystemMessage:
                                final_processed_messages.append(SystemMessage(content=str(content_val)))
                            else: # Default to HumanMessage or try to reconstruct original type if simple
                                try:
                                    final_processed_messages.append(original_msg_type(content=str(content_val)))
                                except Exception: # Fallback
                                    final_processed_messages.append(HumanMessage(content=str(content_val)))

                        elif isinstance(p_msg_data, BaseMessage):
                            final_processed_messages.append(p_msg_data)
                        else: # Should not happen if types are managed
                            final_processed_messages.append(HumanMessage(content=str(p_msg_data)))
                    processed_messages = final_processed_messages


                    if self.verbose:
                        new_total_tokens: int = sum(self._get_token_count(str(msg.content if isinstance(msg, BaseMessage) else msg.get("content","")), self.llm) for msg in processed_messages)
                        print(f"{Fore.CYAN}Context processed. New total tokens (estimated): {new_total_tokens}. Retrying call...{Style.RESET_ALL}")
                    continue # Retry the LLM call with modified messages

                elif isinstance(e, OutputParserException) and attempt < self.MAX_RETRIES_TOKEN_LIMIT:
                    # Handle output parsing errors, often due to incomplete generation or unexpected format
                    if self.verbose:
                        print(f"{Fore.YELLOW}Output parsing error detected (Attempt {attempt + 1}/{self.MAX_RETRIES_TOKEN_LIMIT}). Error: {str(e)[:500]}{Style.RESET_ALL}")
                        print(f"{Fore.CYAN}Retrying call, hoping for a more complete/correct generation...{Style.RESET_ALL}")
                    # Optionally, could add a slight modification to the prompt here, e.g., asking for a specific format.
                    # For now, just retry.
                    await asyncio.sleep(1) # Small delay before retry
                    continue

                # If not a token limit error, or retries exhausted, re-raise
                if self.verbose and attempt == self.MAX_RETRIES_TOKEN_LIMIT:
                    print(f"{Fore.RED}Max retries reached for error: {type(e).__name__}. Raising final exception.{Style.RESET_ALL}")
                raise e # Re-raise the original error if not handled or retries exhausted

        # Should not be reached if loop is structured correctly, but as a fallback:
        raise Exception("Failed to get chat response after multiple retries.")


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
            if content is not None:
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
    if not importlib.util.find_spec(pkg):
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
            raise ImportError(Fore.RED + f"Failed to install {pkg_kebab}. Please install manually with `pip install -U {pkg_kebab}`")
