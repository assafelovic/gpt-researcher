from __future__ import annotations

import json
import logging
import re
from typing import TYPE_CHECKING, Any, Callable

import json_repair
from json_repair.json_parser import JSONReturnType

from gpt_researcher.prompts import auto_agent_instructions
from gpt_researcher.utils.llm import create_chat_completion

if TYPE_CHECKING:
    from gpt_researcher.config import Config

logger: logging.Logger = logging.getLogger(__name__)


async def choose_agent(
    query: str,
    cfg: Config,
    parent_query: str | None = None,
    cost_callback: Callable[[float], None] | None = None,
    headers: dict[str, str] | None = None,
) -> tuple[Any, Any] | tuple[str, str]:
    """Chooses the agent automatically.

    Args:
        parent_query: In some cases the research is conducted on a subtopic from the main query.
        The parent query allows the agent to know the main context for better reasoning.
        query: original query
        cfg: Config
        cost_callback: callback for calculating llm costs.

    Returns:
        agent: Agent name
        agent_role_prompt: Agent role prompt
    """
    query = f"{parent_query} - {query}" if parent_query else f"{query}"
    response: str | None = None

    try:
        response = await create_chat_completion(
            model=cfg.SMART_LLM_MODEL,
            messages=[
                {
                    "role": "system",
                    "content": f"{auto_agent_instructions()}",
                },
                {
                    "role": "user",
                    "content": f"task: {query}",
                },
            ],
            temperature=cfg.SMART_LLM_TEMPERATURE,
            llm_provider=cfg.SMART_LLM_PROVIDER,
            llm_kwargs=cfg.llm_kwargs,
            cost_callback=cost_callback,
            headers=headers,
        )

        if response is None:
            raise ValueError("Response is None")

        # Clean the response to remove invalid escape sequences
        response = re.sub(r'\\(?![\\/"bfnrtu]|u[0-9a-fA-F]{4})', '', response)

        agent_dict: dict[str, Any] = json.loads(response)
        return agent_dict["server"], agent_dict["agent_role_prompt"]

    except Exception as e:
        logger.exception(
            f"⚠️ Error in reading JSON: {e.__class__.__name__}: {e}. attempting to repair JSON"
        )
        return await handle_json_error(response or "")


async def handle_json_error(
    response: str,
) -> tuple[str, str]:
    try:
        agent_dict: JSONReturnType | tuple[JSONReturnType, list[dict[str, str]]] = (
            json_repair.loads(response)
        )
        if not isinstance(agent_dict, dict):
            raise TypeError("Agent dict is not a valid JSON")
        if agent_dict.get("server") and agent_dict.get("agent_role_prompt"):
            return agent_dict["server"], agent_dict["agent_role_prompt"]
    except Exception as e:
        logger.exception(f"Error using json_repair: {e}")

    json_string: str | None = extract_json_with_regex(response)
    if json_string and json_string.strip():
        try:
            json_data: dict[str, Any] = json.loads(json_string.encode().decode('utf-8'))  # type: ignore
            return json_data["server"], json_data["agent_role_prompt"]
        except json.JSONDecodeError as e:
            logger.exception(f"Error decoding JSON: {e.__class__.__name__}: {e}")
            try:
                # Fallback decoding strategy
                json_data = json.loads(json_string, strict=False)
                return json_data["server"], json_data["agent_role_prompt"]
            except Exception as e2:
                logger.exception(f"Secondary error decoding JSON: {e2.__class__.__name__}: {e2}")

    logger.warning("No JSON found in the string. Falling back to Default Agent.")
    return "Default Agent", (
        "You are an AI critical thinker research assistant. Your sole purpose is to write well written, critically acclaimed, objective and structured reports on given text."
    )


def extract_json_with_regex(
    response: str,
) -> str | None:
    json_match: re.Match[str] | None = re.search(r"{.*?}", response, re.DOTALL)
    if json_match:
        return json_match.group(0)
    return None
