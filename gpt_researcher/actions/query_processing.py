from __future__ import annotations

import logging

from typing import Any, Callable

import json_repair

from ..config import Config
from ..llm_provider.generic.base import ReasoningEfforts
from ..prompts import PromptFamily
from ..utils.llm import create_chat_completion

logger = logging.getLogger(__name__)


async def get_search_results(query: str, retriever: Any) -> list[dict[str, Any]]:
    """Get web search results for a given query.

    Args:
        query: The search query
        retriever: The retriever instance

    Returns:
        A list of search results
    """
    search_retriever = retriever(query)
    return search_retriever.search()


async def generate_sub_queries(
    query: str,
    parent_query: str,
    report_type: str,
    context: list[dict[str, Any]],
    cfg: Config,
    cost_callback: Callable | None = None,
    prompt_family: type[PromptFamily] | PromptFamily = PromptFamily,
) -> list[str]:
    """
    Generate sub-queries using the specified LLM model.

    Args:
        query: The original query
        parent_query: The parent query
        report_type: The type of report
        max_iterations: Maximum number of research iterations
        context: Search results context
        cfg: Configuration object
        cost_callback: Callback for cost calculation
        prompt_family: Family of prompts

    Returns:
        A list of sub-queries
    """
    gen_queries_prompt = prompt_family.generate_search_queries_prompt(
        query,
        parent_query,
        report_type,
        max_iterations=cfg.max_iterations or 3,
        context=context,
    )

    try:
        response = await create_chat_completion(
            model=cfg.strategic_llm_model,
            messages=[{"role": "user", "content": gen_queries_prompt}],
            llm_provider=cfg.strategic_llm_provider,
            max_tokens=None,
            llm_kwargs=cfg.llm_kwargs,
            reasoning_effort=ReasoningEfforts.Medium.value,
            cost_callback=cost_callback,
        )
    except Exception as e:
        logger.warning(f"Error with strategic LLM: {e.__class__.__name__}: {e}. Retrying with max_tokens={cfg.strategic_token_limit}.")
        logger.warning("See https://github.com/assafelovic/gpt-researcher/issues/1022")
        try:
            response = await create_chat_completion(
                model=cfg.strategic_llm_model,
                messages=[{"role": "user", "content": gen_queries_prompt}],
                max_tokens=cfg.strategic_token_limit,
                llm_provider=cfg.strategic_llm_provider,
                llm_kwargs=cfg.llm_kwargs,
                cost_callback=cost_callback,
            )
            logger.warning(f"Retrying with max_tokens={cfg.strategic_token_limit} successful.")
        except Exception as e:
            logger.warning(f"Retrying with max_tokens={cfg.strategic_token_limit} failed.")
            logger.warning(f"Error with strategic LLM: {e.__class__.__name__}: {e}. Falling back to smart LLM.")
            response = await create_chat_completion(
                model=cfg.smart_llm_model,
                messages=[{"role": "user", "content": gen_queries_prompt}],
                temperature=cfg.temperature,
                max_tokens=cfg.smart_token_limit,
                llm_provider=cfg.smart_llm_provider,
                llm_kwargs=cfg.llm_kwargs,
                cost_callback=cost_callback,
            )

    result = json_repair.loads(response)
    assert isinstance(result, list), "Sub-queries must be a list, got %s" % type(result)
    return result


async def plan_research_outline(
    query: str,
    search_results: list[dict[str, Any]],
    agent_role_prompt: str,
    cfg: Config,
    parent_query: str,
    report_type: str,
    cost_callback: Callable | None = None,
) -> list[str]:
    """Plan the research outline by generating sub-queries.

    Args:
        query: Original query
        retriever: Retriever instance
        agent_role_prompt: Agent role prompt
        cfg: Configuration object
        parent_query: Parent query
        report_type: Report type
        cost_callback: Callback for cost calculation

    Returns:
        A list of sub-queries
    """

    sub_queries = await generate_sub_queries(query, parent_query, report_type, search_results, cfg, cost_callback)

    return sub_queries
