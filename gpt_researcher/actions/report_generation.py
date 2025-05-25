from __future__ import annotations

import traceback

from collections.abc import Callable
from typing import TYPE_CHECKING, Any

from gpt_researcher.config.config import Config
from gpt_researcher.prompts import PromptFamily, get_prompt_by_report_type
from gpt_researcher.utils.enum import Tone
from gpt_researcher.utils.llm import create_chat_completion
from gpt_researcher.utils.logger import get_formatted_logger

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
                {"role": "user", "content": prompt_family.generate_report_introduction(question=query, research_summary=context, language=config.language)},
            ],
            temperature=0.25,
            llm_provider=config.smart_llm_provider,
            stream=True,
            websocket=websocket,
            max_tokens=config.smart_token_limit,
            llm_kwargs=config.llm_kwargs,
            cost_callback=cost_callback,
            cfg=config,
        )
        return introduction
    except Exception as e:
        logger.error(f"Error in generating report introduction: {traceback.format_exc()}")
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
                    "content": prompt_family.generate_report_conclusion(query=query, report_content=context, language=config.language),
                },
            ],
            temperature=0.25,
            llm_provider=config.smart_llm_provider,
            stream=True,
            websocket=websocket,
            max_tokens=config.smart_token_limit,
            llm_kwargs=config.llm_kwargs,
            cost_callback=cost_callback,
            cfg=config,
        )
        return conclusion
    except Exception as e:
        logger.error(f"Error in writing conclusion: {traceback.format_exc()}")
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
            cfg=config,
        )
        return summary
    except Exception as e:
        logger.error(f"Error in summarizing URL: {traceback.format_exc()}")
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
                {"role": "user", "content": prompt_family.generate_draft_titles_prompt(current_subtopic, query, context)},
            ],
            temperature=0.25,
            llm_provider=config.smart_llm_provider,
            stream=True,
            websocket=None,
            max_tokens=config.smart_token_limit,
            llm_kwargs=config.llm_kwargs,
            cost_callback=cost_callback,
            cfg=config,
        )
        return str(section_titles).split("\n")
    except Exception:
        logger.error(f"Error in generating draft section titles: {traceback.format_exc()}")
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
    custom_prompt: str | None = None,
    headers: dict[str, str] | None = None,
    prompt_family: type[PromptFamily] | PromptFamily = PromptFamily,
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
        custom_prompt: A custom prompt for the report.
        headers: The headers of the report.
        prompt_family: The family of prompts.
        **kwargs: Additional keyword arguments.

    Returns:
        report: The final report.
    """
    # DEBUG: Log function start and params
    logger.info(f"[DEBUG] Starting generate_report for query: {query[:50]}...")
    logger.info(f"[DEBUG] Report type: {report_type}, context length: {len(str(context))}, has custom prompt: {custom_prompt is not None}")

    existing_headers = [] if existing_headers is None else existing_headers
    relevant_written_contents = [] if relevant_written_contents is None else relevant_written_contents
    generate_prompt: Any = get_prompt_by_report_type(
        report_type,
        prompt_family,
    )
    report: str = ""
    generated_prompt: str = ""

    try:
        # DEBUG: Log prompt generation
        logger.info(f"[DEBUG] Generating prompt with report_type: {report_type}")

        if report_type == "subtopic_report":
            generated_prompt = generate_prompt(
                query,
                existing_headers,
                relevant_written_contents,
                main_topic,
                context,
                report_format=cfg.report_format,  # pyright: ignore[reportAttributeAccessIssue]
                tone=tone,
                total_words=cfg.total_words,  # pyright: ignore[reportAttributeAccessIssue]
                language=cfg.language,  # pyright: ignore[reportAttributeAccessIssue]
            )
        else:
            generated_prompt = generate_prompt(
                query,
                context,
                report_source,
                report_format=cfg.report_format,  # pyright: ignore[reportAttributeAccessIssue]
                tone=tone,
                total_words=cfg.total_words,  # pyright: ignore[reportAttributeAccessIssue]
                language=cfg.language,  # pyright: ignore[reportAttributeAccessIssue]
            )

        # DEBUG: Log prompt generation success and length
        logger.info(f"[DEBUG] Generated prompt successfully, length: {len(generated_prompt)}")
        logger.info(f"[DEBUG] Prompt starts with: {generated_prompt[:100]}...")

    except Exception as e:
        logger.error(f"[DEBUG] Error generating prompt: {e.__class__.__name__}: {e}")
        logger.error(f"[DEBUG] Traceback: {traceback.format_exc()}")
        # Default empty prompt in case of error
        generated_prompt = f"Please generate a report about {query} based on the provided context."

    content: str = f"{generated_prompt}"

    # DEBUG: Log message structure before API call
    messages: list[dict[str, str]] = [
        {"role": "system", "content": f"{agent_role_prompt or ''} "},
        {"role": "user", "content": content},
    ]
    logger.info(f"[DEBUG] Preparing to call LLM with model: {cfg.smart_llm_model}, provider: {cfg.smart_llm_provider}")
    logger.info(f"[DEBUG] System message length: {len(agent_role_prompt or '')}")
    logger.info(f"[DEBUG] User message length: {len(content)}")

    try:
        logger.info("[DEBUG] Making first create_chat_completion attempt")
        report = await create_chat_completion(
            model=cfg.smart_llm_model,
            messages=messages,
            temperature=0.35,
            llm_provider=cfg.smart_llm_provider,
            stream=True,
            websocket=websocket,
            max_tokens=cfg.smart_token_limit,
            llm_kwargs=cfg.llm_kwargs,
            cost_callback=cost_callback,
            cfg=cfg,
        )
        # DEBUG: Log successful completion
        logger.info(f"[DEBUG] First attempt successful, report length: {len(report)}")
        logger.info(f"[DEBUG] Report starts with: {report[:100]}...")

        # DEBUG: Check for problematic responses
        if "I'm sorry, but I cannot provide a response to this task" in report:
            logger.warning("[DEBUG] Detected error pattern in report response")
            logger.warning(f"[DEBUG] Full response: {report}")

    except Exception as e:
        logger.error(f"[DEBUG] First attempt failed: {e.__class__.__name__}: {e}")
        logger.error(f"[DEBUG] Traceback: {traceback.format_exc()}")
        try:
            # Try with a simplified approach by combining system and user messages
            logger.info("[DEBUG] Making fallback create_chat_completion attempt")
            simplified_messages: list[dict[str, str]] = [
                {
                    "role": "user",
                    "content": f"{agent_role_prompt or ''}\n\n{content}",
                },
            ]
            logger.info(f"[DEBUG] Simplified message length: {len(simplified_messages[0]['content'])}")

            report = await create_chat_completion(
                model=cfg.smart_llm_model,
                messages=simplified_messages,
                temperature=0.35,
                llm_provider=cfg.smart_llm_provider,
                stream=True,
                websocket=websocket,
                max_tokens=cfg.smart_token_limit,
                llm_kwargs=cfg.llm_kwargs,
                cost_callback=cost_callback,
                cfg=cfg,
            )
            # DEBUG: Log successful fallback completion
            logger.info(f"[DEBUG] Fallback attempt successful, report length: {len(report)}")
            logger.info(f"[DEBUG] Report starts with: {report[:100]}...")

            # DEBUG: Check for problematic responses in fallback
            if "I'm sorry, but I cannot provide a response to this task" in report:
                logger.warning("[DEBUG] Detected error pattern in fallback report response")
                logger.warning(f"[DEBUG] Full fallback response: {report}")

        except Exception as e2:
            print(f"Error in generate_report fallback: {e2.__class__.__name__}: {e2}")
            logger.error(f"[DEBUG] Fallback attempt also failed: {e2.__class__.__name__}: {e2}")
            logger.error(f"[DEBUG] Fallback traceback: {traceback.format_exc()}")

    # DEBUG: Log function end
    logger.info(f"[DEBUG] Finished generate_report, returning report of length: {len(report)}")
    return report
