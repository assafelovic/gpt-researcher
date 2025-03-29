from __future__ import annotations

import json
import re

from typing import TYPE_CHECKING, Any, Callable

import json_repair

from gpt_researcher.prompts import auto_agent_instructions
from gpt_researcher.utils.llm import create_chat_completion

if TYPE_CHECKING:
    import logging

    from gpt_researcher.config import Config

from gpt_researcher.utils.logger import get_formatted_logger

logger: logging.Logger = get_formatted_logger(__name__)


async def choose_agent(
    query: str,
    cfg: Config,
    parent_query: str | None = None,
    cost_callback: Callable[[float], None] | None = None,
    headers: dict[str, Any] | None = None
) -> tuple[str, str]:
    """
    Chooses the agent automatically
    Args:
        parent_query: In some cases the research is conducted on a subtopic from the main query.
            The parent query allows the agent to know the main context for better reasoning.
        query: original query
        cfg: Config
        cost_callback: callback for calculating llm costs

    Returns:
        agent: Agent name
        agent_role_prompt: Agent role prompt
    """
    query = f"{parent_query} - {query}" if parent_query else f"{query}"
    response = None  # Initialize response to ensure it's defined

    try:
        response: str = await create_chat_completion(
            model=cfg.SMART_LLM_MODEL,
            messages=[
                {"role": "system", "content": f"{auto_agent_instructions()}"},
                {"role": "user", "content": f"task: {query}"},
            ],
            temperature=0.15,
            llm_provider=cfg.SMART_LLM_PROVIDER,
            llm_kwargs=cfg.llm_kwargs,
            cost_callback=cost_callback,
        )

        agent_dict = json.loads(response)
        return agent_dict["server"], agent_dict["agent_role_prompt"]

    except Exception:
        return await handle_json_error(response)


async def handle_json_error(response: str) -> tuple[str, str]:
    try:
        agent_dict = json_repair.loads(response)
        if agent_dict.get("server") and agent_dict.get("agent_role_prompt"):
            return agent_dict["server"], agent_dict["agent_role_prompt"]
    except Exception as e:
        logger.debug(f"⚠️ Error in reading JSON and failed to repair with json_repair: {e.__class__.__name__}: {e}")
        logger.debug(f"⚠️ LLM Response: `{response}`")

    json_string: str | None = extract_json_with_regex(response)
    if json_string and json_string.strip():
        try:
            json_data = json.loads(json_string)
            return json_data["server"], json_data["agent_role_prompt"]
        except json.JSONDecodeError as e:
            logger.debug(f"Error decoding JSON: {e.__class__.__name__}: {e}")
            logger.debug(f"⚠️ LLM Response: `{response}`")

    logger.debug("No JSON found in the string. Falling back to Default Agent.")
    return "Default Agent", (
        "You are an AI critical thinker research assistant. Your sole purpose is to write well written, "
        "critically acclaimed, objective and structured reports on given text."
    )


def extract_json_with_regex(response: str) -> str | None:
    json_match: re.Match[str] | None = re.search(r"{.*?}", response, re.DOTALL)
    if json_match:
        return json_match.group(0)
    return None
