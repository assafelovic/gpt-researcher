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

    # Ensure max_context_tokens is at least 10 to prevent empty messages
    if max_context_tokens <= 0:
        logger.warning(f"[DEBUG-TRUNCATE] max_context_tokens too small ({max_context_tokens}), setting to minimum 10")
        max_context_tokens = 10

    # Separate system messages from user/assistant messages
    system_messages: list[dict[str, str]] = [msg for msg in messages if msg.get("role", "") == "system"]
    user_assistant_messages: list[dict[str, str]] = [msg for msg in messages if msg.get("role", "") != "system"]

    # DEBUG: Log message counts by type
    logger.info(f"[DEBUG-TRUNCATE] System messages: {len(system_messages)}, User/Assistant messages: {len(user_assistant_messages)}")

    # Estimate token count for system messages
    system_token_count: int = estimate_token_count(system_messages, model)

    # DEBUG: Log system message token count
    logger.info(f"[DEBUG-TRUNCATE] System messages token count: {system_token_count}")

    # Allocate the remaining tokens to user/assistant messages
    remaining_tokens: int = max_context_tokens - system_token_count

    # DEBUG: Log remaining tokens
    logger.info(f"[DEBUG-TRUNCATE] Remaining tokens for user/assistant messages: {remaining_tokens}")

    if remaining_tokens <= 0:
        # Not enough tokens for any user/assistant messages, truncate system messages
        # (This should be rare, but handle it just in case)
        logger.warning("[DEBUG-TRUNCATE] System messages exceed max tokens, truncating system messages")
        return truncate_system_messages(system_messages, max_context_tokens, model)

    # We need to keep an ordered list of messages for further processing
    result_messages: list[dict[str, str]] = system_messages.copy()

    # For user/assistant messages, prioritize the most recent ones
    # Start from the end (most recent) and keep adding messages until we reach the limit
    user_assistant_messages.reverse()  # Reverse to prioritize recent messages
    current_tokens: int = system_token_count
    current_messages: list[dict[str, str]] = []

    # DEBUG: Log process start
    logger.info("[DEBUG-TRUNCATE] Starting to add user/assistant messages (newest first)")

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

    # Ensure we have at least one message with non-empty content
    if not result_messages:
        # Create a minimal valid message if everything was filtered out
        logger.warning("[DEBUG-TRUNCATE] No messages left after truncation, adding a minimal valid message")
        result_messages = [{"role": "user", "content": "..."}]
    elif all(not msg.get("content") for msg in result_messages):
        # If all messages have empty content, add minimal content to one
        logger.warning("[DEBUG-TRUNCATE] All messages have empty content, adding minimal content to first message")
        result_messages[0]["content"] = "..."

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

    # Ensure we have at least some minimal content
    if max_tokens <= 0:
        logger.warning(f"[DEBUG-TRUNCATE] max_tokens too small ({max_tokens}), setting to minimum 5")
        max_tokens = 5

    # Reserve tokens for message formatting and role
    # These values are rough estimates
    formatting_tokens: int = 4  # Rough estimate for message format
    truncated_tokens: int = max_tokens - formatting_tokens

    if truncated_tokens <= 0:
        logger.warning("[DEBUG-TRUNCATE] Not enough tokens for content after formatting, using minimal content")
        # Instead of empty string, use minimal content that will pass API validation
        truncated_message["content"] = "..."
        return truncated_message

    # Truncate the content
    # This is a simple truncation, it's not perfect but should work for most cases
    # A better approach would be to truncate at a sentence or paragraph boundary
    # Start with a small portion and gradually increase until we hit the limit
    ratio: float = 0.5  # Start with half the content
    while ratio > 0:
        # Try with the current ratio
        truncated_content: str = content[: int(len(content) * ratio)]
        # Ensure we never have empty content
        if not truncated_content:
            truncated_content = "..."

        truncated_message["content"] = truncated_content

        # Check if it fits
        token_count: int = estimate_token_count([truncated_message], model)
        # DEBUG: Log truncation attempt
        logger.info(f"[DEBUG-TRUNCATE] Truncation attempt - ratio: {ratio}, tokens: {token_count}/{max_tokens}")

        if token_count <= max_tokens:
            # It fits, we're done
            # DEBUG: Log success
            logger.info(f"[DEBUG-TRUNCATE] Truncation successful. Final content length: {len(truncated_content)}")
            return truncated_message

        # It doesn't fit, try a smaller ratio
        ratio *= 0.75

    # If we get here, we couldn't truncate enough
    # Just return a very small message with guaranteed non-empty content
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

    # Ensure max_tokens is at least 5 to allow for minimal valid content
    if max_tokens <= 0:
        logger.warning(f"[DEBUG-TRUNCATE] max_tokens too small ({max_tokens}), setting to minimum 5")
        max_tokens = 5

    if len(system_messages) == 1:
        # Only one system message, truncate its content
        return [truncate_message_content(system_messages[0], max_tokens, model)]

    # Multiple system messages, prioritize the first one
    first_message: dict[str, str] = system_messages[0]
    truncated_first: dict[str, str] = truncate_message_content(first_message, max_tokens, model)

    # DEBUG: Log result
    logger.info(f"[DEBUG-TRUNCATE] Kept only first system message, truncated to {len(truncated_first.get('content', ''))} chars")

    return [truncated_first]


async def create_chat_completion(
    messages: list[dict[str, str]],  # type: ignore
    model: str | None = None,
    temperature: float | None = 0.4,
    max_tokens: int | None = 4000,
    llm_provider: str | None = None,
    stream: bool | None = False,
    websocket: Any | None = None,
    llm_kwargs: dict[str, Any] | None = None,
    cost_callback: Callable[[float], None] | None = None,
    reasoning_effort: ReasoningEfforts | None = None,
    cfg: Config | None = None,
    **kwargs,
) -> str:
    """Create a chat completion using the OpenAI API

    Args:
        messages (list[dict[str, str]]): The messages to send to the chat completion
        model (str, optional): The model to use. Defaults to None.
        temperature (float, optional): The temperature to use. Defaults to 0.4.
        max_tokens (int, optional): The max tokens to use. Defaults to 4000.
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
    if max_tokens is not None and max_tokens > 32001:
        raise ValueError(f"Max tokens cannot be more than 16,000, but got {max_tokens}")

    # DEBUG: Log function entry with basic info
    logger.info(f"[DEBUG-LLM] create_chat_completion called with model={model}, provider={llm_provider}, max_tokens={max_tokens}")
    logger.info(f"[DEBUG-LLM] Number of messages: {len(messages)}")

    # Get the provider from supported providers
    provider: GenericLLMProvider = get_llm(
        llm_provider,
        cfg=cfg,
        model=model,
        temperature=temperature,
        max_tokens=max_tokens,
        **(llm_kwargs or {}),
    )

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
        kwargs["temperature"] = temperature
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
    MAX_ATTEMPTS: int = 3
    response: str = ""

    # Check token count and truncate if needed
    model_max_tokens: int = 16000  # Default max context length
    if "gpt-4" in model and "gpt-4.1" not in model:
        model_max_tokens = 8000 if "8k" in model else 16000
        if "32k" in model:
            model_max_tokens = 32000

    # DEBUG: Log model token limits
    logger.info(f"[DEBUG-LLM] Model {model} has max_tokens={model_max_tokens}")

    # Estimate token count of messages
    token_count: int = estimate_token_count(messages, model)

    # DEBUG: Log token count info
    logger.info(f"[DEBUG-LLM] Estimated token count: {token_count}")

    # Reserve tokens for completion
    completion_tokens: int = max_tokens or 4000
    max_context_tokens: int = model_max_tokens - completion_tokens

    # DEBUG: Log token allocation
    logger.info(f"[DEBUG-LLM] Reserved for completion: {completion_tokens} tokens")
    logger.info(f"[DEBUG-LLM] Max context tokens: {max_context_tokens}")

    # Ensure max_context_tokens is at least 10 to prevent empty messages
    # This guarantees we'll have at least a minimal valid message
    if max_context_tokens <= 0:
        logger.warning(f"[DEBUG-LLM] Max context tokens too small ({max_context_tokens}), setting to minimum 10")
        max_context_tokens = 10

    # If messages exceed context limit, truncate them
    if token_count > max_context_tokens:
        logger.warning(f"[DEBUG-LLM] Messages exceed token limit ({token_count} > {max_context_tokens}), truncating content")
        # DEBUG: Log message content sizes before truncation
        for i, msg in enumerate(messages):
            role = msg.get("role", "unknown")
            content_len = len(msg.get("content", ""))
            logger.info(f"[DEBUG-LLM] Before truncation - Message {i} ({role}): {content_len} chars")

        messages = truncate_messages_to_fit(messages, max_context_tokens, model)

        # DEBUG: Log message content sizes after truncation
        for i, msg in enumerate(messages):
            role = msg.get("role", "unknown")
            content_len = len(msg.get("content", ""))
            logger.info(f"[DEBUG-LLM] After truncation - Message {i} ({role}): {content_len} chars")
            # Log first 100 chars of each message after truncation
            content_preview = msg.get("content", "")[:100] + "..." if len(msg.get("content", "")) > 100 else msg.get("content", "")
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

                # Cut the context limit in half for more aggressive truncation
                new_max_tokens = max_context_tokens // 2
                logger.info(f"[DEBUG-LLM] Reducing context tokens from {max_context_tokens} to {new_max_tokens}")
                messages = truncate_messages_to_fit(messages, new_max_tokens, model)

                # DEBUG: Log message content sizes after aggressive truncation
                for i, msg in enumerate(messages):
                    role = msg.get("role", "unknown")
                    content_len = len(msg.get("content", ""))
                    logger.info(f"[DEBUG-LLM] After aggressive truncation - Message {i} ({role}): {content_len} chars")
                    # Log first 100 chars of each message after truncation
                    content_preview = msg.get("content", "")[:100] + "..." if len(msg.get("content", "")) > 100 else msg.get("content", "")
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
        task (str): The main task or topic.
        data (str): Additional data for context.
        config: Configuration settings.
        subtopics (list, optional): Existing subtopics. Defaults to [].
        prompt_family (PromptFamily): Family of prompts

    Returns:
        list[str]: A list of constructed subtopics.
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
