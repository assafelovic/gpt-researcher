# libraries
from __future__ import annotations

import logging

from typing import TYPE_CHECKING, Any, Callable

from langchain.output_parsers import PydanticOutputParser
from langchain.prompts import PromptTemplate
from langchain_core.language_models.chat_models import BaseChatModel
from llm_provider.generic.base import GenericLLMProvider  # noqa: F811

from gpt_researcher.prompts import generate_subtopics_prompt
from gpt_researcher.utils.costs import estimate_llm_cost
from gpt_researcher.utils.schemas import Subtopics
from gpt_researcher.utils.validators import Subtopics

if TYPE_CHECKING:
    from gpt_researcher.config import Config
    from gpt_researcher.llm_provider.generic.base import GenericLLMProvider

logger: logging.Logger = logging.getLogger(__name__)


def get_llm(
    llm_provider: str,
    **kwargs,
) -> GenericLLMProvider:
    from gpt_researcher.llm_provider import GenericLLMProvider

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
    reasoning_effort: str | None = "low",
    max_retries: int | None = 10,
    headers: dict[str, str] | None = None,
) -> str:
    """Create a chat completion using the OpenAI API
    Args:
        messages (list[dict[str, str]]): The messages to send to the chat completion
        model (str | None): The model to use. Defaults to None.
        temperature (float | None): The temperature to use. Defaults to 0.4.
        max_tokens (int | None): The max tokens to use. Defaults to 4000.
        stream (bool | None): Whether to stream the response. Defaults to False.
        llm_provider (str | None): The LLM Provider to use.
        webocket (WebSocket): The websocket used in the currect request,
        cost_callback (Callable | None): Callback function for updating cost
        headers (dict[str, str] | None): The headers to use. Defaults to None.
    Returns:
        str: The response from the chat completion
    """
    # validate input
    if model is None:
        raise ValueError("Model cannot be None")
    if max_tokens is not None and max_tokens > 16001:
        raise ValueError(f"Max tokens cannot be more than 16,000, but got {max_tokens}")
    if llm_provider is None:
        raise ValueError("LLM provider cannot be None")

    headers = {} if headers is None else headers

    # Get the provider from supported providers
    model = model.casefold()
    kwargs: dict[str, Any] = {
        "model": model,
        **(llm_kwargs or {}),
    }

    if "o3" in model or "o1" in model:
        print(f"Using reasoning model '{model}'")
        kwargs["reasoning_effort"] = reasoning_effort
    else:
        print(f"Using non-reasoning model '{model}'")
        kwargs["temperature"] = temperature
        kwargs["max_tokens"] = max_tokens

    print(f"\n🤖 Calling {llm_provider} with model '{model}'...\n")
    provider: GenericLLMProvider = get_llm(llm_provider, **kwargs)
    response: str = ""
    # create response
    for _ in range(10):  # maximum of 10 attempts
        response = await provider.get_chat_response(
            messages,
            stream=bool(stream),
            websocket=websocket,
            max_retries=max_retries or 10,
            headers=headers,
        )

        if cost_callback is not None:
            llm_costs: float = estimate_llm_cost(
                str(messages),
                response,
            )
            cost_callback(llm_costs)

        return response

    logger.error(f"Failed to get response from provider '{llm_provider}'")
    raise RuntimeError(f"Failed to get response from provider '{llm_provider}'")


async def construct_subtopics(
    task: str,
    data: str,
    config: Config,
    subtopics: list[str] | None = None,
    headers: dict[str, str] | None = None,
) -> list[str] | Subtopics:
    """Construct subtopics based on the given task and data.

    Args:
        task (str): The main task or topic.
        data (str): Additional data for context.
        config: Configuration settings.
        subtopics (list, optional): Existing subtopics. Defaults to empty list.
        headers (dict[str, str] | None): The headers to use, if any.
    Returns:
        list: A list of constructed subtopics.
    """
    subtopics = [] if subtopics is None else subtopics
    headers = {} if headers is None else headers
    try:
        parser = PydanticOutputParser(pydantic_object=Subtopics)

        prompt = PromptTemplate(
            template=generate_subtopics_prompt(),
            input_variables=[
                "task",
                "data",
                "subtopics",
                "max_subtopics",
            ],
            partial_variables={"format_instructions": parser.get_format_instructions()},
        )

        logger.debug(f"\n🤖 Calling {config.SMART_LLM_MODEL}...\n")

        temperature: float = config.TEMPERATURE
        assert config.SMART_LLM_PROVIDER is not None
        provider: GenericLLMProvider = GenericLLMProvider.from_provider(
            config.SMART_LLM_PROVIDER,
            model=config.SMART_LLM_MODEL,
            temperature=temperature,
            **config.llm_kwargs,
            headers=headers,
        )
        model: BaseChatModel = provider.llm
        chain = prompt | model | parser
        output: Subtopics = await chain.ainvoke(
            {
                "task": task,
                "data": data,
                "max_subtopics": config.MAX_SUBTOPICS,
                "subtopics": subtopics,
            },
            headers=headers,
        )

        return output

    except Exception as e:
        logger.exception(f"Exception in parsing subtopics: {e.__class__.__name__}: {e}")
        return subtopics
