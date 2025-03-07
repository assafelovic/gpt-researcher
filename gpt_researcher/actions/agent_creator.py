from __future__ import annotations

import json
import re

from typing import TYPE_CHECKING, Any, Callable

import json_repair

from gpt_researcher.prompts import auto_agent_instructions
from gpt_researcher.utils.llm import create_chat_completion

if TYPE_CHECKING:
    import logging

    from json_repair.json_parser import JSONReturnType

    from gpt_researcher.config import Config

from gpt_researcher.utils.logger import get_formatted_logger

logger: logging.Logger = get_formatted_logger(__name__)


async def choose_agent(
    query: str,
    cfg: Config,
    parent_query: str | None = None,
    cost_callback: Callable[[float], None] | None = None,
    headers: dict[str, str] | None = None,
) -> dict[str, Any]:
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
                {"role": "system", "content": f"{auto_agent_instructions()}"},
                {"role": "user", "content": f"task: {query}"},
            ],
            temperature=cfg.SMART_LLM_TEMPERATURE,
            llm_provider=cfg.SMART_LLM_PROVIDER,
            llm_kwargs=cfg.llm_kwargs,
            cost_callback=cost_callback,
        )

        try:
            agent_dict: dict[str, Any] = json.loads(response)
            return agent_dict
        except json.JSONDecodeError as e:
            logger.warning(f"⚠️ Error in reading JSON: {e.__class__.__name__}: {e}. attempting to repair JSON")
            response = (
                re.sub(r'\\(?![\\/"bfnrtu]|u[0-9a-fA-F]{4})', "", response)
                .replace("\n", "")
                .replace("\r", "")
                .replace(" ", "")
            )
            agent_dict: dict[str, Any] = json.loads(response)
        return agent_dict

    except Exception as e:
        logger.warning(f"⚠️ Error in reading JSON: {e.__class__.__name__}: {e}. attempting to repair JSON")
        return await handle_json_error(response or "")


async def handle_json_error(
    response: str,
) -> dict[str, Any]:
    try:
        agent_dict: JSONReturnType | tuple[JSONReturnType, list[dict[str, str]]] = json_repair.loads(response)
        if not isinstance(agent_dict, dict):
            raise TypeError("Agent dict is not a valid JSON")
        agent_dict["server"] = agent_dict.get("server", "Default Agent")
        agent_dict["agent_role_prompt"] = agent_dict.get(
            "agent_role_prompt",
            "You are an AI critical thinker research assistant. Your sole purpose is to write well written, critically acclaimed, objective and structured reports on given text.",
        )
        if agent_dict.get("server") and agent_dict.get("agent_role_prompt"):
            return agent_dict
    except Exception as e:
        logger.exception(f"Error using json_repair: {e}")

    json_string: str | None = extract_json_with_regex(response)
    if json_string and json_string.strip():
        try:
            agent_dict = json.loads(json_string.encode().decode("utf-8"))  # type: ignore
            if not isinstance(agent_dict, dict):
                raise TypeError("Agent dict is not a valid JSON")
            agent_dict["server"] = agent_dict.get("server", "Default Agent")
            agent_dict["agent_role_prompt"] = agent_dict.get(
                "agent_role_prompt",
                "You are an AI critical thinker research assistant. Your sole purpose is to write well written, critically acclaimed, objective and structured reports on given text.",
            )
        except json.JSONDecodeError as e:
            logger.exception(f"Error decoding JSON: {e.__class__.__name__}: {e}")
            try:
                agent_dict = json.loads(json_string, strict=False)
                if not isinstance(agent_dict, dict):
                    raise TypeError("Agent dict is not a valid JSON")
                agent_dict["server"] = agent_dict.get("server", "Default Agent")
                agent_dict["agent_role_prompt"] = agent_dict.get(
                    "agent_role_prompt",
                    "You are an AI critical thinker research assistant. Your sole purpose is to write well written, critically acclaimed, objective and structured reports on given text.",
                )
                return agent_dict
            except Exception as e2:
                logger.exception(f"Secondary error decoding JSON: {e2.__class__.__name__}: {e2}")
        else:
            return agent_dict

    logger.warning("No JSON found in the string. Falling back to Default Agent.")
    return {
        "server": "Default Agent",
        "agent_role_prompt": "You are an AI critical thinker research assistant. Your sole purpose is to write well written, critically acclaimed, objective and structured reports on given text.",
    }


def extract_json_with_regex(
    response: str,
) -> str | None:
    json_match: re.Match[str] | None = re.search(r"{.*?}", response, re.DOTALL)
    if json_match:
        return json_match.group(0)
    return None
