import json
import re

import json_repair

from gpt_researcher.llm_provider.generic.base import ReasoningEfforts
from ..utils.llm import create_chat_completion
from ..prompts import PromptFamily
from typing import Any, List, Dict
from ..config import Config
import logging

logger = logging.getLogger(__name__)

_QUERY_STOPWORDS = {
    "a",
    "about",
    "across",
    "after",
    "against",
    "all",
    "along",
    "an",
    "and",
    "around",
    "as",
    "at",
    "be",
    "because",
    "between",
    "both",
    "but",
    "by",
    "can",
    "compare",
    "comparison",
    "compared",
    "current",
    "difference",
    "differences",
    "do",
    "does",
    "for",
    "from",
    "guide",
    "how",
    "in",
    "into",
    "is",
    "it",
    "latest",
    "learn",
    "main",
    "may",
    "new",
    "of",
    "official",
    "on",
    "overview",
    "please",
    "practical",
    "query",
    "research",
    "report",
    "results",
    "review",
    "status",
    "task",
    "the",
    "their",
    "them",
    "this",
    "to",
    "today",
    "topic",
    "tradeoff",
    "tradeoffs",
    "tutorial",
    "use",
    "using",
    "versus",
    "vs",
    "what",
    "when",
    "where",
    "which",
    "why",
    "with",
    "without",
}

_COMPARISON_MARKERS = (
    " vs ",
    " versus ",
    " between ",
    " compared to ",
    " comparison ",
    " compare ",
    " tradeoff ",
    " tradeoffs ",
    " difference ",
    " differences ",
    " against ",
)


def _task_text(query: str, parent_query: str) -> str:
    return f"{parent_query} - {query}".strip() if parent_query else query.strip()


def _normalize_query_token(token: str) -> str:
    return re.sub(r"[^a-z0-9]+", "", token.lower()).strip()


def _extract_focus_terms(text: str | None) -> list[str]:
    if not text:
        return []

    terms: list[str] = []
    seen: set[str] = set()
    for raw_token in re.findall(r"[A-Za-z0-9]+", text):
        normalized = _normalize_query_token(raw_token)
        if not normalized:
            continue
        if normalized in _QUERY_STOPWORDS:
            continue
        if len(normalized) == 1 and not normalized.isdigit():
            continue
        if normalized in seen:
            continue
        seen.add(normalized)
        terms.append(normalized)
    return terms


def _is_comparison_query(text: str | None) -> bool:
    if not text:
        return False
    lowered = f" {text.lower()} "
    return any(marker in lowered for marker in _COMPARISON_MARKERS)


def _required_overlap_count(focus_terms: list[str], task_text: str) -> int:
    if not focus_terms:
        return 0
    if _is_comparison_query(task_text):
        return 2 if len(focus_terms) >= 2 else 1
    if len(focus_terms) <= 2:
        return 1
    if len(focus_terms) <= 5:
        return 2
    return 3


def _is_task_anchored_query(
    candidate: str,
    query: str,
    parent_query: str,
    focus_terms: list[str] | None = None,
) -> bool:
    if not _looks_like_search_query(candidate):
        return False

    task = _task_text(query, parent_query)
    task_focus_terms = focus_terms or _extract_focus_terms(task)
    if not task_focus_terms:
        return _looks_like_search_query(candidate)

    candidate_terms = _extract_focus_terms(candidate)
    if not candidate_terms:
        return False

    task_focus_set = set(task_focus_terms)
    overlap = [term for term in candidate_terms if term in task_focus_set]
    if not overlap:
        return False

    required_overlap = _required_overlap_count(task_focus_terms, task)
    if len(overlap) < required_overlap:
        return False

    return True


def _looks_like_search_query(candidate: str) -> bool:
    lowered = candidate.lower()
    if len(candidate) < 4:
        return False
    if any(marker in lowered for marker in ("queryselector", "http://", "https://", "<|", "</", "```")):
        return False
    if candidate.startswith("{") or candidate.startswith("}") or candidate.startswith("[") or candidate.startswith("]"):
        return False
    if candidate.startswith("task:") or candidate.startswith("response:"):
        return False
    return True


def _normalize_query_items(items) -> list[str]:
    normalized: list[str] = []
    seen: set[str] = set()

    for item in items:
        if item is None:
            continue
        candidate = str(item).strip()
        candidate = re.sub(r"^[\-\*\u2022\d\.\)\s]+", "", candidate).strip()
        candidate = candidate.strip("\"'").strip()
        key = re.sub(r"\s+", " ", candidate).strip().lower()
        if not candidate or key in seen or not _looks_like_search_query(candidate):
            continue
        seen.add(key)
        normalized.append(candidate)

    return normalized


def _extract_bracketed_json(response: str | None, open_char: str, close_char: str) -> str | None:
    if not response:
        return None
    start = response.find(open_char)
    end = response.rfind(close_char)
    if start == -1 or end == -1 or end <= start:
        return None
    return response[start : end + 1]


def _extract_query_list(payload: object) -> list[str]:
    if isinstance(payload, list):
        return _normalize_query_items(payload)

    if isinstance(payload, dict):
        for key in ("queries", "sub_queries", "subqueries", "search_queries", "items", "results"):
            value = payload.get(key)
            if isinstance(value, list):
                normalized = _normalize_query_items(value)
                if normalized:
                    return normalized

    if isinstance(payload, str):
        candidates = []
        if json_array := _extract_bracketed_json(payload, "[", "]"):
            candidates.append(json_array)
        if json_object := _extract_bracketed_json(payload, "{", "}"):
            candidates.append(json_object)

        for candidate in candidates:
            for loader in (json_repair.loads, json.loads):
                try:
                    parsed = loader(candidate)
                except Exception:
                    continue

                extracted = _extract_query_list(parsed)
                if extracted:
                    return extracted

        bullet_lines = _normalize_query_items(line for line in payload.splitlines())
        if bullet_lines:
            return bullet_lines

    return []


def _fallback_sub_queries(query: str, parent_query: str, max_iterations: int) -> list[str]:
    task = _task_text(query, parent_query)
    candidates = [
        task,
        f"{task} overview",
        f"{task} analysis",
        f"{task} official documentation",
        f"{task} examples",
        f"{task} benchmarks",
    ]
    anchored_candidates = [
        candidate
        for candidate in _normalize_query_items(candidates)
        if _is_task_anchored_query(candidate, query, parent_query)
    ]
    return anchored_candidates[:max_iterations]


def _complete_sub_queries(
    response: str | object,
    query: str,
    parent_query: str,
    max_iterations: int,
    focus_terms: list[str] | None = None,
) -> list[str]:
    task = _task_text(query, parent_query)
    task_focus_terms = focus_terms or _extract_focus_terms(task)
    normalized = []
    normalized_keys: set[str] = set()
    for candidate in _extract_query_list(response):
        if _is_task_anchored_query(candidate, query, parent_query, task_focus_terms):
            key = re.sub(r"\s+", " ", candidate).strip().lower()
            if key in normalized_keys:
                continue
            normalized_keys.add(key)
            normalized.append(candidate)
        else:
            logger.debug("Dropping off-topic planned sub-query for %s: %s", task, candidate)
    if not normalized:
        return _fallback_sub_queries(query, parent_query, max_iterations)

    if len(normalized) >= max_iterations:
        return normalized[:max_iterations]

    for candidate in _fallback_sub_queries(query, parent_query, max_iterations * 2):
        candidate_key = re.sub(r"\s+", " ", candidate).strip().lower()
        if candidate_key not in normalized_keys:
            normalized_keys.add(candidate_key)
            normalized.append(candidate)
        if len(normalized) >= max_iterations:
            break

    return normalized[:max_iterations]

async def get_search_results(query: str, retriever: Any, query_domains: List[str] = None, researcher=None) -> List[Dict[str, Any]]:
    """
    Get web search results for a given query.

    Args:
        query: The search query
        retriever: The retriever instance
        query_domains: Optional list of domains to search
        researcher: The researcher instance (needed for MCP retrievers)

    Returns:
        A list of search results
    """
    # Check if this is an MCP retriever and pass the researcher instance
    if "mcpretriever" in retriever.__name__.lower():
        search_retriever = retriever(
            query, 
            query_domains=query_domains,
            researcher=researcher  # Pass researcher instance for MCP retrievers
        )
    else:
        search_retriever = retriever(query, query_domains=query_domains)
    
    return search_retriever.search()

async def generate_sub_queries(
    query: str,
    parent_query: str,
    report_type: str,
    context: List[Dict[str, Any]],
    cfg: Config,
    cost_callback: callable = None,
    prompt_family: type[PromptFamily] | PromptFamily = PromptFamily,
    **kwargs
) -> List[str]:
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
    task = _task_text(query, parent_query)
    focus_terms = _extract_focus_terms(task)

    gen_queries_prompt = prompt_family.generate_search_queries_prompt(
        query,
        parent_query,
        report_type,
        max_iterations=cfg.max_iterations or 3,
        context=context,
        focus_terms=focus_terms,
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
            **kwargs
        )
    except Exception as e:
        logger.warning(f"Error with strategic LLM: {e}. Retrying with max_tokens={cfg.strategic_token_limit}.")
        logger.warning(f"See https://github.com/assafelovic/gpt-researcher/issues/1022")
        try:
            response = await create_chat_completion(
                model=cfg.strategic_llm_model,
                messages=[{"role": "user", "content": gen_queries_prompt}],
                max_tokens=cfg.strategic_token_limit,
                llm_provider=cfg.strategic_llm_provider,
                llm_kwargs=cfg.llm_kwargs,
                cost_callback=cost_callback,
                **kwargs
            )
            logger.warning(f"Retrying with max_tokens={cfg.strategic_token_limit} successful.")
        except Exception as e:
            logger.warning(f"Retrying with max_tokens={cfg.strategic_token_limit} failed.")
            logger.warning(f"Error with strategic LLM: {e}. Falling back to smart LLM.")
            try:
                response = await create_chat_completion(
                    model=cfg.smart_llm_model,
                    messages=[{"role": "user", "content": gen_queries_prompt}],
                    temperature=cfg.temperature,
                    max_tokens=cfg.smart_token_limit,
                    llm_provider=cfg.smart_llm_provider,
                    llm_kwargs=cfg.llm_kwargs,
                    cost_callback=cost_callback,
                    **kwargs
                )
            except Exception as smart_error:
                logger.warning(
                    f"Smart LLM fallback failed: {smart_error}. Using deterministic anchored sub-queries."
                )
                return _fallback_sub_queries(query, parent_query, cfg.max_iterations or 3)

    return _complete_sub_queries(
        response,
        query,
        parent_query,
        cfg.max_iterations or 3,
        focus_terms=focus_terms,
    )

async def plan_research_outline(
    query: str,
    search_results: List[Dict[str, Any]],
    agent_role_prompt: str,
    cfg: Config,
    parent_query: str,
    report_type: str,
    cost_callback: callable = None,
    retriever_names: List[str] = None,
    **kwargs
) -> List[str]:
    """
    Plan the research outline by generating sub-queries.

    Args:
        query: Original query
        search_results: Initial search results
        agent_role_prompt: Agent role prompt
        cfg: Configuration object
        parent_query: Parent query
        report_type: Report type
        cost_callback: Callback for cost calculation
        retriever_names: Names of the retrievers being used

    Returns:
        A list of sub-queries
    """
    # Handle the case where retriever_names is not provided
    if retriever_names is None:
        retriever_names = []
    
    # For MCP retrievers, we may want to skip sub-query generation
    # Check if MCP is the only retriever or one of multiple retrievers
    if retriever_names and ("mcp" in retriever_names or "MCPRetriever" in retriever_names):
        mcp_only = (len(retriever_names) == 1 and 
                   ("mcp" in retriever_names or "MCPRetriever" in retriever_names))
        
        if mcp_only:
            # If MCP is the only retriever, skip sub-query generation
            logger.info("Using MCP retriever only - skipping sub-query generation")
            # Return the original query to prevent additional search iterations
            return [query]
        else:
            # If MCP is one of multiple retrievers, generate sub-queries for the others
            logger.info("Using MCP with other retrievers - generating sub-queries for non-MCP retrievers")

    # Generate sub-queries for research outline
    sub_queries = await generate_sub_queries(
        query,
        parent_query,
        report_type,
        search_results,
        cfg,
        cost_callback,
        **kwargs
    )

    return sub_queries
