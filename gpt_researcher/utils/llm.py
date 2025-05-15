# libraries
from __future__ import annotations

import asyncio
import logging
import os
from collections.abc import Callable
from typing import TYPE_CHECKING, Any

from langchain.llms.base import BaseLLM
from langchain.output_parsers import PydanticOutputParser
from langchain.prompts import PromptTemplate

from gpt_researcher.config.config import Config

from ..prompts import PromptFamily
from .costs import estimate_llm_cost
from .validators import Subtopics

if TYPE_CHECKING:
    from gpt_researcher.llm_provider.generic.base import (
        GenericLLMProvider,
        ReasoningEfforts,
    )


def get_llm(llm_provider: str, **kwargs) -> GenericLLMProvider:
    from gpt_researcher.llm_provider.generic.base import GenericLLMProvider

    return GenericLLMProvider.from_provider(llm_provider, **kwargs)


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
        kwargs["temperature"] = None
        kwargs["max_tokens"] = None

    if llm_provider == "openai":
        base_url: str | None = os.environ.get("OPENAI_BASE_URL", None)
        if base_url:
            kwargs["openai_api_base"] = base_url

    # Initialize provider and prepare for retries
    provider = get_llm(llm_provider, **kwargs)
    original_max_tokens: int | None = max_tokens
    MAX_ATTEMPTS: int = 3
    response: str = ""
    # Attempt to get a response with fallback for token limits and transient errors
    for attempt in range(MAX_ATTEMPTS):
        try:
            response: str = await provider.get_chat_response(
                messages, stream, websocket
            )
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
                logging.warning(
                    f"max_tokens issue ({original_max_tokens}), retrying without max_tokens"
                )
                kwargs["max_tokens"] = None
                provider: GenericLLMProvider = get_llm(llm_provider, **kwargs)
                continue
            # Transient errors: retry with exponential backoff
            if attempt < MAX_ATTEMPTS - 1:
                backoff: int = 2**attempt
                logging.warning(
                    f"Error calling LLM (attempt {attempt + 1}/{MAX_ATTEMPTS}): {e.__class__.__name__}: {e}, retrying in {backoff}s"
                )
                await asyncio.sleep(backoff)
                continue
            logging.error(
                f"Failed to get response from '{llm_provider}' API after {MAX_ATTEMPTS} attempts: {e.__class__.__name__}: {e}"
            )
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

        temperature: float = config.temperature
        # temperature = 0 # Note: temperature throughout the code base is currently set to Zero
        provider     = get_llm(
            config.smart_llm_provider,
            model=config.smart_llm_model,
            temperature=temperature,
            max_tokens=config.smart_token_limit,
            **config.llm_kwargs,
        )
        model: BaseLLM = provider.llm

        chain = prompt | model | parser

        output: list[str] = chain.invoke(
            {
                "task": task,
                "data": data,
                "subtopics": subtopics,
                "max_subtopics": config.max_subtopics,
            }
        )

        return output

    except Exception as e:
        print("Exception in parsing subtopics : ", e)
        return subtopics
