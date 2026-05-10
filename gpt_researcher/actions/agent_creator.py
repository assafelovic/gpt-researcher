"""Agent creation and selection utilities for GPT Researcher.

This module provides functions to automatically select and configure
the appropriate research agent based on the query type.
"""

import logging

from ..prompts import PromptFamily
from ..utils.json_parsing import extract_json_fragment, parse_llm_json_response
from ..utils.llm import create_chat_completion

logger = logging.getLogger(__name__)

DEFAULT_AGENT_ROLE_PROMPT = (
    "You are an AI critical thinker research assistant. Your sole purpose is to write well written, "
    "critically acclaimed, objective and structured reports on given text."
)

FINANCE_AGENT_ROLE_PROMPT = (
    "You are a seasoned finance analyst AI assistant. Your primary goal is to compose comprehensive, astute, "
    "impartial, and methodically arranged financial reports based on provided data and trends."
)

BUSINESS_AGENT_ROLE_PROMPT = (
    "You are an experienced AI business analyst assistant. Your main objective is to produce comprehensive, "
    "insightful, impartial, and systematically structured business reports based on provided business data, "
    "market trends, and strategic analysis."
)

TRAVEL_AGENT_ROLE_PROMPT = (
    "You are a world-travelled AI tour guide assistant. Your main purpose is to draft engaging, insightful, "
    "unbiased, and well-structured travel reports on given locations, including history, attractions, and "
    "cultural insights."
)

RESEARCH_AGENT_ROLE_PROMPT = (
    "You are a meticulous research assistant AI. Your primary goal is to produce accurate, structured, "
    "evidence-based research summaries with clear reasoning and references."
)


def _fallback_agent_for_query(query: str | None) -> tuple[str, str]:
    normalized_query = (query or "").lower()

    finance_keywords = (
        "stock",
        "stocks",
        "investment",
        "invest",
        "finance",
        "financial",
        "market cap",
        "revenue",
        "earnings",
        "profit",
        "trading",
    )
    travel_keywords = (
        "travel",
        "trip",
        "flight",
        "hotel",
        "vacation",
        "visit",
        "city",
        "attractions",
        "sites",
        "tour",
    )
    business_keywords = (
        "business",
        "startup",
        "company",
        "market",
        "competition",
        "reselling",
        "strategy",
        "pricing",
        "customers",
        "product",
    )

    if any(keyword in normalized_query for keyword in finance_keywords):
        return "💰 Finance Agent", FINANCE_AGENT_ROLE_PROMPT
    if any(keyword in normalized_query for keyword in travel_keywords):
        return "🌍 Travel Agent", TRAVEL_AGENT_ROLE_PROMPT
    if any(keyword in normalized_query for keyword in business_keywords):
        return "📈 Business Analyst Agent", BUSINESS_AGENT_ROLE_PROMPT

    return "🔬 Research Assistant Agent", RESEARCH_AGENT_ROLE_PROMPT


def _extract_agent_choice(payload: object) -> tuple[str, str] | None:
    if not isinstance(payload, dict):
        return None

    server = payload.get("server")
    agent_role_prompt = payload.get("agent_role_prompt")
    if isinstance(server, str) and isinstance(agent_role_prompt, str):
        return server, agent_role_prompt

    for nested_key in ("response", "data", "result"):
        nested_payload = payload.get(nested_key)
        if isinstance(nested_payload, dict):
            extracted = _extract_agent_choice(nested_payload)
            if extracted:
                return extracted

    return None


def _extract_agent_choice_from_text(response: str | object | None) -> tuple[str, str] | None:
    payload = parse_llm_json_response(response, expected_kind="object")
    return _extract_agent_choice(payload)

async def choose_agent(
    query,
    cfg,
    parent_query=None,
    cost_callback: callable = None,
    headers=None,
    prompt_family: type[PromptFamily] | PromptFamily = PromptFamily,
    **kwargs
):
    """
    Chooses the agent automatically
    Args:
        parent_query: In some cases the research is conducted on a subtopic from the main query.
            The parent query allows the agent to know the main context for better reasoning.
        query: original query
        cfg: Config
        cost_callback: callback for calculating llm costs
        prompt_family: Family of prompts

    Returns:
        agent: Agent name
        agent_role_prompt: Agent role prompt
    """
    query = f"{parent_query} - {query}" if parent_query else f"{query}"
    response = None  # Initialize response to ensure it's defined

    try:
        response = await create_chat_completion(
            model=cfg.smart_llm_model,
            messages=[
                {"role": "system", "content": f"{prompt_family.auto_agent_instructions()}"},
                {"role": "user", "content": f"task: {query}"},
            ],
            temperature=0.15,
            llm_provider=cfg.smart_llm_provider,
            llm_kwargs=cfg.llm_kwargs,
            cost_callback=cost_callback,
            **kwargs
        )

        extracted = _extract_agent_choice_from_text(response)
        if extracted:
            return extracted

        return await handle_json_error(response, query)

    except Exception:
        return await handle_json_error(response, query)


async def handle_json_error(response: str | None, query: str | None = None):
    """Recover an agent choice from a malformed LLM response.

    This uses the shared JSON parser first and only falls back to the
    heuristic agent picker if the response still cannot be normalized.

    Args:
        response: The LLM response string that failed initial JSON parsing.

    Returns:
        A tuple of (agent_name, agent_role_prompt). Returns default agent
        if all parsing attempts fail.
    """
    if extracted := _extract_agent_choice_from_text(response):
        return extracted

    logger.info("No valid JSON found in LLM response. Falling back to heuristic agent.")
    return _fallback_agent_for_query(query)


def extract_json_with_regex(response: str | None) -> str | None:
    """Compatibility wrapper around the shared JSON fragment extractor.

    Older callers still import this name, but the central parsing logic now
    lives in :func:`gpt_researcher.utils.json_parsing.extract_json_fragment`.

    Args:
        response: The string to search for JSON content.

    Returns:
        The extracted JSON string if found, None otherwise.
    """
    return extract_json_fragment(response)
