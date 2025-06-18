from __future__ import annotations

import json
import re

from typing import Any, Callable

import json_repair

from gpt_researcher.config import Config
from gpt_researcher.prompts import PromptFamily
from gpt_researcher.utils.llm import create_chat_completion


async def choose_agent(
    query: str,
    cfg: Config,
    parent_query: str | None = None,
    cost_callback: Callable[[float], None] | None = None,
    headers: dict[str, str] | None = None,
    prompt_family: type[PromptFamily] | PromptFamily = PromptFamily,
    **kwargs,
) -> tuple[str, str]:
    """Chooses the agent automatically.

    Args:
        query: original query
        cfg: Config object
        parent_query: In some cases the research is conducted on a subtopic from the main query.
            The parent query allows the agent to know the main context for better reasoning.
        cost_callback: callback for calculating llm costs
        headers: headers for the llm request
        prompt_family: Family of prompts

    Returns:
        agent: Agent name
        agent_role_prompt: Agent role prompt
    """
    parent_query = "" if parent_query is None else parent_query
    query = f"{parent_query} - {query}" if parent_query else f"{query}"
    response = None  # Initialize response to ensure it's defined

    try:
        response = await create_chat_completion(
            model=cfg.strategic_llm_model,
            messages=[
                {"role": "system", "content": f"{prompt_family.auto_agent_instructions()}"},
                {"role": "user", "content": f"task: {query}"},
            ],
            llm_provider=cfg.strategic_llm_provider,
#            max_tokens=cfg.strategic_token_limit,  # pyright: ignore[reportAttributeAccessIssue]
            llm_kwargs=cfg.llm_kwargs,
            cost_callback=cost_callback,
            cfg=cfg,
        )
    except Exception as e:
        # Handle fallback for strategic LLM
        print(f"Error with strategic LLM, falling back to smart LLM: {e.__class__.__name__}: {e}")
        # Log to stderr
        import sys

        sys.stderr.write(f"Error with strategic LLM, falling back to smart LLM: {e.__class__.__name__}: {e}\n")
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
            cfg=cfg,
            **kwargs
        )

    # Split the response to get the agent name and description
    try:
        agent_name: str = ""
        agent_role_prompt: str = ""
        parts: list[str] = response.strip().split("AGENT ROLE:")
        if len(parts) >= 2:
            agent_name = parts[0].strip().replace("AGENT NAME:", "").strip()
            agent_role_prompt = parts[1].strip()
    except Exception:
        # Return default values
        return "Research Agent", "You are a helpful research agent."
    else:
        return agent_name, agent_role_prompt


async def handle_json_error(response: str | None) -> tuple[str, str]:
    try:
        agent_dict: dict[str, Any] = json_repair.loads(response)
        if agent_dict.get("server") and agent_dict.get("agent_role_prompt"):  # pyright: ignore[reportAttributeAccessIssue]
            return agent_dict["server"], agent_dict["agent_role_prompt"]  # pyright: ignore[reportCallIssue, reportIndexIssue, reportOptionalSubscript]
    except Exception as e:
        print(f"⚠️ Error in reading JSON and failed to repair with json_repair: {e}")
        print(f"⚠️ LLM Response: `{response}`")

    json_string: str | None = extract_json_with_regex(response)
    if json_string is not None:
        try:
            json_data: dict[str, Any] = json.loads(json_string)
            return json_data["server"], json_data["agent_role_prompt"]
        except json.JSONDecodeError as e:
            print(f"Error decoding JSON: {e.__class__.__name__}: {e}")

    print("No JSON found in the string. Falling back to Default Agent.")
    return "Default Agent", (
        "You are an AI critical thinker research assistant. Your sole purpose is to write well written, "
        "critically acclaimed, objective and structured reports on given text."
    )


def extract_json_with_regex(response: str | None) -> str | None:
    """Extract JSON with regex from the response.

    Args:
        response (str | None): The response to extract JSON from.

    Returns:
        str | None: The extracted JSON.
    """
    if response is None:
        return None
    json_match: re.Match[str] | None = re.search(r"{.*?}", response, re.DOTALL)
    if json_match is not None:
        return json_match.group(0)
    return None
