# libraries
from __future__ import annotations

import asyncio
import logging
import os
import re
import traceback
import tiktoken
from collections.abc import Callable
from typing import TYPE_CHECKING, Any
import math

from langchain.llms.base import BaseLLM
from langchain.output_parsers import PydanticOutputParser
from langchain.prompts import PromptTemplate

from gpt_researcher.config.config import Config
from gpt_researcher.llm_provider.generic.base import GenericLLMProvider
from gpt_researcher.prompts import PromptFamily
from gpt_researcher.utils.costs import estimate_llm_cost
from gpt_researcher.utils.validators import Subtopics

if TYPE_CHECKING:
    from gpt_researcher.llm_provider.generic.base import (
        GenericLLMProvider,
        ReasoningEfforts,
    )

logger: logging.Logger = logging.getLogger(__name__)


def get_llm(
    llm_provider: str,
    cfg: Config | None = None,
    **kwargs,
) -> GenericLLMProvider:
    """Initialize an LLM provider with fallback support.

    Args:
        llm_provider: Provider name (e.g., 'openai')
        cfg: Configuration object. If None, a new one will be created.
        **kwargs: Additional keyword arguments for the provider

    Returns:
        LLM provider instance with fallback support if fallbacks are configured
    """
    from gpt_researcher.llm_provider.generic.base import GenericLLMProvider
    from gpt_researcher.llm_provider.generic.fallback import FallbackGenericLLMProvider

    # Check if this LLM has fallbacks configured
    config_obj: Config = Config() if cfg is None else cfg
    if "model" in kwargs:
        model_name: str = kwargs.get("model")

        # Get appropriate fallback providers based on model configuration
        fallback_provider_objects: list[GenericLLMProvider] = []
        if config_obj.fast_llm_model == model_name and config_obj.fast_llm_provider == llm_provider:
            fallback_provider_objects = config_obj.fast_llm_fallback_providers
        elif config_obj.smart_llm_model == model_name and config_obj.smart_llm_provider == llm_provider:
            fallback_provider_objects = config_obj.smart_llm_fallback_providers
        elif config_obj.strategic_llm_model == model_name and config_obj.strategic_llm_provider == llm_provider:
            fallback_provider_objects = config_obj.strategic_llm_fallback_providers

        # Extract the parameters needed for FallbackGenericLLMProvider
        chat_log: Any | None = kwargs.get("chat_log")
        verbose: bool = kwargs.get("verbose", True)

        # Create primary provider first
        try:
            primary_provider: GenericLLMProvider = GenericLLMProvider.from_provider(llm_provider, **kwargs)

            # If we have fallback providers, create a fallback wrapper
            if fallback_provider_objects:
                return FallbackGenericLLMProvider(primary_provider.llm, fallback_providers=fallback_provider_objects, chat_log=chat_log, verbose=verbose)
            return primary_provider
        except Exception as e:
            # If primary provider fails and we have fallbacks, use first fallback as primary
            if fallback_provider_objects:
                logger.warning(f"Primary provider {llm_provider} failed: {e}. Using first fallback as primary.")
                primary: GenericLLMProvider = fallback_provider_objects.pop(0)
                return FallbackGenericLLMProvider(primary.llm, fallback_providers=fallback_provider_objects, chat_log=chat_log, verbose=verbose)
            # No fallbacks available, re-raise the exception
            raise

    # Otherwise, use standard provider without fallbacks
    return GenericLLMProvider.from_provider(llm_provider, **kwargs)


def estimate_token_count(
    messages: list[dict[str, str]],
    model: str = "gpt-4.1",
) -> int:
    """Estimate the number of tokens in a list of messages.

    Args:
        messages (list[dict[str, str]]): The messages to estimate tokens for
        model (str, optional): The model to use for estimation. Defaults to "gpt-4.1".

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
        # Add message overhead (4 tokens per message)
        total_tokens += 4

        # Add content token count
        if "content" in message and message["content"]:
            total_tokens += len(encoding.encode(message["content"]))

        # Add role token count
        if "role" in message:
            total_tokens += len(encoding.encode(message["role"]))

    # Add final overhead (3 tokens)
    total_tokens += 3

    return total_tokens


def truncate_messages_to_fit(
    messages: list[dict[str, str]],
    max_context_tokens: int,
    model: str = "gpt-4.1",
) -> list[dict[str, str]]:
    """Truncate messages to fit within the max_context_tokens.

    This function preserves system messages and truncates the user and assistant messages.
    It starts with the oldest messages and gradually moves to the most recent ones.

    Args:
        messages (list[dict[str, str]]): List of messages to truncate
        max_context_tokens (int): Maximum context tokens to preserve
        model (str): The model for token estimation

    Returns:
        list[dict[str, str]]: Truncated messages
    """
    # DEBUG: Log function entry
    logger.info(f"[DEBUG-TRUNCATE] Starting truncation. Target max tokens: {max_context_tokens}")

    if not messages:
        return []

    # Calculate minimum viable tokens for a coherent message
    # Use message structure to determine minimum
    min_message = {"role": "user", "content": "..."}
    min_viable_tokens = estimate_token_count([min_message], model)

    # Ensure we have a workable token limit
    if max_context_tokens < min_viable_tokens:
        logger.warning(f"[DEBUG-TRUNCATE] max_context_tokens ({max_context_tokens}) less than minimum needed ({min_viable_tokens}), using minimum")
        max_context_tokens = min_viable_tokens

    # Separate system messages from user/assistant messages
    system_messages: list[dict[str, str]] = [msg for msg in messages if msg.get("role", "") == "system"]
    user_assistant_messages: list[dict[str, str]] = [msg for msg in messages if msg.get("role", "") != "system"]

    # DEBUG: Log message counts by type
    logger.info(f"[DEBUG-TRUNCATE] System messages: {len(system_messages)}, User/Assistant messages: {len(user_assistant_messages)}")

    # Estimate token count for system messages
    system_token_count: int = estimate_token_count(system_messages, model)

    # DEBUG: Log system message token count
    logger.info(f"[DEBUG-TRUNCATE] System messages token count: {system_token_count}")

    # Allocate tokens dynamically based on message importance
    # System messages are prioritized but can be truncated if needed
    system_importance_factor = 0.8  # Higher factor = more importance to system messages

    # Calculate target token allocations
    if system_token_count > 0:
        # Allow system to use up to 80% of total, but no less than their minimum viable size
        max_system_tokens = min(
            max(int(max_context_tokens * system_importance_factor), min_viable_tokens * len(system_messages)),
            system_token_count
        )
    else:
        max_system_tokens = 0

    # If system needs truncation
    if system_token_count > max_system_tokens:
        logger.warning(f"[DEBUG-TRUNCATE] System messages need truncation ({system_token_count} > {max_system_tokens})")
        system_messages = truncate_system_messages(system_messages, max_system_tokens, model)
        system_token_count = estimate_token_count(system_messages, model)
        logger.info(f"[DEBUG-TRUNCATE] After truncation: System messages token count: {system_token_count}")

    # Allocate the remaining tokens to user/assistant messages
    remaining_tokens: int = max_context_tokens - system_token_count

    # DEBUG: Log remaining tokens
    logger.info(f"[DEBUG-TRUNCATE] Remaining tokens for user/assistant messages: {remaining_tokens}")

    if remaining_tokens <= 0:
        # Not enough tokens for any user/assistant messages
        logger.warning("[DEBUG-TRUNCATE] No tokens left for user/assistant messages after system messages")
        return system_messages

    # We need to keep an ordered list of messages for further processing
    result_messages: list[dict[str, str]] = system_messages.copy()

    # For user/assistant messages, prioritize the most recent ones
    # Start from the end (most recent) and keep adding messages until we reach the limit
    user_assistant_messages.reverse()  # Reverse to prioritize recent messages
    current_tokens: int = system_token_count
    current_messages: list[dict[str, str]] = []

    # DEBUG: Log process start
    logger.info("[DEBUG-TRUNCATE] Starting to add user/assistant messages (newest first)")

    # First pass: determine which messages can be included entirely
    for msg in user_assistant_messages:
        msg_tokens: int = estimate_token_count([msg], model)
        # DEBUG: Log message token estimate
        logger.info(f"[DEBUG-TRUNCATE] Message ({msg.get('role', 'unknown')}) estimated tokens: {msg_tokens}")

        if current_tokens + msg_tokens <= max_context_tokens:
            # We can add this message in full
            current_messages.append(msg)
            current_tokens += msg_tokens
            # DEBUG: Log added message
            logger.info(f"[DEBUG-TRUNCATE] Added full message. New token count: {current_tokens}/{max_context_tokens}")
        else:
            # This message would exceed the limit
            # If it's the first message, we need to truncate it
            if not current_messages:
                # Truncate this message to fit
                truncated_msg: dict[str, str] = truncate_message_content(msg, remaining_tokens, model)
                current_messages.append(truncated_msg)
                msg_after_tokens = estimate_token_count([truncated_msg], model)
                # DEBUG: Log truncated message
                logger.info(f"[DEBUG-TRUNCATE] Truncated message from {msg_tokens} to {msg_after_tokens} tokens")
                logger.info(f"[DEBUG-TRUNCATE] Original content length: {len(msg.get('content', ''))}, Truncated length: {len(truncated_msg.get('content', ''))}")
            break

    # DEBUG: Log final message count
    logger.info(f"[DEBUG-TRUNCATE] Final user/assistant messages kept: {len(current_messages)}")

    # Restore the correct order and combine with system messages
    current_messages.reverse()
    result_messages.extend(current_messages)

    # Final token count check
    final_token_count = estimate_token_count(result_messages, model)
    # DEBUG: Log final token count
    logger.info(f"[DEBUG-TRUNCATE] Final token count: {final_token_count}/{max_context_tokens}")

    # Make sure we have at least one valid message
    if not result_messages:
        # Create a minimal valid message if everything was filtered out
        logger.warning("[DEBUG-TRUNCATE] No messages left after truncation, adding a minimal valid message")
        result_messages = [{"role": "user", "content": "..."}]

    # Make sure messages have content
    for i, msg in enumerate(result_messages):
        if not msg.get("content"):
            logger.warning(f"[DEBUG-TRUNCATE] Empty content in message {i}, adding minimal content")
            msg["content"] = "..."

    return result_messages


def truncate_message_content(
    message: dict[str, str],
    max_tokens: int,
    model: str = "gpt-4.1",
) -> dict[str, str]:
    """Truncate the content of a message to fit within max_tokens.

    Args:
        message (dict[str, str]): The message to truncate
        max_tokens (int): Maximum tokens for the message
        model (str): The model to use for token estimation

    Returns:
        dict[str, str]: Truncated message
    """
    # DEBUG: Log function entry
    logger.info(f"[DEBUG-TRUNCATE] Truncating individual message to fit {max_tokens} tokens")

    # Create a copy of the message to avoid modifying the original
    truncated_message: dict[str, str] = message.copy()
    content: str = message.get("content", "")

    # Calculate minimum viable token space needed for basic message structure
    # Estimate role tokens + message format overhead
    role_tokens = len(message.get("role", "system"))
    estimated_overhead = role_tokens + 5  # Role + basic formatting overhead

    # If max_tokens is less than the overhead plus minimal content, return minimal message
    if max_tokens <= estimated_overhead + 1:
        logger.warning(f"[DEBUG-TRUNCATE] max_tokens ({max_tokens}) too small for content after overhead ({estimated_overhead}), using minimal content")
        truncated_message["content"] = "..."
        return truncated_message

    # Reserve tokens for message formatting and role
    truncated_tokens: int = max_tokens - estimated_overhead

    if truncated_tokens <= 0:
        logger.warning("[DEBUG-TRUNCATE] Not enough tokens for content after formatting, using minimal content")
        truncated_message["content"] = "..."
        return truncated_message

    # More efficient truncation approach using binary search
    # The number of iterations scales with content size
    content_length = len(content)
    start_ratio = 0.0
    end_ratio = 1.0
    best_content = "..."  # Default minimal content
    best_token_count = 0

    # Calculate number of iterations based on content length
    # Logarithmic scaling to use more iterations for larger content
    max_iterations = max(3, min(12, int(math.log(content_length + 1, 2))))

    logger.info(f"[DEBUG-TRUNCATE] Binary search with {max_iterations} iterations for content length {content_length}")

    # Binary search phase
    for iteration in range(max_iterations):
        mid_ratio = (start_ratio + end_ratio) / 2
        current_length = int(len(content) * mid_ratio)

        if current_length <= 0:
            break

        truncated_content = content[:current_length]
        truncated_message["content"] = truncated_content
        token_count = estimate_token_count([truncated_message], model)

        logger.info(f"[DEBUG-TRUNCATE] Binary search iteration {iteration+1}/{max_iterations} - ratio: {mid_ratio:.4f}, tokens: {token_count}/{max_tokens}")

        if token_count <= max_tokens:
            # This fits, save it and try larger
            best_content = truncated_content
            best_token_count = token_count
            start_ratio = mid_ratio
        else:
            # Too large, try smaller
            end_ratio = mid_ratio

        # Determine dynamic termination condition based on context size
        # For smaller contexts, we can be more precise
        precision_factor = min(0.01, 10.0 / content_length)
        if end_ratio - start_ratio < precision_factor:
            logger.info(f"[DEBUG-TRUNCATE] Terminating binary search early at iteration {iteration+1} - precision reached")
            break

    # If we found a valid content size in binary search
    if best_token_count > 0:
        truncated_message["content"] = best_content
        logger.info(f"[DEBUG-TRUNCATE] Truncation successful. Final content length: {len(best_content)}")
        return truncated_message

    # If binary search failed, fall back to a minimal content approach
    truncated_message["content"] = "..."
    logger.warning("[DEBUG-TRUNCATE] Couldn't truncate enough, returning minimal content")
    return truncated_message


def truncate_system_messages(
    system_messages: list[dict[str, str]],
    max_tokens: int,
    model: str = "gpt-4.1",
) -> list[dict[str, str]]:
    """Truncate system messages to fit within max_tokens.

    Args:
        system_messages (list[dict[str, str]]): List of system messages
        max_tokens (int): Maximum tokens to fit within
        model (str): Model to use for token estimation

    Returns:
        list[dict[str, str]]: Truncated system messages
    """
    # DEBUG: Log function entry
    logger.info(f"[DEBUG-TRUNCATE] Truncating system messages to fit {max_tokens} tokens")

    if not system_messages:
        return []

    # Calculate minimum viable token count for a valid system message
    # Role "system" + minimal content + formatting
    min_system_tokens = estimate_token_count([{"role": "system", "content": "..."}], model)

    # If max_tokens is less than minimum needed, return minimal message
    if max_tokens <= min_system_tokens:
        logger.warning(f"[DEBUG-TRUNCATE] max_tokens ({max_tokens}) less than minimum needed for system message ({min_system_tokens}), returning minimal system message")
        return [{"role": "system", "content": "..."}]

    if len(system_messages) == 1:
        # Only one system message, truncate its content
        return [truncate_message_content(system_messages[0], max_tokens, model)]

    # Multiple system messages
    # Try to keep as many as possible, starting with the first one
    # which is typically the most important
    result_messages = []
    remaining_tokens = max_tokens

    for i, msg in enumerate(system_messages):
        msg_tokens = estimate_token_count([msg], model)
        if msg_tokens <= remaining_tokens:
            # This message fits entirely
            result_messages.append(msg)
            remaining_tokens -= msg_tokens
        elif i == 0:
            # First message doesn't fit, truncate it
            truncated = truncate_message_content(msg, remaining_tokens, model)
            result_messages.append(truncated)
            break
        else:
            # Subsequent message doesn't fit, stop adding
            break

    # Log the result
    logger.info(f"[DEBUG-TRUNCATE] Kept {len(result_messages)}/{len(system_messages)} system messages within token limit")
    for i, msg in enumerate(result_messages):
        content_len = len(msg.get("content", ""))
        logger.info(f"[DEBUG-TRUNCATE] System message {i}: {content_len} chars")

    return result_messages


async def create_chat_completion(
    messages: list[dict[str, str]],  # type: ignore
    model: str | None = None,
    temperature: float | None = None,
    max_tokens: int | None = None,
    llm_provider: str | None = None,
    stream: bool | None = False,
    websocket: Any | None = None,
    llm_kwargs: dict[str, Any] | None = None,
    cost_callback: Callable[[float], None] | None = None,
    reasoning_effort: ReasoningEfforts | None = None,
    cfg: Config | None = None,
    **kwargs,
) -> str:
    """Create a chat completion using the API

    Args:
        messages (list[dict[str, str]]): The messages to send to the chat completion
        model (str, optional): The model to use. Defaults to None.
        temperature (float, optional): The temperature to use. Defaults to None.
        max_tokens (int, optional): The max tokens to use. If None, determined dynamically.
        stream (bool, optional): Whether to stream the response. Defaults to False.
        llm_provider (str, optional): The LLM Provider to use.
        webocket (WebSocket): The websocket used in the currect request,
        cost_callback: Callback function for updating cost
        reasoning_effort: The reasoning effort to use.
        cfg (Config, optional): Configuration object. If None, a new one will be created.
        **kwargs: Additional keyword arguments.

    Returns:
        str: The response from the chat completion
    """
    # validate input
    if model is None:
        raise ValueError("Model cannot be None")

    # DEBUG: Log function entry with basic info
    logger.info(f"[DEBUG-LLM] create_chat_completion called with model={model}, provider={llm_provider}, max_tokens={max_tokens}")
    logger.info(f"[DEBUG-LLM] Number of messages: {len(messages)}")

    # Dynamic context limit determination
    # Instead of hardcoded values, we'll query the model or use a conservative estimate
    config_obj: Config = cfg or Config()

    # Initialize the provider to get capabilities
    provider: GenericLLMProvider = get_llm(
        llm_provider,
        cfg=cfg,
        model=model,
        temperature=temperature,
        max_tokens=max_tokens,
        **(llm_kwargs or {}),
    )

    # Try to get context limits from provider if supported
    default_context_limit = getattr(provider.llm, "context_length", None)
    if default_context_limit is None:
        # If not available, derive from config or use dynamic estimation
        if model == config_obj.fast_llm_model:
            default_context_limit = getattr(config_obj, "fast_llm_context_length", None)
        elif model == config_obj.smart_llm_model:
            default_context_limit = getattr(config_obj, "smart_llm_context_length", None)
        elif model == config_obj.strategic_llm_model:
            default_context_limit = getattr(config_obj, "strategic_llm_context_length", None)

    if default_context_limit is None:
        # Conservative estimate if no specific info is available
        # For OpenRouter, extract from model name if possible
        if model and "32k" in model:
            default_context_limit = 32000
        elif model and "16k" in model:
            default_context_limit = 16000
        elif model and "8k" in model:
            default_context_limit = 8000
        else:
            # Default to a conservative estimate based on provider
            if llm_provider == "anthropic" or "claude" in (model or ""):
                default_context_limit = 100000  # Claude models typically have large contexts
            elif "gemini" in (model or ""):
                default_context_limit = 32000  # Gemini models typically have larger contexts
            elif llm_provider == "openai" or llm_provider == "openrouter":
                default_context_limit = 8000  # Conservative default for OpenAI
            else:
                default_context_limit = 4000  # Ultra-conservative fallback

    logger.info(f"[DEBUG-LLM] Estimated model context limit: {default_context_limit}")

    from gpt_researcher.llm_provider.generic.base import (
        NO_SUPPORT_TEMPERATURE_MODELS,
        SUPPORT_REASONING_EFFORT_MODELS,
    )

    # DEBUG: Log model capabilities
    logger.info(f"[DEBUG-LLM] Model in NO_SUPPORT_TEMPERATURE_MODELS: {model in NO_SUPPORT_TEMPERATURE_MODELS}")
    logger.info(f"[DEBUG-LLM] Model in SUPPORT_REASONING_EFFORT_MODELS: {model in SUPPORT_REASONING_EFFORT_MODELS}")

    if model in SUPPORT_REASONING_EFFORT_MODELS:
        kwargs["reasoning_effort"] = reasoning_effort
        logger.info(f"[DEBUG-LLM] Added reasoning_effort={reasoning_effort} to kwargs")

    if model not in NO_SUPPORT_TEMPERATURE_MODELS:
        if temperature is not None:
            kwargs["temperature"] = temperature
        if max_tokens is not None:
            kwargs["max_tokens"] = max_tokens
    else:
        if "temperature" in kwargs:
            del kwargs["temperature"]
            logger.info("[DEBUG-LLM] Removed temperature from kwargs")
        if "max_tokens" in kwargs:
            del kwargs["max_tokens"]
            logger.info("[DEBUG-LLM] Removed max_tokens from kwargs")

    if llm_provider == "openai":
        base_url: str | None = os.environ.get("OPENAI_BASE_URL", None)
        if base_url:
            kwargs["openai_api_base"] = base_url
            logger.info(f"[DEBUG-LLM] Using custom OpenAI base URL: {base_url}")

    # Initialize provider and prepare for retries
    provider = get_llm(llm_provider, cfg=cfg, **kwargs)
    original_max_tokens: int | None = max_tokens

    # Dynamic retry count based on config or reasonable default
    MAX_ATTEMPTS: int = getattr(config_obj, "llm_retry_attempts", 3)
    response: str = ""

    # Calculate appropriate token values based on context size
    # Estimate input token count
    input_token_count: int = estimate_token_count(messages, model)
    logger.info(f"[DEBUG-LLM] Estimated input token count: {input_token_count}")

    # Dynamic output token allocation based on context size
    # If max_tokens is specified, use that, otherwise allocate a portion of context
    # The portion is inversely proportional to the input size (larger inputs = smaller portion for output)
    if max_tokens is None:
        # Calculate a dynamic ratio based on input size
        input_ratio = min(input_token_count / default_context_limit, 0.9)  # Cap at 90%
        output_ratio = 1.0 - input_ratio
        # Ensure output has at least some reasonable space
        output_tokens = max(int(default_context_limit * output_ratio), int(default_context_limit * 0.1))
    else:
        output_tokens = max_tokens

    # Special handling for providers with strict token limits
    if llm_provider == "openrouter":
        # OpenRouter is sensitive to total tokens, adjust if needed
        if max_tokens is None or max_tokens > int(default_context_limit * 0.5):
            # Limit to a reasonable portion of context to avoid errors
            output_ratio = min(0.3, 1.0 - (input_token_count / default_context_limit))
            output_tokens = int(default_context_limit * output_ratio)

            # Update max_tokens in the parameters
            if "max_tokens" in kwargs:
                kwargs["max_tokens"] = output_tokens
                logger.info(f"[DEBUG-LLM] Adjusted OpenRouter max_tokens to {output_tokens}")

            # Reinitialize provider with updated parameters
            provider = get_llm(llm_provider, cfg=cfg, **kwargs)

    # Adaptive context window management
    max_context_tokens = default_context_limit - output_tokens

    # Ensure context has room for at least a minimal message
    # Instead of hardcoding, calculate as a percentage of total context
    min_context_portion = default_context_limit * 0.025  # 2.5% of context
    max_context_tokens = max(int(min_context_portion), max_context_tokens)

    # Log the calculated limits
    logger.info(f"[DEBUG-LLM] Reserved for output: {output_tokens} tokens")
    logger.info(f"[DEBUG-LLM] Available for input context: {max_context_tokens} tokens")

    # If messages exceed context limit, truncate them
    if input_token_count > max_context_tokens:
        logger.warning(f"[DEBUG-LLM] Messages exceed token limit ({input_token_count} > {max_context_tokens}), truncating content")
        # Log message content sizes before truncation
        for i, msg in enumerate(messages):
            role = msg.get("role", "unknown")
            content_len = len(msg.get("content", ""))
            logger.info(f"[DEBUG-LLM] Before truncation - Message {i} ({role}): {content_len} chars")

        messages = truncate_messages_to_fit(messages, max_context_tokens, model)

        # Log message content sizes after truncation
        for i, msg in enumerate(messages):
            role = msg.get("role", "unknown")
            content_len = len(msg.get("content", ""))
            logger.info(f"[DEBUG-LLM] After truncation - Message {i} ({role}): {content_len} chars")
            # Log preview of each message after truncation
            content_preview = msg.get("content", "")
            if len(content_preview) > 100:
                content_preview = content_preview[:100] + "..."
            logger.info(f"[DEBUG-LLM] After truncation - Message {i} preview: {content_preview}")

    # Attempt to get a response with fallback for token limits and transient errors
    for attempt in range(MAX_ATTEMPTS):
        try:
            # DEBUG: Log attempt information
            logger.info(f"[DEBUG-LLM] Attempt {attempt+1}/{MAX_ATTEMPTS} to get chat response")

            response: str = await provider.get_chat_response(messages, stream, websocket)

            # DEBUG: Log successful response
            logger.info(f"[DEBUG-LLM] Got successful response (length: {len(response)})")
            if len(response) > 200:
                logger.info(f"[DEBUG-LLM] Response preview: {response[:200]}...")
            else:
                logger.info(f"[DEBUG-LLM] Full response: {response}")

            # Validate the response - this will raise an exception if invalid
            try:
                validated_response = validate_llm_response(response, f"LLM call to {llm_provider}:{model}")
                response = validated_response
            except ValueError as validation_error:
                logger.error(f"[DEBUG-LLM] Response validation failed: {validation_error}")
                # Treat validation failure as an error to trigger fallbacks
                raise validation_error

            if cost_callback is not None:
                llm_costs: float = estimate_llm_cost(str(messages), response)
                cost_callback(llm_costs)

        except Exception as e:
            err_msg: str = str(e)

            # Special handling for OpenRouter
            if llm_provider == "openrouter" and "maximum context length" in err_msg and attempt < MAX_ATTEMPTS - 1:
                # Extract token limit info if available
                import re
                limit_match = re.search(r"maximum context length is (\d+)", err_msg)
                requested_match = re.search(r"requested about (\d+) tokens", err_msg)

                if limit_match and requested_match:
                    actual_limit = int(limit_match.group(1))
                    requested = int(requested_match.group(1))

                    logger.warning(f"[DEBUG-LLM] OpenRouter token limit exceeded. Limit: {actual_limit}, Requested: {requested}")

                    # Update our context limit understanding with the real value
                    default_context_limit = actual_limit

                    # Allocate tokens dynamically based on actual limit
                    # Use a small percentage for output to maximize context space
                    output_ratio = min(0.1, (actual_limit - input_token_count) / actual_limit)
                    if output_ratio <= 0:
                        # If we can't fit the input, need to truncate
                        output_ratio = 0.1  # Reserve 10% for output

                    new_output_tokens = max(int(actual_limit * output_ratio), 1)
                    new_context_tokens = actual_limit - new_output_tokens

                    # Update parameters
                    if "max_tokens" in kwargs:
                        kwargs["max_tokens"] = new_output_tokens
                        logger.info(f"[DEBUG-LLM] Adjusted max_tokens to {new_output_tokens}")

                    # Reinitialize provider and truncate messages
                    provider = get_llm(llm_provider, cfg=cfg, **kwargs)
                    messages = truncate_messages_to_fit(messages, new_context_tokens, model)
                    continue

            # Fallback for max_tokens errors: remove max_tokens if that's the issue
            if "max_tokens" in err_msg.casefold() and ("too large" in err_msg.casefold() or "supports at most" in err_msg.casefold()):
                logger.warning(f"[DEBUG-LLM] max_tokens issue ({original_max_tokens}), retrying without max_tokens: {traceback.format_exc()}")
                if "max_tokens" in kwargs:
                    del kwargs["max_tokens"]
                provider: GenericLLMProvider = get_llm(llm_provider, cfg=cfg, **kwargs)
                continue
            if "'unrecognized request argument supplied: reasoning_effort'" in err_msg.casefold():
                logger.warning(f"[DEBUG-LLM] reasoning_effort={reasoning_effort} not supported by this model, retrying without reasoning_effort: {traceback.format_exc()}")
                if "reasoning_effort" in kwargs:
                    del kwargs["reasoning_effort"]
                provider: GenericLLMProvider = get_llm(llm_provider, cfg=cfg, **kwargs)
                continue
            logger.error(f"[DEBUG-LLM] Error in attempt {attempt+1}: {traceback.format_exc()}")

            # Context length error: truncate messages further and retry
            if "context length" in err_msg.casefold() or "context_length_exceeded" in err_msg.casefold():
                logger.warning("[DEBUG-LLM] Context length exceeded, further truncating messages")

                # DEBUG: Log message content sizes before aggressive truncation
                for i, msg in enumerate(messages):
                    role = msg.get("role", "unknown")
                    content_len = len(msg.get("content", ""))
                    logger.info(f"[DEBUG-LLM] Before aggressive truncation - Message {i} ({role}): {content_len} chars")

                # Reduce context dynamically based on how many attempts we've made
                # More aggressive truncation with each attempt
                reduction_factor = 1.0 - (0.3 * (attempt + 1))  # 30% more reduction each attempt
                reduction_factor = max(reduction_factor, 0.2)  # Don't go below 20% of original

                new_max_tokens = int(max_context_tokens * reduction_factor)
                logger.info(f"[DEBUG-LLM] Reducing context tokens from {max_context_tokens} to {new_max_tokens}")
                messages = truncate_messages_to_fit(messages, new_max_tokens, model)

                # DEBUG: Log message content sizes after aggressive truncation
                for i, msg in enumerate(messages):
                    role = msg.get("role", "unknown")
                    content_len = len(msg.get("content", ""))
                    logger.info(f"[DEBUG-LLM] After aggressive truncation - Message {i} ({role}): {content_len} chars")
                    # Log preview of each message after truncation
                    content_preview = msg.get("content", "")
                    if len(content_preview) > 100:
                        content_preview = content_preview[:100] + "..."
                    logger.info(f"[DEBUG-LLM] After aggressive truncation - Message {i} preview: {content_preview}")
                continue

            # Transient errors: retry with exponential backoff
            if attempt < MAX_ATTEMPTS - 1:
                backoff: int = 2**attempt
                logger.warning(f"[DEBUG-LLM] Error calling LLM (attempt {attempt + 1}/{MAX_ATTEMPTS}): {traceback.format_exc()}, retrying in {backoff}s")
                await asyncio.sleep(backoff)
                continue
            logger.error(f"[DEBUG-LLM] Failed to get response from '{llm_provider}' API after {MAX_ATTEMPTS} attempts: {traceback.format_exc()}")
            raise
        else:
            # DEBUG: Log successful return
            logger.info(f"[DEBUG-LLM] Successfully returning response from attempt {attempt+1} (response has length {len(response)})")
            return response

    # If all retries fail, raise an error
    logger.error(f"[DEBUG-LLM] All retries exhausted for '{llm_provider}' API")
    raise RuntimeError(f"All retries exhausted for '{llm_provider}' API")


async def construct_subtopics(
    task: str,
    data: str,
    config: Config,
    subtopics: list[str] | None = None,
    prompt_family: type[PromptFamily] | PromptFamily = PromptFamily,
) -> list[str]:
    """Construct subtopics based on the given task and data.

        Args:
            task (str): The main task or topic. Truncation attempt - ratio: 1e-323, tokens: 9/5
    """
    subtopics = [] if subtopics is None else subtopics
    try:
        parser = PydanticOutputParser(pydantic_object=Subtopics)

        prompt = PromptTemplate(
            template=prompt_family.generate_subtopics_prompt(),
            input_variables=["task", "data", "subtopics", "max_subtopics"],
            partial_variables={"format_instructions": parser.get_format_instructions()},
        )

        print(f"\n🤖 Calling {config.smart_llm_model}...\n")

        temperature: float = config.llm_kwargs.get("temperature", getattr(config, "temperature", 0.4))
        # temperature = 0 # Note: temperature throughout the code base is currently set to Zero
        provider: GenericLLMProvider = get_llm(
            config.smart_llm_provider,
            cfg=config,
            model=config.smart_llm_model,
            temperature=temperature,
            #            max_tokens=config.llm_kwargs.get("smart_token_limit", getattr(config, "smart_token_limit", 4000)),
            **config.llm_kwargs,
        )
        model: BaseLLM = provider.llm

        chain = prompt | model | parser

        output: list[str] = chain.invoke(
            {
                "task": task,
                "data": data,
                "subtopics": subtopics,
                "max_subtopics": config.llm_kwargs.get("max_subtopics", getattr(config, "max_subtopics", 5)),
            }
        )

        return output

    except Exception as e:
        print(f"Exception in parsing subtopics: {traceback.format_exc()}")
        return subtopics


def validate_llm_response(response: str, operation: str = "LLM operation") -> str:
    """Validate LLM response and raise an error if it's invalid.

    Args:
        response: The response from the LLM
        operation: Description of the operation for error messages

    Returns:
        The validated response

    Raises:
        ValueError: If the response is invalid
    """
    if not response or not response.strip():
        raise ValueError(f"{operation} failed: Empty response received")

    # Check for common error patterns
    error_patterns: list[str] = [
        "I'm sorry, but I cannot provide a response",
        "I cannot complete this request",
        "I'm unable to process this",
    ]

    response_lower: str = response.lower()
    for pattern in error_patterns:
        if pattern.lower() in response_lower:
            raise ValueError(f"{operation} failed: Response contains error pattern: '{pattern}'")

    # Check for suspiciously short responses (less than 8 characters)
    if len(response.strip()) < 8:
        raise ValueError(f"{operation} failed: Response too short ({len(response.strip())} characters)")

    return response


def extract_json_from_markdown(response: str) -> str:
    """Extract JSON content from markdown code blocks.

    Args:
        response: Response that may contain JSON wrapped in markdown

    Returns:
        Extracted JSON string or original response if no markdown blocks found
    """
    # Look for JSON in markdown code blocks
    json_pattern = r"```(?:json)?\s*(\{.*?\})\s*```"
    match: re.Match[str] | None = re.search(json_pattern, response, re.DOTALL | re.IGNORECASE)
    if match is not None:
        return match.group(1).strip()

    # Look for JSON arrays in markdown code blocks
    json_array_pattern = r"```(?:json)?\s*(\[.*?\])\s*```"
    match = re.search(json_array_pattern, response, re.DOTALL | re.IGNORECASE)
    if match is not None:
        return match.group(1).strip()

    return response
