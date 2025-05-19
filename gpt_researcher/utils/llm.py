# libraries
from __future__ import annotations

import asyncio
import logging
import os
import tiktoken
from collections.abc import Callable
from typing import TYPE_CHECKING, Any

from langchain.llms.base import BaseLLM
from langchain.output_parsers import PydanticOutputParser
from langchain.prompts import PromptTemplate

from gpt_researcher.config.config import Config
from gpt_researcher.prompts import PromptFamily
from gpt_researcher.utils.costs import estimate_llm_cost
from gpt_researcher.utils.validators import Subtopics

if TYPE_CHECKING:
    from gpt_researcher.llm_provider.generic.base import (
        GenericLLMProvider,
        ReasoningEfforts,
    )


def get_llm(llm_provider: str, **kwargs) -> GenericLLMProvider:
    """Initialize an LLM provider with fallback support.

    Args:
        llm_provider: Provider name (e.g., 'openai')
        **kwargs: Additional keyword arguments for the provider

    Returns:
        LLM provider instance with fallback support if fallbacks are configured
    """
    from gpt_researcher.llm_provider.generic.base import GenericLLMProvider
    from gpt_researcher.llm_provider.generic.fallback import FallbackGenericLLMProvider

    # Check if this LLM has fallbacks configured
    cfg: Config = Config()
    fallback_list: list[str] = []
    if 'model' in kwargs:
        model_name: str = kwargs.get('model')

        # Determine which fallback list to use based on the model
        if cfg.fast_llm_model == model_name and cfg.fast_llm_provider == llm_provider:
            fallback_list = cfg.fast_llm_fallback_list
        elif cfg.smart_llm_model == model_name and cfg.smart_llm_provider == llm_provider:
            fallback_list = cfg.smart_llm_fallback_list
        elif cfg.strategic_llm_model == model_name and cfg.strategic_llm_provider == llm_provider:
            fallback_list = cfg.strategic_llm_fallback_list

    # If fallbacks are configured, use fallback provider
    if fallback_list:
        # Log fallback models when fallbacks are enabled
        logging.info(f"Using {llm_provider}:{kwargs.get('model', '')} with fallbacks: {', '.join(fallback_list)}")

        return FallbackGenericLLMProvider.from_provider_with_fallbacks(llm_provider, fallback_list, **kwargs)

    # Otherwise, use standard provider
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
    """Truncate messages to fit within token limit by removing or shortening content.

    Args:
        messages (list[dict[str, str]]): Messages to truncate
        max_context_tokens (int): Maximum context token limit
        model (str, optional): Model to use for token estimation. Defaults to "gpt-4.1".

    Returns:
        list[dict[str, str]]: Truncated messages
    """
    # Don't modify system message or the most recent user message
    if len(messages) <= 2:
        return messages

    try:
        encoding: tiktoken.Encoding = tiktoken.encoding_for_model(model)
    except KeyError:
        encoding = tiktoken.get_encoding("cl100k_base")

    # Make a copy to avoid modifying original
    truncated_messages: list[dict[str, str]] = messages.copy()

    # Reserve tokens for system message and the last user message
    reserved_tokens: int = 0
    system_message: dict[str, str] | None = None
    last_user_message: dict[str, str] | None = None

    # Find system message and last user message
    for i in range(len(truncated_messages)):
        if truncated_messages[i]["role"] == "system":
            system_message = truncated_messages[i]
            reserved_tokens += 4 + len(encoding.encode(system_message["content"]))
        if truncated_messages[i]["role"] == "user" and i == len(truncated_messages) - 1:
            last_user_message = truncated_messages[i]
            reserved_tokens += 4 + len(encoding.encode(last_user_message["content"]))

    # Available tokens for other messages
    available_tokens: int = max_context_tokens - reserved_tokens - 3  # 3 for final overhead

    # Identify messages that can be truncated (not system or last user message)
    truncatable_indices: list[int] = []
    for i in range(len(truncated_messages)):
        if (truncated_messages[i] != system_message and
            truncated_messages[i] != last_user_message):
            truncatable_indices.append(i)

    # If there are no truncatable messages, return original
    if not truncatable_indices:
        return messages

    # Start removing content from oldest messages first
    current_tokens: int = estimate_token_count(truncated_messages, model) - reserved_tokens

    while current_tokens > available_tokens and truncatable_indices:
        # Get the oldest message to truncate
        index: int = truncatable_indices[0]
        message: dict[str, str] = truncated_messages[index]

        # Calculate current tokens in this message
        message_tokens: int = 4 + len(encoding.encode(message["content"]))

        # Remove this message entirely
        truncated_messages.pop(index)
        for i in range(len(truncatable_indices)):
            if truncatable_indices[i] > index:
                truncatable_indices[i] -= 1
        truncatable_indices.pop(0)

        current_tokens -= message_tokens

    # Create a new message list with system message, filtered messages, and last user message
    final_messages: list[dict[str, str]] = []

    for msg in truncated_messages:
        if msg == system_message:
            final_messages.append(msg)
        elif msg == last_user_message:
            continue  # Skip for now, will add at the end
        else:
            final_messages.append(msg)

    # Add the last user message at the end
    if last_user_message:
        final_messages.append(last_user_message)

    logging.info(f"Truncated messages from {estimate_token_count(messages, model)} to {estimate_token_count(final_messages, model)} tokens")

    return final_messages


async def create_chat_completion(
    messages: list[dict[str, str]],  # type: ignore
    model: str | None = None,
    temperature: float | None = 0.4,
    max_tokens: int | None = 4000,
    llm_provider: str | None = None,
    stream: bool | None = False,
    websocket: Any | None = None,
    llm_kwargs: dict[str, Any] | None = None,
    cost_callback: Callable | None = None,
    reasoning_effort: ReasoningEfforts | None = None,
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
        **kwargs: Additional keyword arguments.

    Returns:
        str: The response from the chat completion
    """
    # validate input
    if model is None:
        raise ValueError("Model cannot be None")
    if max_tokens is not None and max_tokens > 32001:
        raise ValueError(f"Max tokens cannot be more than 16,000, but got {max_tokens}")

    # Get the provider from supported providers
    provider: GenericLLMProvider = get_llm(
        llm_provider,
        model=model,
        temperature=temperature,
        max_tokens=max_tokens,
        **(llm_kwargs or {}),
    )

    from gpt_researcher.llm_provider.generic.base import (
        NO_SUPPORT_TEMPERATURE_MODELS,
        SUPPORT_REASONING_EFFORT_MODELS,
    )

    if model in SUPPORT_REASONING_EFFORT_MODELS:
        kwargs["reasoning_effort"] = reasoning_effort

    if model not in NO_SUPPORT_TEMPERATURE_MODELS:
        kwargs["temperature"] = temperature
        kwargs["max_tokens"] = max_tokens
    else:
        if "temperature" in kwargs:
            del kwargs["temperature"]
        if "max_tokens" in kwargs:
            del kwargs["max_tokens"]

    if llm_provider == "openai":
        base_url: str | None = os.environ.get("OPENAI_BASE_URL", None)
        if base_url:
            kwargs["openai_api_base"] = base_url

    # Initialize provider and prepare for retries
    provider = get_llm(llm_provider, **kwargs)
    original_max_tokens: int | None = max_tokens
    MAX_ATTEMPTS: int = 3
    response: str = ""

    # Check token count and truncate if needed
    model_max_tokens: int = 16000  # Default max context length
    if "gpt-4" in model and "gpt-4.1" not in model:
        model_max_tokens = 8000 if "8k" in model else 16000
        if "32k" in model:
            model_max_tokens = 32000

    # Estimate token count of messages
    token_count: int = estimate_token_count(messages, model)

    # Reserve tokens for completion
    completion_tokens: int = max_tokens or 4000
    max_context_tokens: int = model_max_tokens - completion_tokens

    # If messages exceed context limit, truncate them
    if token_count > max_context_tokens:
        logging.warning(f"Messages exceed token limit ({token_count} > {max_context_tokens}), truncating content")
        messages = truncate_messages_to_fit(messages, max_context_tokens, model)

    # Attempt to get a response with fallback for token limits and transient errors
    for attempt in range(MAX_ATTEMPTS):
        try:
            response: str = await provider.get_chat_response(messages, stream, websocket)
            if cost_callback is not None:
                llm_costs: float = estimate_llm_cost(str(messages), response)
                cost_callback(llm_costs)
        except Exception as e:
            err_msg: str = str(e)
            # Fallback for max_tokens errors: remove max_tokens if that's the issue
            if "max_tokens" in err_msg.casefold() and (
                "too large" in err_msg.casefold()
                or "supports at most" in err_msg.casefold()
            ):
                logging.warning(f"max_tokens issue ({original_max_tokens}), retrying without max_tokens")
                if "max_tokens" in kwargs:
                    del kwargs["max_tokens"]
                provider: GenericLLMProvider = get_llm(llm_provider, **kwargs)
                continue
            if "'unrecognized request argument supplied: reasoning_effort'" in err_msg.casefold():
                logging.warning(f"reasoning_effort={reasoning_effort} not supported by this model, retrying without reasoning_effort")
                if "reasoning_effort" in kwargs:
                    del kwargs["reasoning_effort"]
                provider: GenericLLMProvider = get_llm(llm_provider, **kwargs)
                continue

            # Context length error: truncate messages further and retry
            if "context length" in err_msg.casefold() or "context_length_exceeded" in err_msg.casefold():
                logging.warning(f"Context length exceeded, further truncating messages")
                # Cut the context limit in half for more aggressive truncation
                messages = truncate_messages_to_fit(messages, max_context_tokens // 2, model)
                continue

            # Transient errors: retry with exponential backoff
            if attempt < MAX_ATTEMPTS - 1:
                backoff: int = 2**attempt
                logging.warning(f"Error calling LLM (attempt {attempt + 1}/{MAX_ATTEMPTS}): {e.__class__.__name__}: {e}, retrying in {backoff}s")
                await asyncio.sleep(backoff)
                continue
            logging.error(f"Failed to get response from '{llm_provider}' API after {MAX_ATTEMPTS} attempts: {e.__class__.__name__}: {e}")
            raise
        else:
            return response
    # If all retries fail, raise an error
    logging.error(f"All retries exhausted for '{llm_provider}' API")
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
            model=config.smart_llm_model,
            temperature=temperature,
            max_tokens=config.llm_kwargs.get("smart_token_limit", getattr(config, "smart_token_limit", 4000)),
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
        print(f"Exception in parsing subtopics: {e.__class__.__name__}: {e}")
        return subtopics
