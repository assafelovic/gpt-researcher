# libraries
from __future__ import annotations

import logging
from typing import TYPE_CHECKING, Any, Callable

from langchain.output_parsers import PydanticOutputParser
from langchain.prompts import PromptTemplate

from gpt_researcher.prompts import generate_subtopics_prompt
from gpt_researcher.utils.costs import estimate_llm_cost
from gpt_researcher.utils.schemas import Subtopics
from gpt_researcher.llm_provider.generic.base import GenericLLMProvider

if TYPE_CHECKING:
    from gpt_researcher.config import Config
    from gpt_researcher.llm_provider.generic.base import GenericLLMProvider

logger = logging.getLogger(__name__)


def get_llm(
    llm_provider: str,
    **kwargs,
) -> GenericLLMProvider:
    from gpt_researcher.llm_provider import GenericLLMProvider

    return GenericLLMProvider.from_provider(llm_provider, **kwargs)


async def create_chat_completion(
    messages: list,  # type: ignore
    model: str | None = None,
    temperature: float | None = 0.4,
    max_tokens: int | None = 16000,
    llm_provider: str | None = None,
    stream: bool | None = False,
    websocket: Any | None = None,
    llm_kwargs: dict[str, Any] | None = None,
    cost_callback: Callable[[Any], None] | None = None,
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

    Returns:
        str: The response from the chat completion.
    """
    # validate input
    if model is None:
        raise ValueError("Model cannot be None")
    if max_tokens is not None and max_tokens > 16001:
        raise ValueError(f"Max tokens cannot be more than 16,000, but got {max_tokens}")

    # Get the provider from supported providers
    assert llm_provider is not None
    provider: GenericLLMProvider = get_llm(
        llm_provider,
        model=model,
        temperature=temperature,
        max_tokens=max_tokens,
        **(llm_kwargs or {}),
    )

    response = ""
    # create response
    response: str = await provider.get_chat_response(
        messages,
        bool(stream),
        websocket,
    )

    if cost_callback:
        llm_costs: float = estimate_llm_cost(
            str(messages),
            response,
        )
        cost_callback(llm_costs)

    return response

    logger.error(f"Failed to get response from {llm_provider} API")
    raise RuntimeError(f"Failed to get response from {llm_provider} API")


async def construct_subtopics(
    task: str,
    data: str,
    config: Config,
    subtopics: list[str] | None = None,
) -> list[str] | Subtopics:
    """Construct subtopics based on the given task and data.

    Args:
        task (str): The main task or topic.
        data (str): Additional data for context.
        config: Configuration settings.
        subtopics (list, optional): Existing subtopics. Defaults to [].

    Returns:
        list: A list of constructed subtopics.
    """
    subtopics = [] if subtopics is None else subtopics
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

        temperature = config.TEMPERATURE
        assert config.SMART_LLM_PROVIDER is not None
        provider = GenericLLMProvider.from_provider(
            config.SMART_LLM_PROVIDER,
            model=config.SMART_LLM_MODEL,
            temperature=temperature,
            **config.llm_kwargs,
        )
        model = provider.llm
        chain = prompt | model | parser
        output: Subtopics = await chain.ainvoke(
            {
                "task": task,
                "data": data,
                "subtopics": subtopics,
                "max_subtopics": config.MAX_SUBTOPICS,
            }
        )

        return output

    except Exception as e:
        logger.exception(f"Exception in parsing subtopics : {e.__class__.__name__}: {e}")
        return subtopics
