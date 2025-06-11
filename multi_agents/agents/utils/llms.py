from __future__ import annotations

from typing import TYPE_CHECKING, Any

import json5 as json
import json_repair
from langchain_community.adapters.openai import convert_openai_messages
from langchain_core.messages.base import BaseMessage
from loguru import logger

from gpt_researcher.config.config import Config
from gpt_researcher.utils.llm import create_chat_completion

if TYPE_CHECKING:
    from gpt_researcher.skills.llm_visualizer import LLMInteractionVisualizer


async def call_model(
    prompt: list,
    model: str,
    response_format: str | None = None,
    cfg: Config | None = None,
) -> Any | None:
    """Call LLM model with visualization support for report generation"""
    # Import visualization here to avoid circular imports
    from gpt_researcher.skills.llm_visualizer import get_llm_visualizer

    _optional_params: dict[str, Any] = {}
    if str(response_format or "").casefold().strip() == "json":
        _optional_params = {"response_format": {"type": "json_object"}}

    cfg = Config() if cfg is None else cfg
    lc_messages: list[BaseMessage] = convert_openai_messages(prompt)

    # Check if visualization is active for report generation
    visualizer: LLMInteractionVisualizer = get_llm_visualizer()
    is_visualizing: bool = visualizer.is_enabled() and visualizer.is_active()

    # Prepare visualization data if active
    interaction_data: dict[str, Any] | None = None
    if is_visualizing:
        # Extract message content for visualization
        system_message: str = ""
        user_message: str = ""

        for msg_dict in prompt:
            role: str = msg_dict.get("role", "").lower()
            content: str = str(msg_dict.get("content", ""))
            if role == "system":
                system_message += content + "\n"
            elif role in ["user", "human"]:
                user_message += content + "\n"

        system_message = system_message.strip()
        user_message = user_message.strip()

        # Prepare interaction data for logging
        interaction_data = {
            "step_name": "Multi-Agent LLM Call",  # Generic for multi-agent
            "model": model,
            "provider": cfg.smart_llm_provider,
            "prompt_type": f"multi_agent_{response_format or 'text'}",
            "system_message": system_message,
            "user_message": user_message,
            "full_messages": prompt.copy(),
            "temperature": 0,  # Multi-agent calls typically use temperature 0
            "max_tokens": None,
        }

    try:
        response: str = await create_chat_completion(
            model=model,
            messages=lc_messages,
            temperature=0,
            llm_provider=cfg.smart_llm_provider,
            llm_kwargs=cfg.llm_kwargs,
            cfg=cfg,
            # cost_callback=cost_callback,
        )

        # Process response based on format
        result: str | None = None
        if response_format == "json":
            try:
                cleaned_json_string: str = response.strip("```json\n")
                result = json.loads(cleaned_json_string)
            except Exception as e:
                print(f"⚠️ Error in reading JSON, attempting to repair JSON : {e.__class__.__name__}: {e}")
                logger.error(f"Error in reading JSON : {e.__class__.__name__}: {e}, attempting to repair reponse: {response}")
                result = json_repair.loads(response)
        else:
            result = response

        # Log successful interaction to visualizer
        if is_visualizing and interaction_data:
            interaction_data["response"] = response
            interaction_data["success"] = True
            interaction_data["retry_attempt"] = 0

            visualizer.log_interaction(**interaction_data)

        return result

    except Exception as e:
        print("⚠️ Error in calling model")
        logger.error(f"Error in calling model: {e.__class__.__name__}: {e}")

        # Log failed interaction to visualizer
        if is_visualizing and interaction_data:
            interaction_data["response"] = ""
            interaction_data["success"] = False
            interaction_data["error"] = f"{e.__class__.__name__}: {str(e)}"
            interaction_data["retry_attempt"] = 0

            visualizer.log_interaction(**interaction_data)

        return None
