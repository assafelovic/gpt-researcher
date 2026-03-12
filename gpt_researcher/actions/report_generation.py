import asyncio
import logging
from typing import List, Dict, Any
from ..config.config import Config
from ..utils.llm import create_chat_completion
from ..utils.logger import get_formatted_logger
from ..prompts import PromptFamily, get_prompt_by_report_type
from ..utils.enum import Tone

logger = get_formatted_logger()
_retry_logger = logging.getLogger(__name__)


def _is_rate_limit_error(exc: Exception) -> bool:
    """Check if an exception is a rate limit (429) error."""
    msg = str(exc).lower()
    return "429" in msg or "rate limit" in msg or "rate_limit" in msg


def _is_token_limit_error(exc: Exception) -> bool:
    """Check if an exception is a token/context length error."""
    msg = str(exc).lower()
    return any(term in msg for term in (
        "maximum context length",
        "max_tokens",
        "context_length_exceeded",
        "token limit",
        "too many tokens",
        "request too large",
    ))


async def write_report_introduction(
    query: str,
    context: str,
    agent_role_prompt: str,
    config: Config,
    websocket=None,
    cost_callback: callable = None,
    prompt_family: type[PromptFamily] | PromptFamily = PromptFamily,
    **kwargs
) -> str:
    """
    Generate an introduction for the report.

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
        introduction = await create_chat_completion(
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
            **kwargs
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
    websocket=None,
    cost_callback: callable = None,
    prompt_family: type[PromptFamily] | PromptFamily = PromptFamily,
    **kwargs
) -> str:
    """
    Write a conclusion for the report.

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
        conclusion = await create_chat_completion(
            model=config.smart_llm_model,
            messages=[
                {"role": "system", "content": f"{agent_role_prompt}"},
                {
                    "role": "user",
                    "content": prompt_family.generate_report_conclusion(query=query,
                                                                        report_content=context,
                                                                        language=config.language),
                },
            ],
            temperature=0.25,
            llm_provider=config.smart_llm_provider,
            stream=True,
            websocket=websocket,
            max_tokens=config.smart_token_limit,
            llm_kwargs=config.llm_kwargs,
            cost_callback=cost_callback,
            **kwargs
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
    websocket=None,
    cost_callback: callable = None,
    **kwargs
) -> str:
    """
    Summarize the content of a URL.

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
        summary = await create_chat_completion(
            model=config.smart_llm_model,
            messages=[
                {"role": "system", "content": f"{role}"},
                {"role": "user", "content": f"Summarize the following content from {url}:\n\n{content}"},
            ],
            temperature=0.25,
            llm_provider=config.smart_llm_provider,
            stream=True,
            websocket=websocket,
            max_tokens=config.smart_token_limit,
            llm_kwargs=config.llm_kwargs,
            cost_callback=cost_callback,
            **kwargs
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
    websocket=None,
    cost_callback: callable = None,
    prompt_family: type[PromptFamily] | PromptFamily = PromptFamily,
    **kwargs
) -> List[str]:
    """
    Generate draft section titles for the report.

    Args:
        query (str): The research query.
        context (str): Context for the report.
        role (str): The role of the agent.
        config (Config): Configuration object.
        websocket: WebSocket connection for streaming output.
        cost_callback (callable, optional): Callback for calculating LLM costs.
        prompt_family: Family of prompts

    Returns:
        List[str]: A list of generated section titles.
    """
    try:
        section_titles = await create_chat_completion(
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
            **kwargs
        )
        return section_titles.split("\n")
    except Exception as e:
        logger.error(f"Error in generating draft section titles: {e}")
    return []


async def _attempt_report_generation(
    messages: list,
    cfg,
    websocket,
    cost_callback: callable = None,
    llm_provider: str = None,
    llm_model: str = None,
    **kwargs
) -> str:
    """Single attempt at report generation with given model.

    Args:
        messages: Chat messages to send.
        cfg: Configuration object.
        websocket: WebSocket for streaming.
        cost_callback: Cost tracking callback.
        llm_provider: Override LLM provider (for fallback).
        llm_model: Override LLM model (for fallback).

    Returns:
        Generated report string.
    """
    return await create_chat_completion(
        model=llm_model or cfg.smart_llm_model,
        messages=messages,
        temperature=0.35,
        llm_provider=llm_provider or cfg.smart_llm_provider,
        stream=True,
        websocket=websocket,
        max_tokens=cfg.smart_token_limit,
        llm_kwargs=cfg.llm_kwargs,
        cost_callback=cost_callback,
        **kwargs
    )


async def _generate_chunked_report(
    query: str,
    context: str,
    agent_role_prompt: str,
    cfg,
    websocket,
    cost_callback: callable = None,
    llm_provider: str = None,
    llm_model: str = None,
    **kwargs
) -> str:
    """Generate report by chunking context when it exceeds model limits.

    Splits context into chunks, generates partial reports for each, then
    synthesizes a final report from the partials.

    Args:
        query: Research query.
        context: Full research context (too large for single call).
        agent_role_prompt: Agent role system prompt.
        cfg: Configuration object.
        websocket: WebSocket for streaming.
        cost_callback: Cost tracking callback.
        llm_provider: Override LLM provider.
        llm_model: Override LLM model.

    Returns:
        Synthesized report string.
    """
    provider = llm_provider or cfg.smart_llm_provider
    model = llm_model or cfg.smart_llm_model

    # Split context into roughly equal chunks (aim for ~4000 words each)
    words = context.split()
    chunk_size = 4000
    chunks = [
        " ".join(words[i:i + chunk_size])
        for i in range(0, len(words), chunk_size)
    ]

    _retry_logger.info(f"Chunking context into {len(chunks)} parts for report generation")

    partial_reports = []
    for i, chunk in enumerate(chunks):
        _retry_logger.info(f"Generating partial report {i+1}/{len(chunks)}")
        partial = await create_chat_completion(
            model=model,
            messages=[
                {"role": "system", "content": agent_role_prompt},
                {"role": "user", "content": (
                    f"You are writing part {i+1} of {len(chunks)} of a research report on: {query}\n\n"
                    f"Write a detailed section based on this research context:\n\n{chunk}\n\n"
                    f"Focus on key findings and insights. Use markdown formatting."
                )},
            ],
            temperature=0.35,
            llm_provider=provider,
            stream=False,
            websocket=None,
            max_tokens=cfg.smart_token_limit,
            llm_kwargs=cfg.llm_kwargs,
            cost_callback=cost_callback,
            **kwargs
        )
        if partial:
            partial_reports.append(partial)

    if not partial_reports:
        return ""

    # Synthesize final report from partials
    combined = "\n\n---\n\n".join(partial_reports)
    _retry_logger.info("Synthesizing final report from partial sections")

    final_report = await create_chat_completion(
        model=model,
        messages=[
            {"role": "system", "content": agent_role_prompt},
            {"role": "user", "content": (
                f"Synthesize the following partial research sections into a single cohesive "
                f"research report on: {query}\n\n"
                f"Remove redundancy, unify the structure with proper headings, and ensure "
                f"smooth transitions. Preserve all citations and key findings.\n\n"
                f"Partial sections:\n\n{combined}"
            )},
        ],
        temperature=0.35,
        llm_provider=provider,
        stream=True,
        websocket=websocket,
        max_tokens=cfg.smart_token_limit,
        llm_kwargs=cfg.llm_kwargs,
        cost_callback=cost_callback,
        **kwargs
    )
    return final_report or ""


async def generate_report(
    query: str,
    context,
    agent_role_prompt: str,
    report_type: str,
    tone: Tone,
    report_source: str,
    websocket,
    cfg,
    main_topic: str = "",
    existing_headers: list = [],
    relevant_written_contents: list = [],
    cost_callback: callable = None,
    custom_prompt: str = "",
    headers=None,
    prompt_family: type[PromptFamily] | PromptFamily = PromptFamily,
    available_images: list = None,
    **kwargs
):
    """Generate the final report with retry, chunking, and model fallback.

    Resilience layers (in order):
    1. Standard generation attempt
    2. Retry with exponential backoff on 429 rate limit errors
    3. Context chunking fallback on token limit errors
    4. Fallback model (SMART_LLM_FALLBACK) if primary model exhausts retries

    Args:
        query: Research query.
        context: Research context.
        agent_role_prompt: Agent role system prompt.
        report_type: Type of report to generate.
        tone: Report tone.
        report_source: Source of report data.
        websocket: WebSocket for streaming.
        cfg: Configuration object.
        main_topic: Main topic for subtopic reports.
        existing_headers: Headers already written.
        relevant_written_contents: Previously written content.
        cost_callback: Cost tracking callback.
        custom_prompt: Custom user prompt.
        headers: Additional headers.
        prompt_family: Prompt family to use.
        available_images: Pre-generated images to embed.

    Returns:
        Generated report string.

    Raises:
        Exception: Re-raises the last exception if all attempts fail, so
            callers (like the checkpoint system) can detect and handle failure.
    """
    available_images = available_images or []
    generate_prompt = get_prompt_by_report_type(report_type, prompt_family)
    report = ""

    if report_type == "subtopic_report":
        content = f"{generate_prompt(query, existing_headers, relevant_written_contents, main_topic, context, report_format=cfg.report_format, tone=tone, total_words=cfg.total_words, language=cfg.language)}"
    elif custom_prompt:
        content = f"{custom_prompt}\n\nContext: {context}"
    else:
        content = f"{generate_prompt(query, context, report_source, report_format=cfg.report_format, tone=tone, total_words=cfg.total_words, language=cfg.language)}"

    # Add available images instruction if images were pre-generated
    if available_images:
        images_info = "\n".join([
            f"- Image {i+1}: ![{img.get('title', img.get('alt_text', 'Illustration'))}]({img['url']}) - {img.get('section_hint', 'General')}"
            for i, img in enumerate(available_images)
        ])
        content += f"""

AVAILABLE IMAGES:
You have the following pre-generated images available. Embed them in relevant sections of your report using the exact markdown syntax provided:

{images_info}

Place each image on its own line after the relevant section header or paragraph. Use all available images where they add value to the content."""

    messages = [
        {"role": "system", "content": f"{agent_role_prompt}"},
        {"role": "user", "content": content},
    ]

    # Fallback messages (single user message if system message causes issues)
    fallback_messages = [
        {"role": "user", "content": f"{agent_role_prompt}\n\n{content}"},
    ]

    max_retries = getattr(cfg, 'report_generation_retries', 3)
    backoff_delays = [30, 60, 120]  # seconds
    last_error = None

    # --- Primary model attempts ---
    for attempt in range(max_retries):
        try:
            report = await _attempt_report_generation(
                messages=messages, cfg=cfg, websocket=websocket,
                cost_callback=cost_callback, **kwargs
            )
            if report:
                return report

            # Try fallback message format
            report = await _attempt_report_generation(
                messages=fallback_messages, cfg=cfg, websocket=websocket,
                cost_callback=cost_callback, **kwargs
            )
            if report:
                return report

        except Exception as e:
            last_error = e

            if _is_token_limit_error(e):
                _retry_logger.warning(f"Token limit exceeded, attempting chunked generation: {e}")
                try:
                    report = await _generate_chunked_report(
                        query=query, context=str(context),
                        agent_role_prompt=agent_role_prompt,
                        cfg=cfg, websocket=websocket,
                        cost_callback=cost_callback, **kwargs
                    )
                    if report:
                        return report
                except Exception as chunk_err:
                    _retry_logger.error(f"Chunked generation also failed: {chunk_err}")
                    last_error = chunk_err
                break  # Don't retry token errors with same model

            if _is_rate_limit_error(e) and attempt < max_retries - 1:
                delay = backoff_delays[min(attempt, len(backoff_delays) - 1)]
                _retry_logger.warning(
                    f"Rate limited (attempt {attempt+1}/{max_retries}), "
                    f"retrying in {delay}s: {e}"
                )
                await asyncio.sleep(delay)
                continue

            _retry_logger.error(f"Report generation attempt {attempt+1} failed: {e}")
            if attempt < max_retries - 1:
                await asyncio.sleep(5)

    # --- Fallback model attempts ---
    fallback_provider = getattr(cfg, 'smart_llm_fallback_provider', None)
    fallback_model = getattr(cfg, 'smart_llm_fallback_model', None)

    if fallback_provider and fallback_model:
        _retry_logger.info(f"Trying fallback model: {fallback_provider}:{fallback_model}")

        for attempt in range(2):  # 2 attempts with fallback
            try:
                report = await _attempt_report_generation(
                    messages=messages, cfg=cfg, websocket=websocket,
                    cost_callback=cost_callback,
                    llm_provider=fallback_provider,
                    llm_model=fallback_model, **kwargs
                )
                if report:
                    _retry_logger.info("Report generated successfully with fallback model")
                    return report
            except Exception as e:
                last_error = e
                if _is_token_limit_error(e):
                    _retry_logger.warning("Token limit on fallback model, trying chunked")
                    try:
                        report = await _generate_chunked_report(
                            query=query, context=str(context),
                            agent_role_prompt=agent_role_prompt,
                            cfg=cfg, websocket=websocket,
                            cost_callback=cost_callback,
                            llm_provider=fallback_provider,
                            llm_model=fallback_model, **kwargs
                        )
                        if report:
                            return report
                    except Exception as chunk_err:
                        last_error = chunk_err
                    break

                if _is_rate_limit_error(e) and attempt == 0:
                    _retry_logger.warning("Rate limited on fallback, retrying in 30s")
                    await asyncio.sleep(30)
                    continue

                _retry_logger.error(f"Fallback model attempt {attempt+1} failed: {e}")

    # All attempts exhausted — raise so checkpoint system can catch it
    if last_error:
        _retry_logger.error(f"All report generation attempts failed. Last error: {last_error}")
        raise last_error

    return report
