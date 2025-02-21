from __future__ import annotations

import logging

from typing import TYPE_CHECKING, Any, Callable

import json_repair

from gpt_researcher.llm_provider.generic.base import GenericLLMProvider
from gpt_researcher.prompts import generate_search_queries_prompt
from gpt_researcher.utils.llm import create_chat_completion
from gpt_researcher.utils.enum import ReportType

if TYPE_CHECKING:
    from json_repair.json_parser import JSONReturnType

    from gpt_researcher.config import Config


def _get_llm(
    cfg: Config,
    model: str | None = None,
    temperature: float | None = None,
    max_tokens: int | None = None,
) -> GenericLLMProvider:
    """Get an LLM provider instance with optional overrides.

    Args:
        cfg: The config object
        model: Optional model override
        temperature: Optional temperature override
        max_tokens: Optional max_tokens override

    Returns:
        The LLM provider instance
    """
    return GenericLLMProvider.from_provider(
        cfg.STRATEGIC_LLM_PROVIDER if model == cfg.STRATEGIC_LLM_MODEL else cfg.SMART_LLM_PROVIDER,
        model=model or cfg.SMART_LLM_MODEL,
        temperature=temperature or cfg.TEMPERATURE,
        max_tokens=max_tokens,
        **cfg.llm_kwargs,
    )


logger: logging.Logger = logging.getLogger(__name__)


async def get_search_results(
    query: str,
    retriever: Any,
    query_domains: list[str] | None = None,
) -> list[dict[str, Any]]:
    """
    Get web search results for a given query.

    Args:
        query: The search query
        retriever: The retriever instance

    Returns:
        A list of search results
    """
    search_retriever = retriever(query, query_domains=query_domains)
    return search_retriever.search()


async def generate_sub_queries(
    query: str,
    parent_query: str,
    report_type: str | ReportType,
    context: list[dict[str, Any]],
    cfg: Config,
    cost_callback: Callable[[float], None] | None = None,
) -> list[str]:
    """
    Generate sub-queries using the specified LLM model.

    Args:
        query: The original query
        parent_query: The parent query
        report_type (str | ReportType): The type of report
        max_iterations: Maximum number of research iterations
        context: Search results context
        cfg: Configuration object
        cost_callback: Callback for cost calculation

    Returns:
        A list of sub-queries
    """
    gen_queries_prompt: str = generate_search_queries_prompt(
        query,
        parent_query,
        report_type,
        max_iterations=cfg.MAX_ITERATIONS or 3,
        context=context,
    )

    try:
        response = await create_chat_completion(
            model=cfg.STRATEGIC_LLM,
            messages=[{"role": "user", "content": gen_queries_prompt}],
            temperature=1,
            llm_provider=cfg.STRATEGIC_LLM_PROVIDER,
            max_tokens=None,
            llm_kwargs=cfg.llm_kwargs,
            reasoning_effort="high",
            cost_callback=cost_callback,
        )
    except Exception as e:
        logger.warning(f"Error with strategic LLM: {e}. Retrying with max_tokens={cfg.STRATEGIC_TOKEN_LIMIT}.")
        logger.warning("See https://github.com/assafelovic/gpt-researcher/issues/1022")
        try:
            response = await create_chat_completion(
                model=cfg.STRATEGIC_LLM,
                messages=[{"role": "user", "content": gen_queries_prompt}],
                temperature=1,
                llm_provider=cfg.STRATEGIC_LLM_PROVIDER,
                max_tokens=cfg.STRATEGIC_TOKEN_LIMIT,
                llm_kwargs=cfg.llm_kwargs,
                cost_callback=cost_callback,
            )
            logger.warning(f"Retrying with max_tokens={cfg.STRATEGIC_TOKEN_LIMIT} successful.")
        except Exception as e:
            logger.warning(f"Retrying with max_tokens={cfg.STRATEGIC_TOKEN_LIMIT} failed.")
            logger.warning(f"Error with strategic LLM: {e}. Falling back to smart LLM.")
            response = await create_chat_completion(
                model=cfg.SMART_LLM,
                messages=[
                    {
                        "role": "user",
                        "content": gen_queries_prompt,
                    },
                ],
                temperature=cfg.TEMPERATURE,
                max_tokens=cfg.SMART_TOKEN_LIMIT,
                llm_provider=cfg.SMART_LLM_PROVIDER,
                llm_kwargs=cfg.llm_kwargs,
                cost_callback=cost_callback,
            )

    result: JSONReturnType | tuple[JSONReturnType, list[dict[str, str]]] = json_repair.loads(response)
    assert isinstance(result, list), f"Expected list, got {result.__class__.__name__}"

    return result


async def plan_research_outline(
    query: str,
    search_results: list[dict[str, Any]],
    agent_role_prompt: str,
    cfg: Config,
    parent_query: str,
    report_type: str | ReportType,
    cost_callback: Callable[[float], None] | None = None,
) -> list[str]:
    """
    Plan the research outline by generating sub-queries.

    Args:
        query (str): Original query
        retriever (list[dict[str, Any]]): Retriever instance
        agent_role_prompt (str): Agent role prompt
        cfg (Config): Configuration object
        parent_query (str): Parent query
        report_type (str): Report type
        cost_callback (Callable[[float], None] | None): Callback for cost calculation

    Returns:
        A list of sub-queries
    """

    sub_queries: list[str] = await generate_sub_queries(
        query,
        parent_query,
        report_type,
        search_results,
        cfg,
        cost_callback,
    )

    return sub_queries
