from __future__ import annotations

from typing import TYPE_CHECKING, Any, Callable

import json_repair
from langchain_core.retrievers import BaseRetriever

from gpt_researcher.llm_provider.generic.base import ReasoningEfforts
from ..utils.llm import create_chat_completion
from ..prompts import generate_search_queries_prompt
from typing import Any, List, Dict
from ..config import Config
import logging

from gpt_researcher.prompts import generate_search_queries_prompt
from gpt_researcher.utils.llm import create_chat_completion
from gpt_researcher.utils.logger import get_formatted_logger


if TYPE_CHECKING:
    import logging

    from json_repair.json_parser import JSONReturnType

    from gpt_researcher.config import Config
    from gpt_researcher.retrievers.retriever_abc import RetrieverABC
    from gpt_researcher.utils.enum import ReportType
    from gpt_researcher.utils.validators import BaseRetriever

logger: logging.Logger = get_formatted_logger(__name__)


async def get_search_results(
    query: str,
    retriever: type[BaseRetriever] | type[RetrieverABC],
    query_domains: list[str] | None = None,
) -> list[dict[str, Any]]:
    """Get web search results for a given query.

    Args:
    ----
        query (str): The search query
        retriever (type[BaseRetriever] | type): The retriever instance

    Returns:
    -------
        A list of search results
    """
    if isinstance(retriever, type) and issubclass(retriever, BaseRetriever):
        return [doc.model_dump() for doc in await retriever().ainvoke(query)]
    search_retriever: RetrieverABC = retriever(
        query,
        query_domains=query_domains,
    )
    return search_retriever.search()


async def generate_sub_queries(
    query: str,
    parent_query: str,
    report_type: str | ReportType,
    context: list[dict[str, Any]],
    cfg: Config,
    cost_callback: Callable[[float], None] | None = None,
) -> list[str]:
    """Generate sub-queries using the specified LLM model.

    Args:
    ----
        query (str): The original query
        parent_query (str): The parent query
        report_type (str | ReportType): The type of report
        max_iterations (int): Maximum number of research iterations
        context (list[dict[str, Any]]): Search results context
        cfg (Configuration): Configuration object
        cost_callback (Callable[[float], None] | None): Callback for cost calculation

    Returns:
    -------
        (str): A list of sub-queries
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
            temperature=0.6,
            llm_provider=cfg.STRATEGIC_LLM_PROVIDER,
            max_tokens=None,
            llm_kwargs=cfg.llm_kwargs,
            reasoning_effort=ReasoningEfforts.High.value,
            cost_callback=cost_callback,
        )
    except Exception as e:
        logger.warning(
            f"Error with strategic LLM! {e.__class__.__name__}: {e}. Retrying with max_tokens={cfg.STRATEGIC_TOKEN_LIMIT}."
        )
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
            logger.warning(f"Error with strategic LLM! {e.__class__.__name__}: {e}. Falling back to smart LLM.")
            response = await create_chat_completion(
                model=cfg.SMART_LLM,
                messages=[{"role": "user", "content": gen_queries_prompt}],
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
    """Plan the research outline by generating sub-queries.

    Args:
    ----
        query (str): Original query
        search_results (list[dict[str, Any]]): Search results
        agent_role_prompt (str): Agent role prompt
        retriever (list[dict[str, Any]]): Retriever instance
        agent_role_prompt (str): Agent role prompt
        cfg (Config): Configuration object
        parent_query (str): Parent query
        report_type (str): Report type
        cost_callback (Callable[[float], None] | None): Callback for cost calculation

    Returns:
    -------
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
