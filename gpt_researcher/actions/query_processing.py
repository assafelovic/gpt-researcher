from __future__ import annotations

import logging

from typing import TYPE_CHECKING, Any, Callable

import json_repair

from litellm.utils import get_max_tokens

from gpt_researcher.llm_provider.generic.base import GenericLLMProvider
from gpt_researcher.prompts import generate_search_queries_prompt
from gpt_researcher.utils.schemas import ReportType

if TYPE_CHECKING:
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


logger = logging.getLogger(__name__)


async def get_search_results(
    query: str,
    retriever: Any,
) -> list[dict[str, Any]]:
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
    report_type: ReportType,
    context: list[dict[str, Any]],
    cfg: Config,
    cost_callback: Callable[[float], None] | None = None,
) -> list[str]:
    """Generate sub-queries using the specified LLM model.

    Args:
        query: The original query
        parent_query: The parent query
        report_type: The type of report
        max_iterations: Maximum number of research iterations
        context: Search results context
        cfg: Configuration object
        cost_callback: Callback for cost calculation

    Returns:
        A list of sub-queries
    """
    gen_queries_prompt = generate_search_queries_prompt(
        query,
        parent_query,
        report_type,
        max_iterations=cfg.MAX_ITERATIONS or 1,
        context=context,
    )

    try:
        # Try with strategic LLM first
        provider = _get_llm(
            cfg,
            model=cfg.STRATEGIC_LLM_MODEL,
            temperature=1.0,
        )
        response = await provider.get_chat_response(
            messages=[{"role": "user", "content": gen_queries_prompt}],
            stream=False,
        )
    except Exception as e:
        # If that fails, try with max tokens limit
        smart_token_limit = get_max_tokens(cfg.SMART_LLM_MODEL or "")
        logger.warning(
            f"Error with strategic LLM: {e.__class__.__name__}: {e}. Retrying with max_tokens={smart_token_limit}.",
            exc_info=True,
        )
        logger.warning("See https://github.com/assafelovic/gpt-researcher/issues/1022")
        try:
            # Retry strategic LLM with token limit
            provider = _get_llm(
                cfg,
                model=cfg.STRATEGIC_LLM_MODEL,
                temperature=1.0,
                max_tokens=smart_token_limit,
            )
            response = await provider.get_chat_response(
                messages=[{"role": "user", "content": gen_queries_prompt}],
                stream=False,
            )
            logger.warning(f"Retrying with max_tokens={smart_token_limit} successful.")
        except Exception as e:
            # If that fails too, fall back to smart LLM
            logger.warning(f"Retrying with max_tokens={smart_token_limit} failed.")
            logger.warning(
                f"Error with strategic LLM: {e.__class__.__name__}: {e}. Falling back to smart LLM.",
                exc_info=True,
            )
            provider = _get_llm(
                cfg,
                model=cfg.SMART_LLM_MODEL,
                temperature=cfg.TEMPERATURE,
                max_tokens=smart_token_limit,
            )
            response = await provider.get_chat_response(
                messages=[{"role": "user", "content": gen_queries_prompt}],
                stream=False,
            )

    if cost_callback:
        from gpt_researcher.utils.costs import estimate_llm_cost
        llm_costs = estimate_llm_cost(gen_queries_prompt, response)
        cost_callback(llm_costs)

    result = json_repair.loads(response)
    assert not isinstance(result, (int, float, str, dict, tuple, type(None)))
    return result
