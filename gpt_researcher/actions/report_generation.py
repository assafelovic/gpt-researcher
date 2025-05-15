from __future__ import annotations

from collections.abc import Callable
from typing import TYPE_CHECKING, Any

from ..config.config import Config
from ..prompts import PromptFamily, get_prompt_by_report_type
from ..utils.enum import Tone
from ..utils.llm import create_chat_completion
from ..utils.logger import get_formatted_logger

if TYPE_CHECKING:
    from fastapi import WebSocket

logger = get_formatted_logger()


async def write_report_introduction(
    query: str,
    context: str,
    agent_role_prompt: str,
    config: Config,
    websocket: WebSocket | None = None,
    cost_callback: Callable | None = None,
    prompt_family: type[PromptFamily] | PromptFamily = PromptFamily,
) -> str:
    """Generate an introduction for the report.

    Args:
        query (str): The research query.
        context (str): Context for the report.
        role (str): The role of the agent.
        config (Config): Configuration object.
        websocket: WebSocket connection for streaming output.
        cost_callback (callable, optional): Callback for calculating LLM costs.
        prompt_family: Family of prompts

    Returns:
        str: The generated introduction.
    """
    try:
        introduction: str = await create_chat_completion(
            model=config.smart_llm_model,
            messages=[
                {"role": "system", "content": f"{agent_role_prompt}"},
                {"role": "user", "content": prompt_family.generate_report_introduction(
                    question=query,
                    research_summary=context,
                    language=config.language
                )},
            ],
            temperature=0.25,
            llm_provider=config.smart_llm_provider,
            stream=True,
            websocket=websocket,
            max_tokens=config.smart_token_limit,
            llm_kwargs=config.llm_kwargs,
            cost_callback=cost_callback,
        )
        return introduction
    except Exception as e:
        logger.error(f"Error in generating report introduction: {e}")
    return ""


async def write_conclusion(
    query: str,
    context: str,
    agent_role_prompt: str,
    config: Config,
    websocket: WebSocket | None = None,
    cost_callback: Callable | None = None,
    prompt_family: type[PromptFamily] | PromptFamily = PromptFamily,
) -> str:
    """Write a conclusion for the report.

    Args:
        query (str): The research query.
        context (str): Context for the report.
        role (str): The role of the agent.
        config (Config): Configuration object.
        websocket: WebSocket connection for streaming output.
        cost_callback (callable, optional): Callback for calculating LLM costs.
        prompt_family: Family of prompts

    Returns:
        str: The generated conclusion.
    """
    try:
        conclusion: str = await create_chat_completion(
            model=config.smart_llm_model,
            messages=[
                {"role": "system", "content": f"{agent_role_prompt}"},
                {
                    "role": "user",
                    "content": prompt_family.generate_report_conclusion(
                        query=query,
                        report_content=context,
                        language=config.language
                    ),
                },
            ],
            temperature=0.25,
            llm_provider=config.smart_llm_provider,
            stream=True,
            websocket=websocket,
            max_tokens=config.smart_token_limit,
            llm_kwargs=config.llm_kwargs,
            cost_callback=cost_callback,
        )
        return conclusion
    except Exception as e:
        logger.error(f"Error in writing conclusion: {e}")
    return ""


async def summarize_url(
    url: str,
    content: str,
    role: str,
    config: Config,
    websocket: WebSocket | None = None,
    cost_callback: Callable | None = None,
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
            model=config.smart_llm_model,
            messages=[
                {"role": "system", "content": f"{role}"},
                {
                    "role": "user",
                    "content": f"Summarize the following content from {url}:\n\n{content}",
                },
            ],
            temperature=0.25,
            llm_provider=config.smart_llm_provider,
            stream=True,
            websocket=websocket,
            max_tokens=config.smart_token_limit,
            llm_kwargs=config.llm_kwargs,
            cost_callback=cost_callback,
        )
        return summary
    except Exception as e:
        logger.error(f"Error in summarizing URL: {e}")
    return ""


async def generate_draft_section_titles(
    query: str,
    current_subtopic: str,
    context: str,
    role: str,
    config: Config,
    websocket: WebSocket | None = None,
    cost_callback: Callable | None = None,
    prompt_family: type[PromptFamily] | PromptFamily = PromptFamily,
) -> list[str]:
    """Generate draft section titles for the report.

    Args:
        query (str): The research query.
        context (str): Context for the report.
        role (str): The role of the agent.
        config (Config): Configuration object.
        websocket: WebSocket connection for streaming output.
        cost_callback (callable, optional): Callback for calculating LLM costs.
        prompt_family: Family of prompts

    Returns:
        list[str]: A list of generated section titles.
    """
    try:
        section_titles: list[str] = await create_chat_completion(
            model=config.smart_llm_model,
            messages=[
                {"role": "system", "content": f"{role}"},
                {"role": "user", "content": prompt_family.generate_draft_titles_prompt(
                    current_subtopic, query, context)},
            ],
            temperature=0.25,
            llm_provider=config.smart_llm_provider,
            stream=True,
            websocket=None,
            max_tokens=config.smart_token_limit,
            llm_kwargs=config.llm_kwargs,
            cost_callback=cost_callback,
        )
        return str(section_titles).split("\n")
    except Exception as e:
        logger.error(f"Error in generating draft section titles: {e}")
    return []


async def generate_report(
    query: str,
    context: str,
    agent_role_prompt: str,
    report_type: str,
    tone: Tone,
    report_source: str,
    websocket: WebSocket,
    cfg: Config,
    main_topic: str = "",
    existing_headers: list[str] | None = None,
    relevant_written_contents: list[str] | None = None,
    cost_callback: Callable | None = None,
    headers: dict[str, str] | None = None,
    prompt_family: type[PromptFamily] | PromptFamily = PromptFamily,
    custom_prompt: str | None = None,
    **kwargs: dict[str, Any],
) -> str:
    """Generates the final report.

    Args:
        query: The research query.
        context: The context for the report.
        agent_role_prompt: The role of the agent.
        report_type: The type of report.
        tone: The tone of the report.
        report_source: The source of the report.
        websocket: The WebSocket connection for streaming output.
        cfg: The configuration object.
        main_topic: The main topic of the report.
        existing_headers: The existing headers of the report.
        relevant_written_contents: The relevant written contents of the report.
        cost_callback: The callback for calculating the cost of the report.
        prompt_family: The family of prompts.
        custom_prompt: A custom prompt for the report.
        **kwargs: Additional keyword arguments.

    Returns:
        report: The final report.
    """
    existing_headers = [] if existing_headers is None else existing_headers
    relevant_written_contents = [] if relevant_written_contents is None else relevant_written_contents
    generate_prompt: Any = get_prompt_by_report_type(
        report_type,
        prompt_family,
    )
    report: str = ""

    if report_type == "subtopic_report":
        content: str = f"{generate_prompt(query, existing_headers, relevant_written_contents, main_topic, context, report_format=cfg.report_format, tone=tone, total_words=cfg.total_words, language=cfg.language)}"
    else:
        content = f"{generate_prompt(query, context, report_source, report_format=cfg.report_format, tone=tone, total_words=cfg.total_words, language=cfg.language)}"
    try:
        report = await create_chat_completion(
            model=cfg.smart_llm_model,
            messages=[
                {"role": "system", "content": f"{agent_role_prompt}"},
                {"role": "user", "content": content},
            ],
            temperature=0.35,
            llm_provider=cfg.smart_llm_provider,
            stream=True,
            websocket=websocket,
            max_tokens=cfg.smart_token_limit,
            llm_kwargs=cfg.llm_kwargs,
            cost_callback=cost_callback,
        )
    except Exception:
        try:
            report = await create_chat_completion(
                model=cfg.smart_llm_model,
                messages=[
                    {
                        "role": "user",
                        "content": f"{agent_role_prompt}\n\n{content}",
                    },
                ],
                temperature=0.35,
                llm_provider=cfg.smart_llm_provider,
                stream=True,
                websocket=websocket,
                max_tokens=cfg.smart_token_limit,
                llm_kwargs=cfg.llm_kwargs,
                cost_callback=cost_callback,
            )
        except Exception as e:
            print(f"Error in generate_report: {e.__class__.__name__}: {e}")

    return report
