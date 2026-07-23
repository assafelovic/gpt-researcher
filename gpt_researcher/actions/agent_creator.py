"""Agent creation and selection utilities for GPT Researcher.

This module provides functions to automatically select and configure
the appropriate research agent based on the query type.
"""

import json
import logging
import re

import json_repair

from ..prompts import PromptFamily
from ..utils.llm import create_chat_completion

logger = logging.getLogger(__name__)

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

        agent_dict = json.loads(response)
        return agent_dict["server"], agent_dict["agent_role_prompt"]

    except Exception as e:
        return await handle_json_error(response)


async def handle_json_error(response: str | None):
    """Handle JSON parsing errors from LLM responses.

    Attempts to recover agent information from malformed JSON responses
    using json_repair and regex extraction as fallbacks.

    Args:
        response: The LLM response string that failed initial JSON parsing.

    Returns:
        A tuple of (agent_name, agent_role_prompt). Returns default agent
        if all parsing attempts fail.
    """
    try:
        agent_dict = json_repair.loads(response) if response is not None else None
        recovered = _agent_pair_from_payload(agent_dict)
        if recovered is not None:
            return recovered
    except Exception as e:
        error_type = type(e).__name__
        error_msg = str(e)
        logger.warning(
            f"Failed to parse agent JSON with json_repair: {error_type}: {error_msg}",
            exc_info=True
        )
        if response:
            logger.debug(f"LLM response that failed to parse: {response[:500]}...")

    json_string = extract_json_with_regex(response)
    if json_string:
        try:
            json_data = json.loads(json_string)
            recovered = _agent_pair_from_payload(json_data)
            if recovered is not None:
                return recovered
        except json.JSONDecodeError as e:
            logger.warning(
                f"Failed to decode JSON from regex extraction: {str(e)}",
                exc_info=True
            )

    logger.info("No valid JSON found in LLM response. Falling back to default agent.")
    return "Default Agent", (
        "You are an AI critical thinker research assistant. Your sole purpose is to write well written, "
        "critically acclaimed, objective and structured reports on given text."
    )


def _agent_pair_from_payload(payload):
    """Return (server, agent_role_prompt) only for complete dict payloads."""
    if not isinstance(payload, dict):
        return None
    server = payload.get("server")
    role = payload.get("agent_role_prompt")
    if server and role:
        return server, role
    return None


def extract_json_with_regex(response: str | None) -> str | None:
    """Extract JSON object from a string using regex.

    Attempts to find the first JSON object pattern in the response string.

    Args:
        response: The string to search for JSON content.

    Returns:
        The extracted JSON string if found, None otherwise.
    """
    if not response:
        return None
    # Greedy ``{.*}`` so the match spans from the first ``{`` to the LAST ``}``
    # in the response, capturing the whole object. A non-greedy ``{.*?}``
    # stopped at the first ``}``, truncating any object with more than one
    # key or with a ``}`` inside a string value (e.g. an agent_role_prompt
    # mentioning "{markets}") into invalid JSON.
    json_match = re.search(r"{.*}", response, re.DOTALL)
    if json_match:
        return json_match.group(0)
    return None
