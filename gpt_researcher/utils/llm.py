from __future__ import annotations

import logging
import os

from typing import TYPE_CHECKING, Any, Callable

from langchain.output_parsers import PydanticOutputParser
from langchain.prompts import PromptTemplate
from langchain_core.language_models.chat_models import BaseChatModel
from langchain_core.messages import BaseMessage
from litellm.utils import get_max_tokens

from gpt_researcher.llm_provider.generic.base import GenericLLMProvider  # noqa: F811
from gpt_researcher.utils.costs import estimate_llm_cost
from gpt_researcher.utils.validators import Subtopics

if TYPE_CHECKING:
    from gpt_researcher.config import Config
    from gpt_researcher.llm_provider.generic.base import GenericLLMProvider

logger: logging.Logger = logging.getLogger(__name__)


def get_llm_params(
    model: str | None,
    temperature: float = 0.35,
    include_max_tokens: bool = True,
) -> dict[str, Any]:
    """Get LLM parameters for the given model.

    Args:
        model (str): The model name.
        temperature (float): The temperature for the model.
        include_max_tokens (bool): Whether to include max tokens.

    Returns:
        dict[str, Any]: A dictionary of LLM parameters.
    """
    params: dict[str, Any] = {
        "model": model,
        "temperature": temperature,
    }
    if model and include_max_tokens:
        try:
            max_tokens = get_max_tokens(model)
            params["max_tokens"] = max_tokens
        except Exception as e:
            logger.error(f"Error in get_max_tokens: {e.__class__.__name__}: {e}")
    return params


def get_llm(
    llm_provider: str,
    **kwargs,
) -> GenericLLMProvider:
    from gpt_researcher.llm_provider import GenericLLMProvider
    # Use the new from_provider method if available, otherwise fallback to the constructor
    if hasattr(GenericLLMProvider, "from_provider"):
        return GenericLLMProvider(llm_provider, **kwargs)
    return GenericLLMProvider(llm_provider, **kwargs)


async def create_chat_completion(
    messages: list[BaseMessage] | list[dict[str, str]],
    model: str | None = None,
    temperature: float | None = 0.4,
    max_tokens: int | None = 16384,
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
        messages (list[BaseMessage | dict[str, str]]): The messages to send to the chat completion
        model (str | None): The model to use. Defaults to None.
        temperature (float | None): The temperature to use. Defaults to 0.4.
        max_tokens (int | None): The max tokens to use. Defaults to 16384.
        llm_provider (str | None): The LLM Provider to use.
        stream (bool | None): Whether to stream the response. Defaults to False.
        websocket (Any | None): The websocket used in the current request.
        llm_kwargs (dict[str, Any] | None): Additional LLM keyword arguments.
        cost_callback (Callable | None): Callback function for updating cost.
        reasoning_effort (str | None): Reasoning effort for models. Defaults to "low".
        max_retries (int | None): Maximum number of retries. Defaults to 10.
        headers (dict[str, str] | None): The headers to use. Defaults to None.

    Returns:
        str: The response from the chat completion.
    """
    # validate input
    if model is None:
        raise ValueError("Model cannot be None")
    if llm_provider is None:
        raise ValueError("LLM provider cannot be None")

    headers = {} if headers is None else headers

    # Get the provider from supported providers
    model = model.casefold()
    kwargs: dict[str, Any] = {
        "model": model,
        **(llm_kwargs or {}),
    }

    if "o3-" in model or "o1-" in model:
        print(f"Using reasoning model '{model}'")
        kwargs["reasoning_effort"] = reasoning_effort
    else:
        print(f"Using non-reasoning model '{model}'")
        kwargs["temperature"] = temperature
        kwargs["max_tokens"] = max_tokens

    # Merge incoming change: handle OpenAI base URL if provided
    if llm_provider == "openai":
        base_url = os.environ.get("OPENAI_BASE_URL", None)
        if base_url:
            kwargs["openai_api_base"] = base_url

    print(f"\n🤖 Calling {llm_provider} with model '{model}'...\n")
    provider: GenericLLMProvider = get_llm(llm_provider, **kwargs)
    response: str = ""
    # create response
    for _ in range(10):  # maximum of 10 attempts
        response = await provider.get_chat_response(
            messages=messages,  # type: ignore[arg-type]
            stream=bool(stream),
            websocket=websocket,
            max_retries=max_retries or 10,
            headers=headers,
        )

        if cost_callback is not None:
            llm_costs: float = estimate_llm_cost(
                provider.msgs_to_str(messages),
                response,
            )
            cost_callback(llm_costs)

        return response.encode().decode("utf-8")

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
        list[str] | Subtopics: A list of constructed subtopics.
    """
    subtopics = [] if subtopics is None else subtopics
    headers = {} if headers is None else headers
    try:
        parser = PydanticOutputParser(pydantic_object=Subtopics)

        prompt = PromptTemplate(
            template="""
Provided the main topic:

{task}

Providerarch data:

{data}

- Construct a list of subtopics which indicate the headers of a report document to be generated on the task.
- These are a possible list of subtopics: {subtopics}.
- There should NOT be any duplicate subtopics.
- Limit the number of subtopics to a maximum of {max_subtopics}
- Finally order the subtopics by their tasks, in a relevant and meaningful order which is presentable in a detailed report

"IMPORTANT!":
- Every subtopic MUST be relevant to the main topic and task and provided research data ONLY!
- Consider what subtopics will likely dive into the proper rabbitholes that would uncover the most relevant information.

{format_instructions}
""",
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
        provider: GenericLLMProvider = get_llm(
            config.SMART_LLM_PROVIDER,
            model=config.SMART_LLM_MODEL,
            temperature=temperature,
            fallback_models=config.FALLBACK_MODELS,
            **config.llm_kwargs,
            headers=headers,
        )
        model: BaseChatModel = provider.current_model
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
