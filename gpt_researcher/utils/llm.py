# libraries
from __future__ import annotations

import asyncio
import logging
import os
import re
import time
import traceback
from collections.abc import Callable
from typing import TYPE_CHECKING, Any

import tiktoken
from langchain.llms.base import BaseLLM
from langchain.output_parsers import PydanticOutputParser
from langchain.prompts import PromptTemplate

from gpt_researcher.config.config import Config
from gpt_researcher.llm_provider.generic.base import (
    SUPPORT_REASONING_EFFORT_MODELS,
    GenericLLMProvider,
    ReasoningEfforts,
)
from gpt_researcher.prompts import PromptFamily
from gpt_researcher.utils.costs import estimate_llm_cost
from gpt_researcher.utils.llm_debug_logger import LLMDebugLogger, get_llm_debug_logger
from gpt_researcher.utils.validators import Subtopics

if TYPE_CHECKING:
    from gpt_researcher.skills.llm_visualizer import LLMInteractionVisualizer


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
                logger.warning(f"Primary provider {llm_provider} failed: {e.__class__.__name__}: {e}. Using first fallback as primary.")
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
    # Import visualization here to avoid circular imports
    from gpt_researcher.skills.llm_visualizer import get_llm_visualizer

    # validate input
    if model is None:
        raise ValueError("Model cannot be None")

    # Initialize debug logger
    debug_logger: LLMDebugLogger = get_llm_debug_logger()
    interaction_id: str | None = None

    try:
        # Extract message content for logging
        system_message: str = ""
        user_message: str = ""
        for msg in messages:
            role: str = msg.get("role", "").lower()
            content: str = str(msg.get("content", ""))
            if role == "system":
                system_message += content + "\n"
            elif role in ["user", "human"]:
                user_message += content + "\n"

        system_message = system_message.strip()
        user_message = user_message.strip()

        # Start debug logging
        interaction_id = debug_logger.start_interaction(
            step_name=kwargs.get("step_name", "LLM Chat Completion"),
            model=model,
            provider=llm_provider or "unknown",
            is_fallback=False,
            fallback_attempt=0,
            context_info={
                "stream": stream,
                "reasoning_effort": str(reasoning_effort) if reasoning_effort else None,
                "llm_kwargs": llm_kwargs or {}
            }
        )
        debug_logger.log_request(
            system_message=system_message,
            user_message=user_message,
            full_messages=messages,
            temperature=temperature,
            max_tokens=max_tokens,
            **kwargs
        )

        # DEBUG: Log function entry with basic info
        logger.info(f"[DEBUG-LLM] create_chat_completion called with model={model}, provider={llm_provider}, max_tokens={max_tokens}")
        logger.info(f"[DEBUG-LLM] Number of messages: {len(messages)}")

        # Check if visualization is active for report generation
        visualizer: LLMInteractionVisualizer = get_llm_visualizer()
        is_visualizing: bool = visualizer.is_enabled() and visualizer.is_active()

        # Prepare visualization data
        interaction_data: dict[str, Any] | None = None
        if is_visualizing:
            # Prepare interaction data for logging
            interaction_data = {
                "step_name": kwargs.get("step_name", "LLM Interaction"),
                "model": model,
                "provider": llm_provider or "unknown",
                "prompt_type": "chat_completion",
                "system_message": system_message,
                "user_message": user_message,
                "full_messages": messages.copy(),
                "temperature": temperature or 0.0,
                "max_tokens": max_tokens,
            }

        # Dynamic context limit determination
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

        # DEBUG: Check what type of provider we got
        logger.error(f"[DEBUG-PROVIDER] Provider type: {type(provider)}")
        logger.error(f"[DEBUG-PROVIDER] Provider class name: {provider.__class__.__name__}")
        logger.error(f"[DEBUG-PROVIDER] Provider module: {provider.__class__.__module__}")

        # Try to get context limits from provider if supported
        default_context_limit: int | None = getattr(provider.llm, "context_length", None)
        if default_context_limit is None:
            # If not available, derive from config or use dynamic estimation
            if model == config_obj.fast_llm_model:
                default_context_limit = getattr(config_obj, "fast_llm_context_length", 4096)
            elif model == config_obj.smart_llm_model:
                default_context_limit = getattr(config_obj, "smart_llm_context_length", 8192)
            elif model == config_obj.strategic_llm_model:
                default_context_limit = getattr(config_obj, "strategic_llm_context_length", 16385)

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

        logger.debug(f"[DEBUG-LLM] Estimated model context limit: {default_context_limit}")

        from gpt_researcher.llm_provider.generic.base import (
            NO_SUPPORT_TEMPERATURE_MODELS,
            SUPPORT_REASONING_EFFORT_MODELS,
        )

        # Update kwargs based on model capabilities
        if model in SUPPORT_REASONING_EFFORT_MODELS:
            kwargs["reasoning_effort"] = reasoning_effort
            logger.debug(f"[DEBUG-LLM] Added `reasoning_effort={reasoning_effort}` to kwargs")

        if model not in NO_SUPPORT_TEMPERATURE_MODELS:
            if temperature is not None:
                kwargs["temperature"] = temperature
            if max_tokens is not None:
                kwargs["max_tokens"] = max_tokens
        else:
            if "temperature" in kwargs:
                del kwargs["temperature"]
                logger.debug("[DEBUG-LLM] Removed `temperature` from kwargs")
            if "max_tokens" in kwargs:
                del kwargs["max_tokens"]
                logger.debug("[DEBUG-LLM] Removed `max_tokens` from kwargs")

        if llm_provider == "openai":
            base_url: str | None = os.environ.get("OPENAI_BASE_URL", None)
            if base_url and base_url.strip():
                kwargs["openai_api_base"] = base_url

        MAX_ATTEMPTS: int = getattr(config_obj, "llm_retry_attempts", 3)
        retry_attempt: int = 0
        last_error: Exception | None = None

        start_time: float = time.time()

        # Check if this is a fallback provider - if so, let it handle all retries internally
        from gpt_researcher.llm_provider.generic.fallback import (
            FallbackGenericLLMProvider,
        )
        is_fallback_provider: bool = isinstance(provider, FallbackGenericLLMProvider)

        if is_fallback_provider:
            # For fallback providers, make a single call and let them handle all retry logic
            logger.info("[DEBUG-LLM] Using FallbackGenericLLMProvider - delegating all retry logic to fallback provider")
            try:
                response: str = await provider.get_chat_response(messages, stream, websocket)

                try:
                    validated_response: str = validate_llm_response(response, f"LLM call to {llm_provider}:{model}")
                    response = validated_response
                except ValueError as validation_error:
                    logger.error(f"[DEBUG-LLM] Response validation failed: {validation_error}")
                    raise validation_error

                if cost_callback is not None:
                    llm_costs: float = estimate_llm_cost(str(messages), response)
                    cost_callback(llm_costs)

                duration: float = time.time() - start_time
                debug_logger.log_response(
                    response=response,
                    success=True,
                    duration_seconds=duration
                )

                if is_visualizing and interaction_data:
                    interaction_data["response"] = response
                    interaction_data["success"] = True
                    interaction_data["retry_attempt"] = 0
                    visualizer.log_interaction(**interaction_data)

                logger.info("[DEBUG-LLM] Successfully returning response from FallbackGenericLLMProvider")
                return response

            except Exception as e:
                duration: float = time.time() - start_time
                debug_logger.log_response(
                    response="",
                    success=False,
                    error_message=str(e),
                    error_type=type(e).__name__,
                    duration_seconds=duration
                )

                if is_visualizing and interaction_data:
                    interaction_data["response"] = ""
                    interaction_data["success"] = False
                    interaction_data["error"] = str(e)
                    interaction_data["retry_attempt"] = 0
                    visualizer.log_interaction(**interaction_data)

                logger.error(f"[DEBUG-LLM] FallbackGenericLLMProvider exhausted all options: {type(e).__name__}: {str(e)}")
                raise e

        # For non-fallback providers, use the original retry logic
        for attempt in range(MAX_ATTEMPTS):
            try:
                if attempt > 0:
                    debug_logger.log_retry_attempt(
                        attempt_number=attempt + 1,
                        reason=f"Previous attempt failed: {str(last_error) if 'last_error' in locals() else 'Unknown error'}",
                        details={"max_attempts": MAX_ATTEMPTS}
                    )

                response: str = await provider.get_chat_response(messages, stream, websocket)

                try:
                    validated_response: str = validate_llm_response(response, f"LLM call to {llm_provider}:{model}")
                    response = validated_response
                except ValueError as validation_error:
                    logger.error(f"[DEBUG-LLM] Response validation failed: {validation_error}")
                    raise validation_error

                if cost_callback is not None:
                    llm_costs: float = estimate_llm_cost(str(messages), response)
                    cost_callback(llm_costs)

                duration: float = time.time() - start_time
                debug_logger.log_response(
                    response=response,
                    success=True,
                    duration_seconds=duration
                )

                if is_visualizing and interaction_data:
                    interaction_data["response"] = response
                    interaction_data["success"] = True
                    interaction_data["retry_attempt"] = retry_attempt
                    visualizer.log_interaction(**interaction_data)

                logger.info(f"[DEBUG-LLM] Successfully returning response from attempt {attempt+1}")
                return response

            except Exception as e:
                last_error = e
                retry_attempt = attempt + 1
                logger.error(f"[DEBUG-LLM] Error in attempt {attempt+1}: {type(e).__name__}: {str(e)[:300]}...")

                if attempt < MAX_ATTEMPTS - 1:
                    transient_patterns: list[str] = [
                        "rate limit",
                        "timeout",
                        "connection",
                        "network",
                        "temporary",
                        "service unavailable",
                        "internal server error",
                    ]
                    is_transient: bool = any(pattern in str(e).lower() for pattern in transient_patterns)
                    if is_transient:
                        backoff: int = 2**attempt
                        logger.warning(f"[DEBUG-LLM] Transient error detected, retrying in {backoff}s...")
                        await asyncio.sleep(backoff)
                        continue
                    else:
                        logger.error("[DEBUG-LLM] Non-transient error, not retrying at this level.")
                        break
                else:
                    logger.error("[DEBUG-LLM] All attempts exhausted for create_chat_completion")
                    break

        duration: float = time.time() - start_time
        debug_logger.log_response(
            response="",
            success=False,
            error_message=str(last_error) if last_error else "Unknown error",
            error_type=type(last_error).__name__ if last_error else "UnknownError",
            duration_seconds=duration
        )

        if is_visualizing and interaction_data:
            interaction_data["response"] = ""
            interaction_data["success"] = False
            interaction_data["error"] = str(last_error) if last_error else "Unknown error"
            interaction_data["retry_attempt"] = retry_attempt
            visualizer.log_interaction(**interaction_data)

        if last_error is not None:
            raise last_error
        raise RuntimeError(f"Unexpected end of retry loop for '{llm_provider}' API")

    finally:
        if interaction_id and interaction_id.strip():
            debug_logger.finish_interaction()


import logging
import traceback

async def construct_subtopics(
    task: str,
    data: str,
    config,
    subtopics: list = None,
    prompt_family: type[PromptFamily] | PromptFamily = PromptFamily,
    **kwargs
) -> list:
    """
    Construct subtopics based on the given task and data.

    Args:
        task (str): The main task or topic.
        data (str): Additional data for context.
        config: Configuration settings.
        subtopics (list, optional): Existing subtopics. Defaults to [].
        prompt_family (PromptFamily): Family of prompts
        **kwargs: Additional keyword arguments.

    Returns:
        list: A list of constructed subtopics.
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

        provider_kwargs = {"model": config.smart_llm_model}
        if config.llm_kwargs:
            provider_kwargs.update(config.llm_kwargs)

        if config.smart_llm_model in SUPPORT_REASONING_EFFORT_MODELS:
            provider_kwargs["reasoning_effort"] = ReasoningEfforts.High.value
        else:
            provider_kwargs["temperature"] = config.temperature
            provider_kwargs["max_tokens"] = config.smart_token_limit

        provider: GenericLLMProvider = get_llm(
            config.smart_llm_provider,
            cfg=config,
            model=config.smart_llm_model,
            temperature=temperature,
            **config.llm_kwargs,
        )

        model: BaseLLM = provider.llm
        chain = prompt | model | parser

        # Flexible handling of max_subtopics (kwargs > llm_kwargs > config)
        max_subtopics = (
            kwargs.get("max_subtopics")
            or config.llm_kwargs.get("max_subtopics")
            or getattr(config, "max_subtopics", 5)
        )

        output = await chain.ainvoke(
            {
                "task": task,
                "data": data,
                "subtopics": subtopics,
                "max_subtopics": max_subtopics,
            },
            **kwargs,
        )

        return output

    except Exception as e:
        print(f"Exception in parsing subtopics: {e}")
        logging.getLogger(__name__).error(
            f"Exception in parsing subtopics:\n{traceback.format_exc()}"
        )
        return subtopics



def validate_llm_response(
    response: str,
    operation: str = "LLM operation",
) -> str:
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
