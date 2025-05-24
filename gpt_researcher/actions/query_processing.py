from __future__ import annotations

import logging
from typing import Any, Callable

import json_repair

from gpt_researcher.config import Config
from gpt_researcher.llm_provider.generic.base import ReasoningEfforts
from gpt_researcher.prompts import PromptFamily
from gpt_researcher.retrievers.retriever_abc import RetrieverABC
from gpt_researcher.utils.llm import create_chat_completion

logger: logging.Logger = logging.getLogger(__name__)


async def get_search_results(
    query: str,
    retriever: Callable[[str, dict[str, Any] | None], RetrieverABC] | type[RetrieverABC],
    query_domains: list[str] | None = None,
) -> list[dict[str, Any]]:
    """Get web search results for a given query.

    Args:
        query: The search query
        retriever: The retriever instance
        query_domains: Optional list of domains to search
    Returns:
        A list of search results
    """
    search_retriever: RetrieverABC = retriever(query, query_domains=query_domains)
    return search_retriever.search()  # pyright: ignore[reportCallIssue]  # TODO: actually inherit RetrieverABC everywhere.


async def generate_sub_queries(
    query: str,
    parent_query: str,
    report_type: str,
    context: list[dict[str, Any]] | None = None,
    cfg: Config | None = None,
    cost_callback: Callable[[float], None] | None = None,
    prompt_family: type[PromptFamily] | PromptFamily = PromptFamily,
) -> list[str]:
    """Generate sub-queries using the specified LLM model.

    Args:
        query: The original query
        parent_query: The parent query
        report_type: The type of report
        context: Search results context
        cfg: Configuration object
        cost_callback: Callback for cost calculation
        prompt_family: Family of prompts

    Returns:
        A list of sub-queries
    """
    cfg = Config() if cfg is None else cfg
    gen_queries_prompt: str = prompt_family.generate_search_queries_prompt(
        query,
        parent_query,
        report_type,
        max_iterations=cfg.max_iterations or 3,  # pyright: ignore[reportAttributeAccessIssue]
        context=context,
    )

    try:
        response: str = await create_chat_completion(
            model=cfg.strategic_llm_model,
            messages=[{"role": "user", "content": gen_queries_prompt}],
            llm_provider=cfg.strategic_llm_provider,
            max_tokens=None,
            llm_kwargs=cfg.llm_kwargs,
            reasoning_effort=ReasoningEfforts.Medium.value,
            cost_callback=cost_callback,
        )
    except Exception as e:
        logger.warning(f"Error with strategic LLM: {e.__class__.__name__}: {e}. Retrying with max_tokens={cfg.strategic_token_limit}.")  # pyright: ignore[reportAttributeAccessIssue]
        logger.warning("See https://github.com/assafelovic/gpt-researcher/issues/1022")
        try:
            response = await create_chat_completion(
                model=cfg.strategic_llm_model,
                messages=[{"role": "user", "content": gen_queries_prompt}],
                max_tokens=cfg.strategic_token_limit,  # pyright: ignore[reportAttributeAccessIssue]
                llm_provider=cfg.strategic_llm_provider,
                llm_kwargs=cfg.llm_kwargs,
                cost_callback=cost_callback,
            )
            logger.warning(f"Retrying with max_tokens={cfg.strategic_token_limit} successful.")  # pyright: ignore[reportAttributeAccessIssue]
        except Exception as e:
            logger.warning(f"Retrying with max_tokens={cfg.strategic_token_limit} failed.")  # pyright: ignore[reportAttributeAccessIssue]
            logger.warning(f"Error with strategic LLM: {e.__class__.__name__}: {e}. Falling back to smart LLM.")
            response = await create_chat_completion(
                model=cfg.smart_llm_model,
                messages=[{"role": "user", "content": gen_queries_prompt}],
                temperature=cfg.temperature,  # pyright: ignore[reportAttributeAccessIssue]
                max_tokens=cfg.smart_token_limit,  # pyright: ignore[reportAttributeAccessIssue]
                llm_provider=cfg.smart_llm_provider,
                llm_kwargs=cfg.llm_kwargs,
                cost_callback=cost_callback,
            )

    result: str | list[str] | dict[str, str] | int | float | bool = json_repair.loads(response)
    if isinstance(result, str):
        return [query.strip() for query in result.split("\n")]
    if isinstance(result, list):
        return result
    if isinstance(result, dict):
        return [str(query).strip() for query in result.values()]
    if isinstance(result, (int, float, bool)):
        return [str(result)]
    raise ValueError(f"Invalid result type: `{result.__class__.__name__}`, expected `list`")


async def plan_research_outline(
    query: str,
    search_results: list[dict[str, Any]],
    agent_role_prompt: str,
    cfg: Config,
    parent_query: str,
    report_type: str,
    cost_callback: Callable[[float], None] | None = None,
    retriever_names: list[str] | None = None,
) -> list[str]:
    """Plan the research outline by generating sub-queries.

    Args:
        query (str): Original query
        search_results (list[dict[str, Any]]): Search results
        agent_role_prompt (str): Agent role prompt
        cfg (Config): Configuration object
        parent_query (str): Parent query
        report_type (str): Report type
        cost_callback (Callable[[float], None] | None): Callback for cost calculation
        retriever_names (list[str] | None): Names of the retrievers being used

    Returns:
        A list of sub-queries
    """
    retriever_names = [] if retriever_names is None else retriever_names

    # For MCP retrievers, we may want to skip sub-query generation
    # Check if MCP is the only retriever or one of multiple retrievers
    if (
        retriever_names
        and ("mcp" in retriever_names or "MCPRetriever" in retriever_names)
    ):
        mcp_only: bool = (
            len(retriever_names) == 1
            and (
                "mcp" in retriever_names
                or "MCPRetriever" in retriever_names  # pyright: ignore[dontUnwrapThis]
            )
        )

        if mcp_only:
            logger.info("Using MCP retriever only - skipping sub-query generation")
            return [query]
        else:
            logger.info("Using MCP with other retrievers - generating sub-queries for non-MCP retrievers")

    sub_queries: list[str] = await generate_sub_queries(
        query,
        parent_query,
        report_type,
        search_results,
        cfg,
        cost_callback,
    )

    return sub_queries
