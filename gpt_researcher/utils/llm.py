# libraries
from __future__ import annotations

import logging
from typing import Any

from langchain_core.output_parsers import PydanticOutputParser
from langchain_core.prompts import PromptTemplate

from gpt_researcher.llm_provider.generic.base import NO_SUPPORT_TEMPERATURE_MODELS, SUPPORT_REASONING_EFFORT_MODELS, ReasoningEfforts

from ..prompts import PromptFamily
from .costs import estimate_llm_cost, calculate_llm_cost
from .validators import Subtopics
import os


def get_llm(llm_provider, **kwargs):
    from gpt_researcher.llm_provider import GenericLLMProvider
    return GenericLLMProvider.from_provider(llm_provider, **kwargs)


async def create_chat_completion(
        messages: list[dict[str, str]],
        model: str | None = None,
        temperature: float | None = 0.4,
        max_tokens: int | None = 4000,
        llm_provider: str | None = None,
        stream: bool = False,
        websocket: Any | None = None,
        llm_kwargs: dict[str, Any] | None = None,
        cost_callback: callable = None,
        reasoning_effort: str | None = ReasoningEfforts.Medium.value,
        **kwargs
) -> str:
    """Create a chat completion using the OpenAI API
    Args:
        messages (list[dict[str, str]]): The messages to send to the chat completion.
        model (str, optional): The model to use. Defaults to None.
        temperature (float, optional): The temperature to use. Defaults to 0.4.
        max_tokens (int, optional): The max tokens to use. Defaults to 4000.
        llm_provider (str, optional): The LLM Provider to use.
        stream (bool): Whether to stream the response. Defaults to False.
        webocket (WebSocket): The websocket used in the currect request,
        llm_kwargs (dict[str, Any], optional): Additional LLM keyword arguments. Defaults to None.
        cost_callback: Callback function for updating cost.
        reasoning_effort (str, optional): Reasoning effort for OpenAI's reasoning models. Defaults to 'low'.
        **kwargs: Additional keyword arguments.
    Returns:
        str: The response from the chat completion.
    """
    # validate input
    if model is None:
        raise ValueError("Model cannot be None")
    if max_tokens is not None and max_tokens > 32001:
        raise ValueError(
            f"Max tokens cannot be more than 32,000, but got {max_tokens}")

    # Get the provider from supported providers
    provider_kwargs = {'model': model}

    if llm_kwargs:
        provider_kwargs.update(llm_kwargs)

    if model in SUPPORT_REASONING_EFFORT_MODELS:
        provider_kwargs['reasoning_effort'] = reasoning_effort

    if model not in NO_SUPPORT_TEMPERATURE_MODELS:
        provider_kwargs['temperature'] = temperature
        provider_kwargs['max_tokens'] = max_tokens
    else:
        provider_kwargs['temperature'] = None
        provider_kwargs['max_tokens'] = None

    if llm_provider == "openai":
        base_url = os.environ.get("OPENAI_BASE_URL", None)
        if base_url:
            provider_kwargs['openai_api_base'] = base_url

    provider = get_llm(llm_provider, **provider_kwargs)
    response = ""
    # create response
    for _ in range(10):  # maximum of 10 attempts
        response = await provider.get_chat_response(
            messages, stream, websocket, **kwargs
        )

        if cost_callback:
            # Prefer provider-reported usage when available (more accurate than estimation)
            usage = getattr(provider, "last_usage", None)
            if isinstance(usage, dict) and isinstance(usage.get("prompt_tokens"), int) and isinstance(usage.get("completion_tokens"), int):
                llm_costs = calculate_llm_cost(
                    prompt_tokens=int(usage["prompt_tokens"]),
                    completion_tokens=int(usage["completion_tokens"]),
                    model=model,
                )
                token_usage = {
                    "prompt_tokens": int(usage["prompt_tokens"]),
                    "completion_tokens": int(usage["completion_tokens"]),
                    "total_tokens": int(usage.get("total_tokens", int(usage["prompt_tokens"]) + int(usage["completion_tokens"]))),
                }
            else:
                llm_costs = estimate_llm_cost(str(messages), response, model=model)
                from .costs import estimate_token_usage
                token_usage = estimate_token_usage(str(messages), response, model=model)

            # Sanity check: if provider usage looks implausibly small vs text estimation, prefer estimation
            # (some streaming providers expose partial/delta usage metadata).
            try:
                from .costs import estimate_token_usage
                est = estimate_token_usage(str(messages), response, model=model)
                
                provider_completion = token_usage.get("completion_tokens", 0)
                est_completion = est.get("completion_tokens", 0)
                
                # If estimate is significantly larger than provider usage, trust estimate.
                if (
                    isinstance(provider_completion, int)
                    and isinstance(est_completion, int)
                    and est_completion > provider_completion * 1.25
                ):
                    logging.getLogger(__name__).warning(
                        f"Token usage mismatch (provider vs estimate). "
                        f"provider={token_usage} estimate={est} model={model}. Using estimate."
                    )
                    token_usage = est
                    llm_costs = calculate_llm_cost(
                        prompt_tokens=int(token_usage["prompt_tokens"]),
                        completion_tokens=int(token_usage["completion_tokens"]),
                        model=model,
                    )
            except Exception as e:
                logging.getLogger(__name__).warning(f"Error validating token usage: {e}")

            # Track cost and token usage
            try:
                if cost_callback:
                    # Try passing both cost and token_usage
                    cost_callback(llm_costs, token_usage=token_usage)
            except TypeError:
                # Fallback for callbacks that don't support token_usage arg
                if cost_callback:
                    cost_callback(llm_costs)
            except Exception as e:
                logging.getLogger(__name__).warning(f"Error in cost_callback: {e}")

            # Log usage
            logging.getLogger("research").info(
                f"LLM Call Usage: model={model} "
                f"prompt={token_usage.get('prompt_tokens', 0)} "
                f"completion={token_usage.get('completion_tokens', 0)} "
                f"total={token_usage.get('total_tokens', 0)}"
            )

        return response

    logging.error(f"Failed to get response from {llm_provider} API")
    raise RuntimeError(f"Failed to get response from {llm_provider} API")


async def construct_subtopics(
    task: str,
    data: str,
    config,
    subtopics: list = [],
    cost_callback: callable | None = None,
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
    try:
        parser = PydanticOutputParser(pydantic_object=Subtopics)

        prompt = PromptTemplate(
            template=prompt_family.generate_subtopics_prompt(),
            input_variables=["task", "data", "subtopics", "max_subtopics"],
            partial_variables={
                "format_instructions": parser.get_format_instructions()},
        )

        rendered = prompt.format(
            task=task,
            data=data,
            subtopics=subtopics,
            max_subtopics=config.max_subtopics,
        )

        # Use the unified create_chat_completion path so token/cost accounting is consistent.
        response = await create_chat_completion(
            messages=[{"role": "user", "content": rendered}],
            model=config.smart_llm_model,
            llm_provider=config.smart_llm_provider,
            llm_kwargs=getattr(config, "llm_kwargs", None),
            max_tokens=config.smart_token_limit,
            temperature=getattr(config, "temperature", 0.4),
            reasoning_effort=ReasoningEfforts.High.value if config.smart_llm_model in SUPPORT_REASONING_EFFORT_MODELS else ReasoningEfforts.Medium.value,
            cost_callback=cost_callback,
            **kwargs,
        )

        return parser.parse(response)

    except Exception as e:
        print("Exception in parsing subtopics : ", e)
        logging.getLogger(__name__).error("Exception in parsing subtopics : \n {e}")
        return subtopics
