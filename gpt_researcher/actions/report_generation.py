from __future__ import annotations

from typing import TYPE_CHECKING, Any

from gpt_researcher.config.config import Config
from gpt_researcher.llm_provider.generic.base import GenericLLMProvider
from gpt_researcher.prompts import (
    generate_draft_titles_prompt,
    generate_report_conclusion,
    generate_report_introduction,
    get_prompt_by_report_type,
)
from gpt_researcher.utils.enum import ReportType
from gpt_researcher.utils.llm import create_chat_completion
from gpt_researcher.utils.logger import get_formatted_logger

if TYPE_CHECKING:
    from collections.abc import Callable
    from logging import Logger

    from backend.server.server_utils import CustomLogsHandler
    from fastapi.websockets import WebSocket

    from gpt_researcher.utils.enum import Tone

logger: Logger = get_formatted_logger()


def _get_llm(
    cfg: Config,
    model: str | None = None,
    temperature: float | None = None,
) -> GenericLLMProvider:
    """Get an LLM provider instance with optional overrides.

    Args:
    ----
        cfg: The config object
        model: Optional model override
        temperature: Optional temperature override

    Returns:
    -------
        The LLM provider instance
    """
    return GenericLLMProvider(
        cfg.STRATEGIC_LLM if model is None else f"{cfg.STRATEGIC_LLM_PROVIDER}:{model}",
        temperature=temperature or cfg.SMART_LLM_TEMPERATURE,
        fallback_models=cfg.FALLBACK_MODELS,
        **cfg.llm_kwargs,
    )


async def write_report_introduction(
    query: str,
    context: str,
    agent_role_prompt: str,
    config: Config,
    websocket: CustomLogsHandler | WebSocket | None = None,
    cost_callback: Callable[[float], None] | None = None,
) -> str:
    """Generate an introduction for the report.

    Args:
        query (str): The research query.
        context (str): Context for the report.
        role (str): The role of the agent.
        config (Config): Configuration object.
        websocket: WebSocket connection for streaming output.
        cost_callback (callable, optional): Callback for calculating LLM costs.

    Returns:
        str: The generated introduction.
    """
    try:
        introduction: str = await create_chat_completion(
            model=config.SMART_LLM_MODEL,
            messages=[
                {"role": "system", "content": f"{agent_role_prompt}"},
                {"role": "user", "content": generate_report_introduction(query, context, config.LANGUAGE)},
            ],
            temperature=0.25,
            llm_provider=config.SMART_LLM_PROVIDER,
            stream=True,
            websocket=websocket,
            max_tokens=config.SMART_TOKEN_LIMIT,
            llm_kwargs=config.llm_kwargs,
            cost_callback=cost_callback,
        )

    except Exception as e:
        logger.exception(f"Error in generating report introduction: {e.__class__.__name__}: {e}")

    else:
        return introduction
    return ""


async def write_conclusion(
    query: str,
    context: str,
    agent_role_prompt: str,
    config: Config,
    websocket: CustomLogsHandler | WebSocket | None = None,
    cost_callback: Callable[[float], None] | None = None,
) -> str:
    """Write a conclusion for the report.

    Args:
    ----
        query (str): The research query.
        context (str): Context for the report.
        role (str): The role of the agent.
        config (Config): Configuration object.
        websocket: WebSocket connection for streaming output.
        cost_callback (callable, optional): Callback for calculating LLM costs.

    Returns:
    -------
        str: The generated conclusion.
    """
    try:
        conclusion: str = await create_chat_completion(
            model=config.SMART_LLM_MODEL,
            messages=[
                {"role": "system", "content": f"{agent_role_prompt}"},
                {"role": "user", "content": generate_report_conclusion(query, context, config.LANGUAGE)},
            ],
            temperature=0.25,
            llm_provider=config.SMART_LLM_PROVIDER,
            stream=True,
            websocket=websocket,
            max_tokens=config.SMART_TOKEN_LIMIT,
            llm_kwargs=config.llm_kwargs,
            cost_callback=cost_callback,
        )
        return conclusion
    except Exception as e:
        logger.exception(f"Error in writing conclusion! {e.__class__.__name__}: {e}")
    return ""


async def summarize_url(
    url: str,
    content: str,
    role: str,
    config: Config,
    websocket: WebSocket | None = None,
    cost_callback: Callable[[float], None] | None = None,
) -> str:
    """Summarize the content of a URL.

    Args:
        url (str): The URL to summarize.
        content (str): The content of the URL.
        role (str): The role of the agent.
        config (Config): Configuration object.
        websocket: WebSocket connection for streaming output.
        cost_callback (callable, optional): Callback for calculating LLM costs.

    Returns:
        str: The summarized content.
    """
    try:
        summary: str = await create_chat_completion(
            messages=[
                {"role": "system", "content": f"{role}"},
                {"role": "user", "content": f"Summarize the following content from {url}:\n\n{content}"},
            ],
            temperature=0.25,
            llm_provider=config.STRATEGIC_LLM,
            stream=True,
            websocket=websocket,
            max_tokens=config.SMART_TOKEN_LIMIT,
            llm_kwargs=config.llm_kwargs,
            cost_callback=cost_callback,
        )
        return summary
    except Exception as e:
        logger.exception(f"Error in summarizing URL: {e.__class__.__name__}: {e}")
    return ""


async def generate_draft_section_titles(
    query: str,
    current_subtopic: str,
    context: str,
    role: str,
    config: Config,
    websocket: CustomLogsHandler | WebSocket | None = None,
    cost_callback: Callable[[float], None] | None = None,
) -> list[str]:
    """Generate draft section titles for the report.

    Args:
        query (str): The research query.
        context (str): Context for the report.
        role (str): The role of the agent.
        config (Config): Configuration object.
        websocket: WebSocket connection for streaming output.
        cost_callback (callable, optional): Callback for calculating LLM costs.

    Returns:
        list[str]: A list of generated section titles.
    """
    try:
        section_titles: str = await create_chat_completion(
            model=config.SMART_LLM_MODEL,
            messages=[
                {"role": "system", "content": f"{role}"},
                {"role": "user", "content": generate_draft_titles_prompt(current_subtopic, query, context)},
            ],
            temperature=0.25,
            llm_provider=config.SMART_LLM_PROVIDER,
            stream=True,
            websocket=None,  # FIXME: should send websocket?
            max_tokens=config.SMART_TOKEN_LIMIT,
            llm_kwargs=config.llm_kwargs,
            cost_callback=cost_callback,
        )

        if cost_callback is not None:
            from gpt_researcher.utils.costs import estimate_llm_cost

            llm_costs: float = estimate_llm_cost(
                generate_draft_titles_prompt(current_subtopic, query, context),
                section_titles,
            )
            cost_callback(llm_costs)
    except Exception as e:
        logger.exception(f"Error in generating draft section titles! {e.__class__.__name__}: {e}")
    else:
        return section_titles.split("\n")
    return []


async def generate_report(
    query: str,
    context: Any,
    agent_role_prompt: str,
    report_type: ReportType,
    tone: Tone,
    report_source: str,
    websocket: WebSocket | None = None,
    cfg: Config | None = None,
    main_topic: str = "",
    existing_headers: list[str] | None = None,
    relevant_written_contents: list[str] | None = None,
    cost_callback: Callable[[float], None] | None = None,
    headers: list[str] | None = None,
) -> str:
    """Generates the final report.

    Args:
    ----
        query (str):
        context (Any):
        agent_role_prompt (str):
        report_type (ReportType):
        websocket (WebSocket | None):
        tone (Tone):
        cfg (Config):
        main_topic (str):
        existing_headers (list[str] | None):
        relevant_written_contents (list[str] | None):
        cost_callback (Callable[[float], None] | None): Callback for calculating LLM costs.

    Returns:
    -------
        report (str): The final report

    """
    cfg = Config() if cfg is None else cfg
    existing_headers = [] if existing_headers is None else existing_headers
    relevant_written_contents = [] if relevant_written_contents is None else relevant_written_contents
    headers = [] if headers is None else headers

    generate_prompt: Callable[..., str] = get_prompt_by_report_type(report_type)
    report: str = ""

    if report_type == ReportType.SubtopicReport:
        content: str = generate_prompt(
            query,
            existing_headers,
            relevant_written_contents,
            main_topic,
            context,
            report_format=cfg.REPORT_FORMAT,
            tone=tone,
            total_words=cfg.TOTAL_WORDS,
            language=cfg.LANGUAGE,
        )
    else:
        content = generate_prompt(
            query,
            context,
            report_source,
            report_format=cfg.REPORT_FORMAT,
            tone=tone,
            total_words=cfg.TOTAL_WORDS,
            language=cfg.LANGUAGE,
        )

    try:
        # Get LLM parameters with error handling for max_tokens
        report = await create_chat_completion(
            model=cfg.SMART_LLM_MODEL,
            messages=[
                {"role": "system", "content": f"{agent_role_prompt}\n\n{content}"},
            ],
            temperature=0.35,
            llm_provider=cfg.SMART_LLM_PROVIDER,
            stream=True,
            websocket=websocket,
            max_tokens=cfg.SMART_TOKEN_LIMIT,
            llm_kwargs=cfg.llm_kwargs,
            cost_callback=cost_callback,
        )

    except BaseException as first_error:
        logger.warning(f"Error in generate_report: {first_error.__class__.__name__}: {first_error}", exc_info=True)

        try:
            report = await create_chat_completion(
                model=cfg.SMART_LLM_MODEL,
                messages=[
                    {"role": "user", "content": f"{agent_role_prompt}\n\n{content}"},
                ],
                temperature=0.35,
                llm_provider=cfg.SMART_LLM_PROVIDER,
                stream=True,
                websocket=websocket,
                max_tokens=cfg.SMART_TOKEN_LIMIT,
                llm_kwargs=cfg.llm_kwargs,
                cost_callback=cost_callback,
            )
        except BaseException as second_error:
            logger.exception(
                f"Error in generate_report fallback: {second_error.__class__.__name__}: {second_error}. Additionally, an attempt to output the existing content failed."  # noqa: E501
            )
            report = content

    return report
